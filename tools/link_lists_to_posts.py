#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""목록의 각 줄을 방금 만든 상세 페이지로 이어 준다.

    python tools/link_lists_to_posts.py

News / Projects / Gallery 목록은 눌러도 갈 곳이 없었다. 제목을 기준으로
tools/post_index.json 과 맞춰 링크를 건다. 제목 표기가 미묘하게 달라
(마침표, 앰퍼샌드, 공백) 정확히 안 맞는 경우가 있어 느슨하게 비교한다.
"""
import html, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def key(t):
    t = html.unescape(t or "")
    t = re.sub(r"\[[^\]]*\]", " ", t)          # [Ongoing], [2026.08] 같은 머리표
    t = re.sub(r"[^0-9a-z가-힣]+", "", t.lower())
    return t


def load_index():
    p = os.path.join(ROOT, "tools", "post_index.json")
    return json.load(io.open(p, encoding="utf-8"))


def wire(path, entries, pattern, build):
    full = os.path.join(ROOT, path)
    s = io.open(full, encoding="utf-8").read()
    by = {}
    for e in entries:
        by.setdefault(key(e["title"]), e)
    hit = miss = 0

    def repl(m):
        nonlocal hit, miss
        title = m.group("title")
        e = by.get(key(title))
        if not e:
            miss += 1
            return m.group(0)
        hit += 1
        return build(m, os.path.basename(e["href"]))

    out = pattern.sub(repl, s)
    io.open(full, "w", encoding="utf-8", newline="\n").write(out)
    print(f"{path:24} 연결 {hit:3d}  못찾음 {miss:3d}")
    return miss


def main():
    idx = load_index()
    misses = 0

    # News: <p>제목</p> 을 링크로
    misses += wire(
        "board/index.html", idx["news2"],
        re.compile(r'(?P<pre><li class="lrow"[^>]*><time>[^<]*</time>)<p>(?P<title>[^<]+)</p>'),
        lambda m, h: f'{m.group("pre")}<p><a href="{h}">{m.group("title")}</a></p>')

    # Projects: <h4>제목</h4> 을 링크로
    misses += wire(
        "research/index.html", idx["projects2"],
        re.compile(r'<h4>(?P<title>[^<]+)</h4>'),
        lambda m, h: f'<h4><a href="{h}">{m.group("title")}</a></h4>')

    # Gallery: 설명 글을 링크로 (확대 버튼은 그대로 두고 제목만 상세로)
    misses += wire(
        "board/gallery.html", idx["gallery2"],
        re.compile(r'<figcaption><time>(?P<t>[^<]*)</time>(?P<title>[^<]+)</figcaption>'),
        lambda m, h: f'<figcaption><time>{m.group("t")}</time><a href="{h}">{m.group("title")}</a></figcaption>')

    print("\n못 찾은 항목이 있으면 제목 표기가 원본과 달라진 것이다." if misses else "\n전부 연결됨")


if __name__ == "__main__":
    main()
