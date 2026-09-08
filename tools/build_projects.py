#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""과제 목록(research/index.html)의 카드를 첫 화면 Key Projects 와 같은 꼴로 다시 찍는다.

    python tools/build_projects.py

카드 하나: 그림(진행 중이면 Ongoing 칩) · 기간 · 제목 · 한 줄 소개 · 지원기관 로고+이름 · 금액 ·
키워드 둘 · 화살표. 소개와 키워드는 tools/projects_data.json 에 적어 둔다.
과제의 사실 자료(제목·기간·역할·지원기관·금액·그림)는 카드에 이미 있는 것을 읽어
data-role / data-sponsor / data-short 속성에 옮겨 둔다 — build_home.py, build_areas.py 가 거기서 읽는다.
몇 번을 돌려도 결과는 같다. 돌린 뒤 build_home.py → build_areas.py → build_list_pages.py → tidy_pages.py.
"""
import html
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.loads(io.open(os.path.join(ROOT, "tools", "projects_data.json"), encoding="utf-8").read())

def rd(rel): return io.open(os.path.join(ROOT, rel), encoding="utf-8", newline="").read()
def wr(rel, s): io.open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="").write(s)
def e(s): return html.escape(s, quote=True)
def plain(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def won(sponsor):
    """'… (KRW 3.03 billion)' → '₩ 3,030,000,000'"""
    m = re.search(r"KRW\s+([\d.]+)\s*(billion|million)", sponsor)
    if not m: return ""
    n = float(m.group(1)) * (1e9 if m.group(2) == "billion" else 1e6)
    return "₩ %s" % format(int(round(n)), ",")

def facts(a):
    """옛 카드든 새 카드든 같은 사실을 뽑는다."""
    seq, title = re.search(r'<h4><a href="project/(\d+)\.html">(.*?)</a>', a, re.S).groups()
    img = re.search(r'<img src="(\.\./[^"]+)"', a).group(1)
    tm = plain(re.search(r"<time[^>]*>(.*?)</time>", a, re.S).group(1))
    on = 'class="tag on"' in a
    d = dict(re.findall(r'data-(role|sponsor|short)="([^"]*)"', a))
    if "sponsor" not in d:                       # 옛 카드: 칩에서
        chips = [plain(c) for c in re.findall(r'<span class="tag">(.*?)</span>', a, re.S)]
        d = dict(role=chips[0] if chips else "", sponsor=chips[1] if len(chips) > 1 else "", short=chips[2] if len(chips) > 2 else "")
    else:
        d = {k: html.unescape(v) for k, v in d.items()}
    year, status = re.search(r'data-year="(\d+)" data-status="(\w+)"', a).groups()
    ko = re.search(r'<p class="proj_ko">(.*?)</p>', a, re.S)
    return dict(seq=seq, title=title, img=img, when=tm, on=on, year=year, status=status,
                role=d.get("role", ""), sponsor=d.get("sponsor", ""), short=d.get("short", ""), ko=plain(ko.group(1)) if ko else "")

def card(f):
    p = DATA["projects"].get(f["seq"])
    if not p: print("  소개·키워드 없음 (projects_data.json 에 더할 것):", f["seq"], f["title"][:50]); p = dict(desc="", tags=[])
    name = f["sponsor"].split(" (")[0].strip()
    short = DATA["sponsor_short"].get(name) or DATA["sponsor_short"].get(f["short"]) or f["short"] or name
    logo = DATA["logos"].get(short) or DATA["logos"].get(name)
    sp = ('<img class="proj_splogo" src="../assets/img/%s" alt="">' % logo) if logo else '<i class="fa-regular fa-building proj_spico" aria-hidden="true"></i>'
    when = re.sub(r"(\d{4}\.\d{2})\.\d{2}", r"\1", f["when"]).replace(" ~ ", " – ")
    amt = won(f["sponsor"])
    href = "project/%s.html" % f["seq"]
    return ('<article class="proj" data-year="%s" data-status="%s" data-role="%s" data-sponsor="%s" data-short="%s">'
            '<a class="proj_img" href="%s" tabindex="-1" aria-hidden="true"><img src="%s" alt="" loading="lazy">%s</a>'
            '<div class="proj_body"><time class="proj_when">%s</time><h4><a href="%s">%s</a></h4>%s'
            '<p class="proj_desc">%s</p>'
            '<p class="proj_fund"><span class="proj_sp">%s<span>%s</span></span>%s</p>'
            '<p class="proj_tags">%s<a class="pub_go" href="%s" aria-label="Open project"><span aria-hidden="true">→</span></a></p>'
            '</div></article>'
            % (f["year"], f["status"], e(f["role"]), e(f["sponsor"]), e(f["short"]),
               href, f["img"], '<span class="tag on">Ongoing</span>' if f["on"] else "",
               e(when), href, f["title"], ('<p class="proj_ko">%s</p>' % e(f["ko"])) if f["ko"] else "",
               e(p["desc"]), sp, e(short), ('<b class="proj_amt">%s</b>' % amt) if amt else "",
               "".join('<span class="tag">%s</span>' % e(t) for t in p["tags"]), href))

def main():
    rel = "research/index.html"; s = rd(rel); n = 0
    def sub(m):
        nonlocal n; n += 1
        return card(facts(m.group(0)))
    s = re.sub(r'<article class="proj".*?</article>', sub, s, flags=re.S)
    wr(rel, s)
    print("research/index.html: 과제 카드 %d개" % n)

if __name__ == "__main__":
    main()
