#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""옛 글 주소(board/news-82.html)에 새 주소(board/news/82.html)로 보내는 이동 쪽을 찍는다.

왜 필요한가 — 2026.08 에 organize_posts.py 가 글을 종류별 폴더로 옮긴 뒤, 옛 주소는
404.html 의 스크립트가 새 주소로 보내 왔다. 사람 눈에는 문제가 없지만 검색엔진은
스크립트를 기다리지 않는다. GitHub Pages 가 옛 주소에 HTTP 404 를 돌려주므로
서치콘솔이 "찾을 수 없음(404)" 으로 계속 집어내고, 옛 주소로 쌓인 검색 순위도
새 주소로 넘어가지 않는다.

GitHub Pages 에는 서버 쪽 리다이렉트(301)가 없다. 대신 옛 주소에 실제 파일을 두고
<meta http-equiv="refresh" content="0; url=새주소"> 와 <link rel="canonical"> 을
넣으면 200 으로 열리고, 구글은 지연 0 의 meta refresh 를 영구 이동으로 친다.

- 지금 있는 글마다 하나씩 찍는다. 글이 지워졌으면 옛 주소도 404 가 맞다.
- 이동 쪽은 tidy_pages.py(사이트맵)·organize_posts.py 가 LEGACY 표식으로 건너뛴다.
- 글을 더했으면 다시 돌린다. 이미 같은 내용이면 파일을 건드리지 않는다.

    python tools/build_redirects.py
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://hai.seoultech.ac.kr"

KINDS = [("board", "news"), ("board", "gallery"), ("board", "vlog"),
         ("research", "project"), ("research", "video")]

# 옛 주소 꼴. tidy_pages.py 와 organize_posts.py 도 같은 식으로 알아본다.
LEGACY = re.compile(r"^(board|research)/(news|gallery|vlog|project|video)-(\d+)\.html$")

# 이동 쪽임을 나타내는 표식 — 손으로 만든 글과 헷갈리지 않게 파일 안에도 남긴다.
MARK = "<!-- redirect-stub: tools/build_redirects.py 가 만든다. 손으로 고치지 않는다 -->"

TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
%(mark)s
<meta http-equiv="refresh" content="0; url=%(abs_url)s">
<link rel="canonical" href="%(abs_url)s">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<script>location.replace("%(rel_url)s" + location.search + location.hash);</script>
</head>
<body>
<p>이 글은 <a href="%(rel_url)s">%(abs_url)s</a> 로 옮겨졌습니다.</p>
</body>
</html>
"""

TITLE = re.compile(r"<title>(.*?)</title>", re.S)


def title_of(path):
    s = io.open(path, encoding="utf-8").read()
    m = TITLE.search(s)
    return m.group(1).strip() if m else "SeoulTech HAI Lab"


def main():
    made = same = 0
    for d, kind in KINDS:
        folder = os.path.join(ROOT, d, kind)
        if not os.path.isdir(folder):
            continue
        for f in sorted(os.listdir(folder)):
            m = re.match(r"^(\d+)\.html$", f)
            if not m:
                continue
            n = m.group(1)
            rel_new = "%s/%s/%s.html" % (d, kind, n)
            rel_old = "%s/%s-%s.html" % (d, kind, n)
            html = TEMPLATE % {
                "mark": MARK,
                "abs_url": SITE + "/" + rel_new,
                "rel_url": "%s/%s.html" % (kind, n),   # 옛 파일과 같은 폴더 기준
                "title": title_of(os.path.join(folder, f)),
            }
            dst = os.path.join(ROOT, rel_old)
            if os.path.exists(dst):
                if io.open(dst, encoding="utf-8").read() == html:
                    same += 1
                    continue
            io.open(dst, "w", encoding="utf-8", newline="\n").write(html)
            made += 1
    print("이동 쪽 %d개 씀, %d개 그대로" % (made, same))


if __name__ == "__main__":
    main()
