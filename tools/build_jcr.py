#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""학술지 논문의 JCR 배지(SSCI/SCIE · 분위 · 상위 %)를 한 기준으로 다시 찍고 하이라이트 비율을 맞춘다.

    python tools/build_jcr.py

기준: 게재 연도의 JCR, 그 학술지가 든 카테고리 가운데 가장 높은 순위. 자료는 tools/jcr_data.json
(2026-09-08 JCR 사이트에서 직접 읽음). 새 논문이 들어오면 거기에 한 줄 더하고 다시 돌린다.
배지 규칙: 색인(plain) · Q1(bdg-q1)/Q2~4(plain) · 상위 10% 안이면 Top N%(bdg-top, N은 올림) ·
note 가 있으면 Top N% 대신 그 글(bdg-top). 하이라이트의 Q1 비율·Top 5% 비율도 여기서 센다.
돌린 뒤 build_fwci.py --offline → build_list_pages.py → build_areas.py → tidy_pages.py.
"""
import html
import io
import json
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tools", "jcr_data.json")

def rd(rel): return io.open(os.path.join(ROOT, rel), encoding="utf-8", newline="").read()
def wr(rel, s): io.open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="").write(s)
def plain(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def badges(d):
    out = ['<span class="bdg bdg-plain">%s</span>' % d["edition"]]
    out.append('<span class="bdg %s">%s</span>' % ("bdg-q1" if d["quartile"] == "Q1" else "bdg-plain", d["quartile"]))
    pct = d["rank"] / d["total"] * 100
    if d.get("note"): out.append('<span class="bdg bdg-top">%s</span>' % html.escape(d["note"]))
    elif pct <= 10: out.append('<span class="bdg bdg-top">Top %d%%</span>' % math.ceil(pct))
    return "".join(out), pct

def main():
    rows = json.loads(io.open(DATA, encoding="utf-8").read())["papers"]
    p = "publications/index.html"; s = rd(p)
    cnt = dict(j=0, q1=0, top=0); used = set()
    def fix(m):
        li = m.group(0)
        if "journal" not in re.search(r'data-cat="([^"]+)"', li).group(1): return li
        title = plain(re.search(r"<h4>(.*?)</h4>", li, re.S).group(1)); year = re.search(r'data-year="(\d+)"', li).group(1)
        hit = [r for r in rows if title.lower().startswith(r["title"].lower()) and str(r["year"]) == year]
        if not hit:
            print("  JCR 자료 없음 (배지 없이 둔다): %s %s" % (year, title[:60])); return li
        d = hit[0]; used.add(d["title"])
        if d.get("edition") is None: return re.sub(r'<p class="pub_m">.*?</p>', '<p class="pub_m"></p>', li, count=1, flags=re.S)
        b, pct = badges(d); cnt["j"] += 1; cnt["q1"] += d["quartile"] == "Q1"; cnt["top"] += pct <= 5
        return re.sub(r'<p class="pub_m">.*?</p>', '<p class="pub_m">%s</p>' % b, li, count=1, flags=re.S)
    s = re.sub(r'<li class="pub".*?</li>', fix, s, flags=re.S)
    for r in rows:
        if r["title"] not in used: print("  목록에 없는 자료: %s" % r["title"])
    q1, top = round(cnt["q1"] / cnt["j"] * 100), round(cnt["top"] / cnt["j"] * 100)
    s = re.sub(r'(<span class="pubhi_num">)\d+%(</span></div><p class="pubhi_lab">Q1 Journal)', lambda m: "%s%d%%%s" % (m.group(1), q1, m.group(2)), s, count=1)
    s = re.sub(r'(<span class="pubhi_num">)\d+%(</span></div><p class="pubhi_lab">Top 5% Journal)', lambda m: "%s%d%%%s" % (m.group(1), top, m.group(2)), s, count=1)
    s = s.replace('<p class="pubhi_note">* Based on publications since 2021</p>',
                  '<p class="pubhi_note">* Publications since 2021; journal ranks from the JCR of each publication year</p>')
    wr(p, s)
    print("JCR 배지: 학술지 %d편 · Q1 %d편 (%d%%) · Top 5%% %d편 (%d%%)" % (cnt["j"], cnt["q1"], q1, cnt["top"], top))

if __name__ == "__main__":
    main()
