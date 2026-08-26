#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""원본 게시판(스마트에디터) HTML 을 이 사이트에 맞게 정리한다.

본문에 style 속성이 2,500개 넘게 박혀 있고 span/font 로만 감싼 껍데기가 대부분이라,
그대로 넣으면 이 사이트의 글자 크기·색과 싸운다. 구조만 남기고 전부 벗긴다.

  - style/class/id 제거
  - span·font 는 벗겨서 내용만 남김. 단 원문이 색으로 강조한 부분은 <strong> 으로 옮긴다
    (원저자가 의도한 강조라 버리면 뜻이 죽는다)
  - 빈 <p> 와 연속 <br> 정리
  - 이미지 경로를 내려받은 로컬 파일로 교체
"""
import html as _html
import os
import re

from lxml import etree, html as LH

KEEP = {"p", "br", "b", "strong", "u", "em", "i", "a", "img", "blockquote", "ul", "ol", "li", "h4", "h5"}
UNWRAP = {"span", "font", "div", "o:p", "v:shapetype", "v:shape", "v:imagedata"}
EMPH_COLORS = re.compile(r"color:\s*rgb\(\s*0\s*,\s*11[0-9]\s*,\s*2[0-4][0-9]|color:\s*#0075c8", re.I)


def _is_emph(el):
    s = el.get("style") or ""
    return bool(EMPH_COLORS.search(s))


def clean(fragment, img_map, base_depth=1):
    """fragment: 원본 innerHTML. img_map: 원본 src -> 로컬 파일명."""
    if not fragment or not fragment.strip():
        return ""
    try:
        root = LH.fragment_fromstring(fragment, create_parent="div")
    except Exception:
        return ""

    # 색 강조를 <strong> 으로 승격시켜 둔다 (span 을 벗기기 전에)
    for el in root.iter():
        if isinstance(el.tag, str) and el.tag.lower() in ("span", "font") and _is_emph(el):
            el.tag = "strong"

    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el is root:
            continue  # 루트는 감싸려고 만든 것이라 건드리지 않는다
        tag = el.tag.lower().replace("{urn:schemas-microsoft-com:office:office}", "o:")
        if tag == "img":
            src = el.get("src") or ""
            local = img_map.get(src)
            if local:
                el.attrib.clear()
                el.set("src", "../assets/img/posts/" + local)
                el.set("alt", "")
                el.set("loading", "lazy")
            else:
                el.getparent().remove(el)
            continue
        if tag == "a":
            href = el.get("href") or ""
            el.attrib.clear()
            if href and not href.startswith("javascript"):
                el.set("href", href)
                if href.startswith("http"):
                    el.set("target", "_blank")
                    el.set("rel", "noopener")
            else:
                el.tag = "span"
            continue
        for k in list(el.attrib):
            del el.attrib[k]
        if tag in UNWRAP or tag not in KEEP:
            el.drop_tag()

    out = etree.tostring(root, encoding="unicode", method="html")
    out = re.sub(r"^<div>|</div>$", "", out.strip())
    out = out.replace("&#13;", "").replace("\r", "")
    out = re.sub(r"<p>\s*(?:<br\s*/?>|&nbsp;|\s)*</p>", "", out)     # 빈 문단
    out = re.sub(r"(?:<br\s*/?>\s*){3,}", "<br><br>", out)           # 줄바꿈 폭주
    out = re.sub(r"<b>\s*<strong>", "<strong>", out)      # 색 강조를 승격하며 생긴 이중 감싸기
    out = re.sub(r"</strong>\s*</b>", "</strong>", out)
    out = re.sub(r"<strong>\s*<b>", "<strong>", out)
    out = re.sub(r"</b>\s*</strong>", "</strong>", out)
    out = re.sub(r"\s{2,}", " ", out)
    return group_images(out)


IMG_RE = re.compile(r"<img[^>]*>")


def group_images(html_str):
    """이미지가 <p> 안에 <br> 로 줄줄이 이어 붙어 있다. 원본 에디터가 그렇게 저장한다.
    그대로 두면 세로로 8장이 쏟아지므로, 문단에서 떼어내 격자로 묶는다."""
    def fix(m):
        block = m.group(0)
        imgs = IMG_RE.findall(block)
        if not imgs:
            return block
        # 이미지를 뺀 나머지에 글자가 남아 있으면 문단을 건드리지 않는다
        rest = IMG_RE.sub("", block)
        rest = re.sub(r"<[^>]+>|&nbsp;|\s", "", rest)
        if rest:
            return block
        cls = "post_gal" + (" is-one" if len(imgs) == 1 else "")
        return f'<div class="{cls}">' + "".join(imgs) + "</div>"

    return re.sub(r"<p>.*?</p>", fix, html_str, flags=re.S)


# 원본에 남아 있는 영문 오탈자. 사람 이름과 학회명이라 그대로 두면 검색에도 안 걸린다.
TYPOS = [
    (r"\brecieved\b", "received"),
    (r"\bDoctorol Consorcium\b", "Doctoral Consortium"),
    (r"\bDoctorol\b", "Doctoral"),
    (r"\bConsorcium\b", "Consortium"),
    (r"\bEdeg-Guided\b", "Edge-Guided"),
    (r"\bSeoung Eon Cha\b", "Seung Eon Cha"),
    (r"\bYuwon kim\b", "Yuwon Kim"),
    (r"\bMinyoung Park Publishes\b", "Minyoung Park Publishes"),
    (r"\bpresent below research\b", "presented the research below"),
    (r"\bpresented below research\b", "presented the research below"),
    (r"\bhad presented their papers accepted at\b", "presented their accepted papers at"),
    (r"\bis excited to welcome a new researcher to our team\.\s*-\s*(?=[A-Z][a-z]+ [A-Z])",
     "is excited to welcome new researchers to our team. - "),
]


def fix_typos(text):
    for pat, rep in TYPOS:
        text = re.sub(pat, rep, text)
    return text
