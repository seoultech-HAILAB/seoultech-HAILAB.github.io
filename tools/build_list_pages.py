#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""목록의 2쪽부터를 제 주소로 만든다.

    python tools/build_list_pages.py

쪽 나누기가 자바스크립트로만 돌 때는 몇 쪽을 보고 있든 주소가 늘 같아서,
2쪽의 글을 공유하거나 새로고침하면 1쪽으로 돌아갔다. 쪽마다 실제 파일을 둔다:

    publications/index.html   1쪽 (지금 그대로)
    publications/2/index.html 2쪽
    ...

사본에는 목록 전체가 그대로 들어 있고, 몇 쪽을 보여줄지는 assets/js/main.js 가
주소를 보고 가른다 — 덕분에 연도·구분 필터(?year=2024)가 어느 쪽 주소에서도
목록 전체를 상대로 돈다. 쪽 번호(nav.pager)는 진짜 링크로도 미리 박아 둔다.

글 수가 바뀌면 다시 돌린다. 쪽 폴더(숫자 이름)는 지우고 새로 만들므로
글이 줄어 쪽이 사라져도 옛 폴더가 남지 않는다. 돌린 뒤에는 늘 그렇듯
tidy_pages.py 가 og·canonical·사이트맵을 마저 맞춘다.
"""
import io
import math
import os
import re
import shutil
import posixpath
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relocate import rewrite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://hai.seoultech.ac.kr"   # tidy_pages.py 와 같은 값

# (목록 페이지, 쪽 폴더가 놓일 곳). 1쪽은 목록 페이지 그 자체다.
LISTS = [
    ("publications/index.html", "publications"),
    ("board/index.html",        "board"),           # News
    ("board/gallery.html",      "board/gallery"),
    ("research/index.html",     "research"),        # Projects
    ("about/patents.html",      "about/patents"),
    ("members/alumni.html",     "members/alumni"),  # 지금은 1쪽 — 늘면 여기도 쪽이 생긴다
]

CONTAINER = re.compile(r'<(ol|ul|div)\b[^>]*\bdata-filter\b[^>]*>')
TAG = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*?>')
VOID = {"img", "br", "hr", "input", "meta", "link", "source", "wbr", "area", "col", "embed", "track"}


def container_span(s):
    """data-filter 목록의 여는 태그 위치와 닫는 태그 끝 위치."""
    m = CONTAINER.search(s)
    if not m:
        return None
    depth = 0
    for t in TAG.finditer(s, m.start()):
        if t.group(2).lower() in VOID:
            continue
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return m, t.end()
    return None


def per_of(open_tag):
    """한 쪽에 몇 개 — assets/js/main.js 의 PER 계산과 같아야 한다."""
    cls = re.search(r'class="([^"]*)"', open_tag)
    cls = cls.group(1).split() if cls else []
    return 9 if ({"gallery", "vids", "acards"} & set(cls)) else 10


def pager_html(cur, last, doc_dir, src_rel, pages_dir):
    """진짜 링크로 된 쪽 번호. main.js 가 이 data-* 를 읽어 그대로 다시 그린다."""
    def rel(target):
        return posixpath.relpath(target, doc_dir) if doc_dir else target

    first = rel(src_rel)
    tpl = rel(pages_dir + "/{n}/index.html")
    link = lambda n: first if n == 1 else tpl.replace("{n}", str(n))

    h = ['<nav class="pager" aria-label="쪽 이동" data-page="%d" data-first="%s" data-tpl="%s">'
         % (cur, first, tpl)]
    h.append('<span class="pg pg_nav is-off" aria-hidden="true">‹</span>' if cur == 1 else
             '<a class="pg pg_nav" href="%s" aria-label="이전 쪽">‹</a>' % link(cur - 1))
    for i in range(1, last + 1):
        h.append('<span class="pg is-on" aria-current="page">%d</span>' % i if i == cur else
                 '<a class="pg" href="%s">%d</a>' % (link(i), i))
    h.append('<span class="pg pg_nav is-off" aria-hidden="true">›</span>' if cur == last else
             '<a class="pg pg_nav" href="%s" aria-label="다음 쪽">›</a>' % link(cur + 1))
    h.append('</nav>')
    return "".join(h)


def set_page_meta(s, rel, n):
    """사본에 제 주소와 '· n쪽' 표식을 준다 (tidy 가 og 는 다시 맞춘다)."""
    s = re.sub(r"<title>([^<|]*?)\s*\|", "<title>\\1 · %d쪽 |" % n, s, count=1)
    url = SITE + "/" + rel
    s = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, s)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url, s)
    return s


def main():
    for src_rel, pages_dir in LISTS:
        full = os.path.join(ROOT, src_rel)
        s = io.open(full, encoding="utf-8").read()
        # 이전 실행이 박아 둔 쪽 번호와 쪽 폴더를 걷어내고 시작한다
        s = re.sub(r'\n?<nav class="pager".*?</nav>', "", s, flags=re.S)
        pd = os.path.join(ROOT, pages_dir)
        if os.path.isdir(pd):
            for d in os.listdir(pd):
                if d.isdigit() and os.path.isdir(os.path.join(pd, d)):
                    shutil.rmtree(os.path.join(pd, d))

        span = container_span(s)
        if not span:
            print("%-26s data-filter 목록이 없다 — 건너뜀" % src_rel)
            continue
        m, end = span
        items = s.count('data-year="', m.start(), end)
        per = per_of(m.group(0))
        last = max(1, math.ceil(items / per))
        doc_dir = posixpath.dirname(src_rel)

        if last > 1:
            base = s[:end] + "\n" + pager_html(1, last, doc_dir, src_rel, pages_dir) + s[end:]
        else:
            base = s
        if base != io.open(full, encoding="utf-8").read():
            io.open(full, "w", encoding="utf-8", newline="\n").write(base)

        for n in range(2, last + 1):
            rel = "%s/%d/index.html" % (pages_dir, n)
            copy = rewrite(s, src_rel, rel)
            span2 = container_span(copy)
            copy = copy[:span2[1]] + "\n" + pager_html(
                n, last, posixpath.dirname(rel), src_rel, pages_dir) + copy[span2[1]:]
            copy = set_page_meta(copy, rel, n)
            os.makedirs(os.path.join(ROOT, pages_dir, str(n)), exist_ok=True)
            io.open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="\n").write(copy)

        print("%-26s %3d개 / %d쪽 (한 쪽 %d개)" % (src_rel, items, last, per))


if __name__ == "__main__":
    main()
