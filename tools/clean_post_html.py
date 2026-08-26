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
    # 워드에서 붙여넣은 흔적. <v:imagedata> 가 로컬 파일(file:///...)을 가리켜
    # 원본 사이트에서도 깨져 있다. lxml 이 네임스페이스 태그로 읽어 태그 필터를
    # 그냥 지나가므로, 파싱 전에 통째로 걷어낸다.
    fragment = re.sub(r"<!--\[if[^>]*>.*?<!\[endif\]-->", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[/]?[ov]:[^>]*>", "", fragment, flags=re.I)
    fragment = re.sub(r"<img[^>]*src=[\"']file:///[^>]*>", "", fragment, flags=re.I)
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
    """사진을 전부 같은 방식으로 늘어놓는다.

    원본 에디터는 사진을 문단 안에 <br> 로 이어 붙이기도 하고 글과 섞어 두기도 해서,
    그대로 두면 어떤 글은 사진이 두 줄로, 어떤 글은 세로로 쭉 쌓인다.
    문단에서 사진만 모두 뽑아 문단 바로 뒤에 하나의 격자로 놓는다.
    이러면 글이 어떻게 저장돼 있든 화면에서는 같은 모양이 된다."""
    def fix(m):
        block = m.group(0)
        imgs = IMG_RE.findall(block)
        if not imgs:
            return block
        rest = IMG_RE.sub("", block)
        text = re.sub(r"<[^>]+>|&nbsp;|\s", "", rest)
        gal = '<div class="post_gal">' + "".join(imgs) + "</div>"
        if not text:
            return gal              # 사진뿐인 문단 -> 격자로 대체
        return rest + gal           # 글이 섞여 있으면 글을 남기고 격자를 뒤에

    out = re.sub(r"<p>.*?</p>", fix, html_str, flags=re.S)

    # 문단 밖에 홀로 놓인 사진도 있다 (에디터가 <p> 없이 저장한 경우).
    # 잇달아 나오는 것끼리 묶어 같은 격자로 만든다.
    def loose(m):
        imgs = IMG_RE.findall(m.group(0))
        return '<div class="post_gal">' + "".join(imgs) + "</div>" if imgs else m.group(0)
    out = re.sub(r"(?:<img[^>]*>\s*(?:<br\s*/?>\s*)*)+", loose, out)

    # 격자가 잇달아 나오면 하나로 합친다 (문단이 나뉘어 있었을 뿐이다)
    out = re.sub(r'</div>\s*<div class="post_gal">', "", out)
    out = re.sub(r'<div class="post_gal"></div>', "", out)
    return tidy_flow(out)


# 문단으로 다뤄야 하는 것들 — 이 사이에 놓인 <br> 은 하는 일이 없다
BLOCK = r'(?:<p>.*?</p>|<div class="post_(?:gal|video)">.*?</div>|<ul>.*?</ul>|'\
        r'<ol>.*?</ol>|<blockquote>.*?</blockquote>|<h4>.*?</h4>|<h5>.*?</h5>)'


def tidy_flow(html_str):
    """문단 사이 간격을 한 가지로 맞춘다.

    원본 에디터는 줄을 띄우려고 <br> 을 넣었다가, 어떤 글은 <p> 로 나누고 어떤 글은
    <br><br> 로만 나눠 놓았다. 그대로 두면 같은 페이지 안에서도 문단 간격이 두 배씩
    널뛰고, <p> 밖에 맨몸으로 놓인 글줄은 아예 간격을 못 받는다.
    문단은 <p> 하나로만 나누고, 그 사이의 <br> 은 걷어낸다."""
    s = re.sub(r"<!--.*?-->", "", html_str, flags=re.S)   # 에디터가 남긴 안내 주석

    # 원본 에디터는 글자를 키우려고 <h4>/<h5> 를 쓰기도 했다. 그 안에 사진 격자가
    # 들어가면 격자가 '글줄 폭'(제목에 걸린 max-width)을 물려받아, 같은 두 장짜리
    # 글인데도 어떤 글은 사진이 좁게 나왔다. 제목 노릇을 못 하는 껍데기라 벗긴다.
    s = re.sub(r'<(h4|h5)>(\s*(?:<div class="post_(?:gal|video)">.*?</div>\s*)+)</\1>',
               r"\2", s, flags=re.S)

    # 1) <p> 안쪽 정리: 앞뒤 공백·<br> 제거, <br><br> 는 문단 나눔으로 승격
    def fix_p(m):
        inner = m.group(1)
        inner = re.sub(r"^(?:\s|<br\s*/?>|&nbsp;)+", "", inner)
        inner = re.sub(r"(?:\s|<br\s*/?>|&nbsp;)+$", "", inner)
        if not inner.strip():
            return ""
        parts = re.split(r"(?:<br\s*/?>\s*){2,}", inner)
        return "".join("<p>%s</p>" % p.strip() for p in parts if p.strip())
    s = re.sub(r"<p>(.*?)</p>", fix_p, s, flags=re.S)

    # 2) 문단 밖에 맨몸으로 놓인 글줄을 <p> 로 감싼다
    out, pos = [], 0
    for m in re.finditer(BLOCK, s, flags=re.S):
        out.append(_wrap_loose(s[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_wrap_loose(s[pos:]))
    s = "".join(out)

    # 3) 문단과 문단 사이에 남은 <br> 은 간격만 두 겹으로 만들 뿐이다
    s = re.sub(r"(</(?:p|div|ul|ol|blockquote|h4|h5)>)\s*(?:<br\s*/?>\s*)+", r"\1", s)
    s = re.sub(r"(?:<br\s*/?>\s*)+(<(?:p|div|ul|ol|blockquote|h4|h5)[ >])", r"\1", s)
    s = re.sub(r"^(?:\s|<br\s*/?>)+", "", s)
    s = re.sub(r"(?:\s|<br\s*/?>)+$", "", s)
    return s


def _wrap_loose(chunk):
    """블록 사이에 놓인 맨몸 글줄 -> <p>. 빈 <br> 뭉치는 버린다."""
    if not chunk or not re.sub(r"<[^>]+>|&nbsp;|\s", "", chunk):
        return ""
    parts = re.split(r"(?:<br\s*/?>\s*){2,}", chunk)
    return "".join("<p>%s</p>" % p.strip() for p in parts
                   if re.sub(r"<[^>]+>|&nbsp;|\s", "", p))


# 원본에 남아 있는 영문 오탈자. 사람 이름과 학회명이라 그대로 두면 검색에도 안 걸린다.
TYPOS = [
    (r"\brecieved\b", "received"),
    (r"\bDoctorol Consorcium\b", "Doctoral Consortium"),
    (r"\bDoctorol\b", "Doctoral"),
    (r"\bConsorcium\b", "Consortium"),
    (r"\bEdeg-Guided\b", "Edge-Guided"),
    (r"\bSeoung Eon Cha\b", "Seung Eon Cha"),
    (r"\bYuwon kim\b", "Yuwon Kim"),
    (r"\bpresent below research\b", "presented the research below"),
    (r"\bpresented below research\b", "presented the research below"),
    (r"\bhad presented their papers accepted at\b", "presented their accepted papers at"),
    (r"\bpositions for for\b", "positions for"),
]


def fix_typos(text):
    for pat, rep in TYPOS:
        text = re.sub(pat, rep, text)
    return text
