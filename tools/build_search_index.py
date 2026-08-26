#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/search-index.json 을 만든다.

    python tools/build_search_index.py

GitHub Pages 는 정적이라 검색 서버가 없다. 페이지에서 제목·항목만 뽑아
브라우저가 훑을 수 있는 평평한 목록으로 저장한다. 홈은 다른 페이지의
내용을 그대로 다시 보여주는 자리라 색인에서 뺀다 (넣으면 결과가 홈 중복으로 덮인다).

글마다 상세 페이지가 생겼으므로, 목록에서 뽑은 항목은 목록이 아니라 그 글로 곧장
연결한다. 상세 페이지의 본문도 앞부분을 함께 담아 제목에 없는 말로도 찾을 수 있게 한다.
"""
import collections
import glob
import html
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = {
    "about/index.html": ("Research Area", "About"),
    "about/facility.html": ("Facility", "About"),
    "about/patents.html": ("Patent", "About"),
    "members/index.html": ("Professor", "Members"),
    "members/researcher.html": ("Researcher", "Members"),
    "members/alumni.html": ("Alumni", "Members"),
    "members/history.html": ("History", "Members"),
    "research/index.html": ("Projects", "Research"),
    "research/videos.html": ("Video", "Research"),
    "publications/index.html": ("Publications", "Publications"),
    "board/index.html": ("News", "Board"),
    "board/gallery.html": ("Gallery", "Board"),
    "board/vlog.html": ("V-log", "Board"),
}

# 상세 페이지 묶음 — (파일 패턴, 페이지 이름, 대메뉴)
POSTS = [
    ("board/news-*.html", "News", "Board"),
    ("board/gallery-*.html", "Gallery", "Board"),
    ("board/vlog-*.html", "V-log", "Board"),
    ("research/project-*.html", "Projects", "Research"),
    ("research/video-*.html", "Video", "Research"),
]

FIELDS = re.compile(
    r'<h[34][^>]*>(.*?)</h[34]>'
    r'|<span class="gal_tit">(.*?)</span>'
    r'|<span class="subject">(.*?)</span>'
    r'|<span class="vtit">(.*?)</span>'          # 영상 목록 (옛 mvp_tit)
    r'|<figcaption>(.*?)</figcaption>'           # 갤러리 목록
    r'|<li class="lrow"[^>]*>(.*?)</li>', re.S)

# 항목 안에 상세 글 링크가 있으면 목록 대신 그리로 보낸다
DETAIL = re.compile(r'href="((?:\.\./)?[a-z]*/?(?:news|gallery|vlog|project|video)-\d+\.html)"')

MAX_BODY_CHUNKS = 3        # 글 하나에서 본문은 앞 세 문단까지만

# 과제 글의 머리말 — '공동연구책임자 / 2026.07.01 ~ ...', '기간: ...', 'Funding: ...',
# 'English Summary:' 처럼 검색어가 될 일이 없는 줄이다. 이것들이 위 세 자리를 먼저
# 차지해 버려서, 정작 과제 설명이 색인에 들어가지 못했다.
SKIP_BODY = re.compile(
    r'^(기간|Funding|English Summary|Period)\s*[::]'
    r'|^\S.{0,40}\s/\s\d{4}\.\d{2}\.\d{2}\s*~')

# 사람 카드는 조각내지 않고 한 줄로 담는다.
#   "Sabin Lee — Netmarble AI Engineer (2026년 졸업)"
# 이름과 소속을 따로 담으면 둘이 같은 사람인지 알 수 없어, '졸업생들 어디 갔나요'
# 같은 질문에 이름만 늘어놓게 된다.
CARD = re.compile(r'<article class="(acard|mcard)"([^>]*)>(.*?)</article>', re.S)


def person_lines(body):
    for m in CARD.finditer(body):
        kind, attrs, c = m.group(1), m.group(2), m.group(3)
        def pick(pat):
            g = re.search(pat, c, re.S)
            return clean(g.group(1)) if g else ""
        name = pick(r"<h4>(.*?)</h4>")
        if not name:
            continue
        if kind == "acard":
            year, now = pick(r'<p class="ayear">(.*?)</p>'), pick(r'<p class="anow">(.*?)</p>')
            diss = pick(r'<p class="diss">(.*?)</p>')
            # 졸업생 카드에만 data-year 가 붙는다. 없으면 방문 교수다.
            grad = "data-year" in attrs
            bits = [name, "— 석사 졸업생" if grad else "— 방문 교수 (졸업생 아님)"]
            if now:
                bits.append(", " + now)
            if year and grad:
                bits.append("(%s년 졸업)" % year)
            yield " ".join(bits).replace(" ,", ",")
            if diss:
                yield "%s %s" % (name, diss)
        else:
            role, mint = pick(r'<p class="mrole">(.*?)</p>'), pick(r'<p class="mint">(.*?)</p>')
            bits = [name]
            if role:
                bits.append("— " + role)
            if mint:
                bits.append("· " + mint)
            yield " ".join(bits)

# 논문도 카드처럼 한 줄로 담는다. 제목만 담으면 저자 이름으로는 검색이 안 되고,
# 챗봇도 어떤 논문이 중요한지(수상·저널 등급) 알 길이 없다.
PUB = re.compile(r'<li class="pub" data-year="(\d+)"[^>]*>(.*?)</li>', re.S)


def pub_lines(body):
    for m in PUB.finditer(body):
        year, c = m.group(1), m.group(2)
        def pick(pat):
            g = re.search(pat, c, re.S)
            return clean(g.group(1)) if g else ""
        title = pick(r"<h4>(.*?)</h4>")
        if not title:
            continue
        authors = pick(r'<p class="authors">(.*?)</p>')
        venue = pick(r'<p class="venue">(.*?)</p>')
        bdgs = " ".join(clean(b) for b in re.findall(r'<span class="bdg[^"]*">(.*?)</span>', c))
        line = "(%s) %s — %s / %s" % (year, title, authors, venue)
        if bdgs:
            line += " ★" + bdgs
        yield title, line[:240]


def load_aliases():
    """영문 이름에 한글 표기를 붙여 준다. '박보겸' 으로 쳐도 'Bogyeom Park' 이 걸리게 하는 표.
    부분 일치라 '보겸' 만 쳐도 찾는다. tools/name_aliases.json 에서 관리한다."""
    p = os.path.join(ROOT, "tools", "name_aliases.json")
    if not os.path.exists(p):
        return {}
    raw = json.loads(io.open(p, encoding="utf-8").read())
    return {k: v for k, v in raw.items() if not k.startswith("_") and v}


def clean(t):
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def rec_for(text, path, section, page_title, aliases):
    r = {"t": text, "p": path, "s": section, "pt": page_title}
    extra = [a for name, al in aliases.items() if name in text for a in al]
    if extra:
        r["a"] = " ".join(extra)
    return r


def main():
    aliases = load_aliases()
    recs, seen_global = [], set()

    # 1) 고정 페이지 — 목록 항목은 상세 글로 연결
    for path, (title, section) in PAGES.items():
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            print("  건너뜀 (없음):", path)
            continue
        src = io.open(full, encoding="utf-8").read()
        m = re.search(r'<div class="sub_body">(.*?)</div>\s*</div>', src, re.S)
        body = m.group(1) if m else src
        folder = path.rsplit("/", 1)[0]
        bare = set()
        if path.startswith("publications/"):
            for title, line in pub_lines(body):
                bare.add(title)          # 제목만 있는 조각은 아래에서 걸러진다
                if (line, path) not in seen_global:
                    seen_global.add((line, path))
                    recs.append(rec_for(line, path, section, "Publications", aliases))
        for line in person_lines(body):
            # 이름만 남은 조각을 걸러내려면 이름 부분만 떼야 한다.
            # 줄 모양은 '이름 — 역할 · 관심분야' 인데 역할이나 관심분야가 없을 수도 있다.
            bare.add(re.split(r' [—·] | Dissertation ', line)[0].strip())
            if 4 <= len(line) <= 240 and (line, path) not in seen_global:
                seen_global.add((line, path))
                recs.append(rec_for(line, path, section, title, aliases))

        for f in FIELDS.finditer(body):
            raw = next(g for g in f.groups() if g is not None)
            t = clean(raw)
            if len(t) < 4 or len(t) > 240:
                continue
            if t in bare:
                continue      # 위에서 소속까지 붙여 이미 담은 사람이다
            d = DETAIL.search(raw)
            target = "%s/%s" % (folder, d.group(1).split("/")[-1]) if d else path
            key = (t, target)
            if key in seen_global:
                continue
            seen_global.add(key)
            recs.append(rec_for(t, target, section, title, aliases))

    # 2) 상세 글 — 제목과 본문 앞부분
    for pattern, title, section in POSTS:
        for full in sorted(glob.glob(os.path.join(ROOT, pattern))):
            path = os.path.relpath(full, ROOT).replace("\\", "/")
            src = io.open(full, encoding="utf-8").read()
            h = re.search(r'<h3 class="post_tit">(.*?)</h3>', src, re.S)
            if h:
                t = clean(h.group(1))
                if 4 <= len(t) <= 240 and (t, path) not in seen_global:
                    seen_global.add((t, path))
                    recs.append(rec_for(t, path, section, title, aliases))
            b = re.search(r'<div class="post_body">(.*?)\n\s*</div>', src, re.S)
            if not b:
                continue
            n = 0
            for p in re.findall(r'<p>(.*?)</p>', b.group(1), re.S):
                t = clean(p)
                if len(t) < 20 or SKIP_BODY.search(t):
                    continue
                t = t[:240]
                if (t, path) in seen_global:
                    continue
                seen_global.add((t, path))
                recs.append(rec_for(t, path, section, title, aliases))
                n += 1
                if n >= MAX_BODY_CHUNKS:
                    break

    out = os.path.join(ROOT, "assets", "search-index.json")
    io.open(out, "w", encoding="utf-8", newline="\n").write(
        json.dumps(recs, ensure_ascii=False, separators=(",", ":")))
    print("색인 %d건 -> assets/search-index.json (%d KB)"
          % (len(recs), os.path.getsize(out) // 1024))
    for s, n in collections.Counter(r["s"] for r in recs).most_common():
        print("  %4d  %s" % (n, s))
    tagged = sum(1 for r in recs if "a" in r)
    print("  별칭 붙은 항목 %d건 (이름 %d개 등록)" % (tagged, len(aliases)))
    lists = sum(1 for r in recs if not re.search(r"-\d+\.html$", r["p"]))
    print("  상세 글로 연결 %d건 / 목록으로 연결 %d건" % (len(recs) - lists, lists))


if __name__ == "__main__":
    main()
