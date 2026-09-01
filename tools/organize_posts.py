#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""글 파일을 종류별 폴더로 옮긴다.

    python tools/organize_posts.py

board/ 와 research/ 에 news-82.html 같은 글 200장이 목록 페이지와 한데 섞여
쌓여 있었다. 종류별 폴더로 옮긴다:

    board/news-82.html        -> board/news/82.html
    board/gallery-220.html    -> board/gallery/220.html
    board/vlog-79.html        -> board/vlog/79.html
    research/project-166.html -> research/project/166.html
    research/video-68.html    -> research/video/68.html

옮기면서 같이 고치는 것:
  1. 옮긴 글 자신의 상대 주소 — 한 층 깊어졌으니 ../assets 는 ../../assets 로,
     이전/다음 글 링크(news-81.html)는 같은 폴더의 81.html 로
  2. 사이트 전 페이지에서 옮긴 글을 가리키는 링크 (목록·홈 카드·글 사이 링크)
  3. tools/post_index.json 의 href

옛 주소로 오는 방문자(검색엔진·공유된 링크)는 404.html 의 이동 스크립트가
새 주소로 보낸다. 이미 옮겼으면 이 스크립트는 아무 일도 하지 않는다.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relocate import rewrite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KINDS = [("board", "news"), ("board", "gallery"), ("board", "vlog"),
         ("research", "project"), ("research", "video")]

# OneDrive 충돌 사본은 배포되지 않는 곁가지다 — 옮기지도, 링크를 고치지도 않는다
CONFLICT = re.compile(r"-DESKTOP-[^.]*\.html$", re.I)


def html_pages():
    """assets(데모 앱은 자족적이다)와 tools 를 뺀 모든 페이지."""
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ("assets", "tools") and not d.startswith(".")]
        for f in files:
            if f.endswith(".html") and not f.startswith(("google", "naver")) \
               and not CONFLICT.search(f):
                yield os.path.relpath(os.path.join(base, f), ROOT).replace("\\", "/")


def main():
    moved = {}
    for d, kind in KINDS:
        pat = re.compile(r"^%s-(\d+)\.html$" % re.escape(kind))
        for f in sorted(os.listdir(os.path.join(ROOT, d))):
            m = pat.match(f)
            if m and not CONFLICT.search(f):
                moved["%s/%s" % (d, f)] = "%s/%s/%s.html" % (d, kind, m.group(1))
    if not moved:
        print("옮길 글이 없다 — 이미 폴더로 이사했다.")
        return

    pages = list(html_pages())
    touched = 0
    for rel in pages:
        new_rel = moved.get(rel, rel)
        full = os.path.join(ROOT, rel)
        s = io.open(full, encoding="utf-8").read()
        s2 = rewrite(s, rel, new_rel, moved)
        if new_rel != rel:
            dst = os.path.join(ROOT, new_rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            io.open(dst, "w", encoding="utf-8", newline="\n").write(s2)
            os.remove(full)
        elif s2 != s:
            io.open(full, "w", encoding="utf-8", newline="\n").write(s2)
            touched += 1

    p = os.path.join(ROOT, "tools", "post_index.json")
    idx = json.load(io.open(p, encoding="utf-8"))
    for entries in idx.values():
        for e in entries:
            e["href"] = moved.get(e["href"], e["href"])
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        json.dumps(idx, ensure_ascii=False, indent=1))

    print("글 %d장 이사, 링크를 고친 페이지 %d장, post_index.json 갱신"
          % (len(moved), touched))
    print("이어서: python tools/build_list_pages.py && python tools/tidy_pages.py"
          " && python tools/build_search_index.py")


if __name__ == "__main__":
    main()
