#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""갤러리·영상 글의 날짜를 제목에서 날짜 칸으로 옮긴다.

    python tools/fix_gallery_dates.py

갤러리 제목이 '[2026.08] 2026학년도 후기 학위수여식' 처럼 대괄호로 날짜를 달고 있었다.
같은 사이트의 News·Projects 는 제목과 날짜를 따로 두는데 갤러리만 제목 안에 넣은 셈이라,
목록에서는 날짜가 두 번(왼쪽 time + 제목 앞 대괄호) 나오고, 정작 상세 페이지의 날짜 칸은
비어 있었다. 대괄호를 떼어 그 값을 날짜 칸에 넣는다.

영상·V-log 는 애초에 날짜가 없어 목록에서 가져온다 (없으면 비워 둔다).
"""
import glob
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRACKET = re.compile(r"\[(\d{4})\.(\d{2})\]\s*")


def list_dates(list_page, href_prefix):
    """목록 페이지에서 '글 파일 이름 -> 날짜' 를 거둬 온다."""
    p = os.path.join(ROOT, list_page)
    if not os.path.exists(p):
        return {}
    s = io.open(p, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'<time>([^<]*)</time>\s*<a href="(%s-\d+\.html)"' % href_prefix, s):
        out[m.group(2)] = m.group(1).strip()
    for m in re.finditer(r'<a[^>]+href="(%s-\d+\.html)"[^>]*>.*?<time>([^<]*)</time>' % href_prefix,
                         s, re.S):
        out.setdefault(m.group(1), m.group(2).strip())
    return out


def main():
    dates = {}
    dates.update(list_dates("board/gallery.html", "gallery"))
    dates.update(list_dates("board/vlog.html", "vlog"))
    dates.update(list_dates("research/videos.html", "video"))

    # 1) 상세 페이지: 제목에서 대괄호를 떼고 그 값을 날짜 칸에 넣는다
    titles = {}
    for pat in ("board/gallery-*.html", "board/vlog-*.html", "research/video-*.html"):
        for full in sorted(glob.glob(os.path.join(ROOT, pat))):
            name = os.path.basename(full)
            s = io.open(full, encoding="utf-8").read()

            m = re.search(r'<h3 class="post_tit">(.*?)</h3>', s, re.S)
            if not m:
                continue
            raw = m.group(1)
            b = BRACKET.search(raw)
            date = "%s.%s" % (b.group(1), b.group(2)) if b else dates.get(name, "")
            clean = BRACKET.sub("", raw).strip()
            titles[name] = clean

            s = s.replace('<h3 class="post_tit">%s</h3>' % raw,
                          '<h3 class="post_tit">%s</h3>' % clean)
            s = re.sub(r'(<title>)\s*\[\d{4}\.\d{2}\]\s*', r'\1', s)
            if date:
                s = s.replace('<p class="post_meta"><time></time></p>',
                              '<p class="post_meta"><time>%s</time></p>' % date)
            io.open(full, "w", encoding="utf-8", newline="\n").write(s)

    # 2) 어디에 남아 있든 제목 앞 대괄호는 걷어낸다 (이전/다음 글, 홈 카드, 목록의 alt·data-cap)
    pages = []
    for d in ("", "about", "members", "research", "publications", "board"):
        base = os.path.join(ROOT, d) if d else ROOT
        pages += [os.path.join(base, f) for f in os.listdir(base) if f.endswith(".html")]

    touched = 0
    for full in pages:
        s0 = io.open(full, encoding="utf-8").read()
        s = re.sub(r"\[(\d{4})\.(\d{2})\]\s*(?=[^<]*(?:</b>|</span>|</a>|\"))", "", s0)
        if s != s0:
            io.open(full, "w", encoding="utf-8", newline="\n").write(s)
            touched += 1

    left = sum(1 for f in pages if BRACKET.search(io.open(f, encoding="utf-8").read()))
    print("상세 %d장 제목 정리, %d장에서 대괄호 제거, 남은 페이지 %d장"
          % (len(titles), touched, left))


if __name__ == "__main__":
    main()
