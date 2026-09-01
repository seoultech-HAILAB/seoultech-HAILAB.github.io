#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 문서가 다른 깊이로 옮겨질 때 상대 주소를 다시 계산한다.

organize_posts.py(글을 폴더로 이사)와 build_list_pages.py(목록 쪽 사본)가 같이 쓴다.
'../ 를 하나 더 붙인다' 식으로 문자열을 만지면 news-82.html 같은 같은-폴더 링크를
반드시 놓친다. 여기서는 한 가지 방법만 쓴다 — 링크를 루트 기준 경로로 풀었다가,
문서의 새 자리에서 다시 상대 경로로 적는다.
"""
import posixpath
import re

# 주소를 담는 속성만 만진다. og 메타(content=)와 JSON-LD 는 절대 주소라
# tidy_pages.py 가 파일 위치(rel)로부터 다시 만드니 여기서 건드리지 않는다.
ATTR = re.compile(r'\b(href|src|data-full)="([^"]*)"')
SKIP = ("http://", "https://", "//", "#", "mailto:", "data:", "javascript:", "tel:")


def rewrite(s, old_rel, new_rel, moved=None):
    """old_rel 에 있던 문서 s 가 new_rel 로 옮겨간다 치고 상대 주소를 고친다.

    moved: 루트 기준 '옛 경로 -> 새 경로' 표 (같이 옮겨간 다른 파일들).
    문서가 제자리면 old_rel == new_rel 로 부른다 — 그때는 옮겨간 파일을
    가리키는 링크만 바뀌고 나머지는 글자 하나 안 바뀐다 (diff 를 깨끗하게).
    """
    moved = moved or {}
    old_dir = posixpath.dirname(old_rel)
    new_dir = posixpath.dirname(new_rel)

    def f(m):
        attr, val = m.group(1), m.group(2)
        if not val or val.startswith(SKIP):
            return m.group(0)
        # ?v=캐시번호, #조각 은 경로가 아니다 — 떼어 뒀다가 도로 붙인다
        cut = re.search(r"[?#]", val)
        path, tail = (val[:cut.start()], val[cut.start():]) if cut else (val, "")
        if not path:
            return m.group(0)
        tgt = posixpath.normpath(posixpath.join(old_dir, path))
        tgt2 = moved.get(tgt, tgt)
        if tgt2 == tgt and old_dir == new_dir:
            return m.group(0)
        link = posixpath.relpath(tgt2, new_dir) if new_dir else tgt2
        return '%s="%s%s"' % (attr, link, tail)

    return ATTR.sub(f, s)
