#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""첫 화면(index.html)의 머리띠 아래 블록들을 목록 페이지에서 다시 채운다.

    python tools/build_home.py

머리띠(.mainVisual)는 손대지 않는다. <!-- home:start --> 와 <!-- home:end --> 사이만
새로 만든다:

  1. What We Explore   — 연구 방향 셋 (이 파일의 AREAS 에 적어 둔다)
  2. Key Projects      — research/index.html 의 과제 중 FEATURED 에 적은 셋
  3. Latest News       — board/index.html 의 최신 넷. 사진·요약은 글 본문에서 꺼낸다.
                         tag_news.py 가 첫 화면의 소식 줄도 태그하므로
                         <li><a href="board/news/N.html"> + .ntag + .nsub/.subject 순서를 지킨다.
  4. Life at HAI       — board/gallery.html 의 최신 다섯 장 + board/vlog.html 의 최신 영상
  5. Our Partners      — 로고 띠 (PARTNERS 에 적어 둔다)

글이 늘면 다시 돌린다. 돌린 뒤에는 늘 그렇듯 tidy_pages.py 로 마무리한다.
"""
import html
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def rd(rel):
    return io.open(os.path.join(ROOT, rel), encoding="utf-8").read()

def e(s):
    return html.escape(s, quote=True)

def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def clip(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"

# ───────────────────────── 1. 연구 방향 ─────────────────────────
AREAS = [
    ("01", "fa-solid fa-brain", "Agentic AI",
     "AI systems that reason, act, and collaborate with humans.",
     ["LLM Agents", "Multi-Agent Systems", "Human-Agent Interaction", "AI Accessibility", "Explainable & Trustworthy AI"]),
    ("02", "fa-solid fa-robot", "Physical AI",
     "AI systems that perceive, understand, and interact with the physical world.",
     ["Vision-Language-Action", "Multimodal AI", "Embodied AI", "Human Sensing", "AR/VR & Spatial Computing"]),
    ("03", "fa-solid fa-people-group", "AI for Social Good",
     "Applying AI to real-world challenges for a more inclusive and sustainable society.",
     ["Healthcare & Well-being", "Education & Learning", "Accessibility & Inclusion", "Future of Work", "Human-AI Collaboration"]),
]

def head(kicker, title, sub, more_href, more_txt):
    return ('<div class="hm_head"><div><span class="hm_kicker">%s</span><h2>%s</h2><p class="hm_sub">%s</p></div>'
            '<a class="hm_more" href="%s">%s <span aria-hidden="true">→</span></a></div>'
            % (kicker, title, sub, more_href, more_txt))

def build_areas():
    cards = []
    for i, (no, ico, tit, desc, tags) in enumerate(AREAS, 1):
        cards.append(
            '<a class="hm_area hm_area--%d" href="about/index.html">'
            '<span class="hm_area_top"><span class="hm_area_ico"><i class="%s" aria-hidden="true"></i></span>'
            '<span><span class="hm_area_no">%s</span><strong class="hm_area_tit">%s</strong></span></span>'
            '<span class="hm_area_desc">%s</span>'
            '<span class="hm_tags">%s</span><span class="hm_arrow" aria-hidden="true">→</span></a>'
            % (i, ico, no, e(tit), e(desc), "".join("<span>%s</span>" % e(t) for t in tags)))
    return ('<section class="hm hm--areas" aria-label="What we explore">'
            + head("Our Research", "What We Explore",
                   "Advancing Human-Centered AI through three complementary research directions.",
                   "about/index.html", "View All Research Areas")
            + '<div class="hm_areas">%s</div></section>' % "".join(cards))

# ───────────────────────── 2. 대표 과제 ─────────────────────────
FEATURED = ["256", "183", "257"]         # research/project/<번호>.html — 비면 최신 셋
SPONSOR_KO = {
    "과학기술정보통신부": "과기정통부", "산업통상자원부": "산업부", "교육부": "교육부",
    "한국연구재단": "한국연구재단", "서울특별시교육청": "서울시교육청",
}

def krw(s):
    """'KRW 6 billion' / 'KRW 80 million' → '60억 원' / '0.8억 원'"""
    m = re.search(r"KRW\s+([\d.]+)\s*(billion|million)", s)
    if not m:
        return ""
    v = float(m.group(1)) * (10 if m.group(2) == "billion" else 0.01)
    return ("%g억 원" % round(v, 2))

def build_projects():
    s = rd("research/index.html")
    arts = re.findall(r'<article class="proj".*?</article>', s, re.S)
    by_seq = {}
    for a in arts:
        m = re.search(r'<h4><a href="project/(\d+)\.html">(.*?)</a>', a, re.S)
        if m:
            by_seq[m.group(1)] = (a, m.group(2))
    seqs = [q for q in FEATURED if q in by_seq] or list(by_seq)[:3]
    cards = []
    for q in seqs:
        a, title = by_seq[q]
        img = re.search(r'<img src="\.\./([^"]+)"', a).group(1)
        tm = re.search(r"<time>(.*?)</time>", a)
        period = re.sub(r"\.\d\d(\s*~\s*)", r"\1", tm.group(1)).replace(" ~ ", " ~ ") if tm else ""
        period = re.sub(r"(\d{4}\.\d{2})\.\d{2}", r"\1", tm.group(1)) if tm else ""
        on = 'class="tag on"' in a
        chips = [plain(c) for c in re.findall(r'<span class="tag">(.*?)</span>', a, re.S)]
        sponsor = chips[1] if len(chips) > 1 else ""
        name = sponsor.split(" (")[0].strip()
        short = chips[2] if len(chips) > 2 else name
        badge = SPONSOR_KO.get(name) or (short if re.search(r"[A-Za-z]", short) and len(short) <= 12 else "산학협력")
        if not SPONSOR_KO.get(name) and "KRW" in sponsor and not re.search(r"부$|재단$|청$|원$", name):
            badge = "산학협력"
        budget = krw(sponsor) or "비공개"
        cards.append(
            '<a class="hm_proj" href="research/project/%s.html">'
            '<span class="hm_proj_img"><img src="%s" alt="" loading="lazy"></span>'
            '<span class="hm_proj_body"><span class="hm_badges"><span class="hm_badge">%s</span>%s</span>'
            '<strong class="hm_proj_tit">%s</strong><span class="hm_proj_sub">%s</span>'
            '<span class="hm_proj_meta"><span>%s</span><span>%s</span><span class="hm_arrow" aria-hidden="true">→</span></span>'
            '</span></a>'
            % (q, img, e(badge), '<span class="hm_badge hm_badge--on">진행중</span>' if on else "",
               title, e(short) if short != badge else "", e(period), e(budget)))
    return ('<section class="hm hm--projects" aria-label="Key projects">'
            + head("Research in Action", "Key Projects", "Turning research ideas into real-world impact.",
                   "research/index.html", "View All Projects")
            + '<div class="hm_projs">%s</div></section>' % "".join(cards))

# ───────────────────────── 3. 최신 소식 ─────────────────────────
def build_news(n=4):
    s = rd("board/index.html")
    rows = re.findall(r'<li class="lrow"[^>]*>.*?</li>', s, re.S)[:n]
    items = []
    for r in rows:
        tag = re.search(r'<span class="ntag[^"]*">[^<]*</span>', r)
        a = re.search(r'<a href="(news/\d+\.html)">(.*?)</a>', r, re.S)
        date = re.search(r"<time>([\d.]+)</time>", r).group(1)
        post = rd("board/" + a.group(1))
        body = post[post.find('class="post_body"'):]
        img = re.search(r'src="\.\./\.\./(assets/img/posts/[^"]+)"', body)
        para = ""
        for p in re.findall(r"<p>(.*?)</p>", body, re.S):
            t = plain(p)
            if len(t) > 20:
                para = t
                break
        if img:
            shot = '<span class="hm_new_shot"><img src="%s" alt="" loading="lazy"></span>' % img.group(1)
        else:
            k = plain(tag.group(0)) if tag else "News"
            shot = '<span class="hm_new_shot hm_new_shot--ph"><span>%s</span></span>' % e(k)
        items.append(
            '<li><a href="board/%s">%s<span class="nsub"><span class="subject">%s</span></span>'
            '%s<time class="hm_new_date">%s</time><span class="hm_new_ex">%s</span></a></li>'
            % (a.group(1), tag.group(0) if tag else "", a.group(2), shot, date, e(clip(para, 90))))
    return ('<section class="hm hm--news" aria-label="Latest news">'
            + head("Latest News", "What’s Happening at HAI", "HAI Lab의 최신 소식을 만나보세요.",
                   "board/index.html", "View All News")
            + '<ul class="hm_news">%s</ul></section>' % "".join(items))

# ───────────────────────── 4. 연구실 일상 ─────────────────────────
def caption(t):
    m = re.search(r"\(([^()]*[A-Za-z][^()]*)\)\s*$", t)   # 괄호 안 영문이 있으면 그것
    return (m.group(1) if m else t).strip()

def build_life(n=5):
    s = rd("board/gallery.html")
    figs = re.findall(r'<figure class="gitem".*?</figure>', s, re.S)[:n]
    tiles = []
    for f in figs:
        img = re.search(r'<img src="\.\./([^"]+)"', f).group(1)
        a = re.search(r'<a href="(gallery/\d+\.html)">(.*?)</a>', f, re.S)
        tiles.append('<a class="hm_shot" href="board/%s"><span class="hm_shot_img"><img src="%s" alt="" loading="lazy"></span>'
                     '<span class="hm_shot_cap">%s</span></a>' % (a.group(1), img, e(clip(caption(plain(a.group(2))), 40))))
    v = rd("board/vlog.html")
    m = re.search(r'<a class="vid" href="(vlog/\d+\.html)"><span class="vthumb"><img src="([^"]+)" alt="([^"]*)"', v)
    if m:
        tiles.append('<a class="hm_shot hm_shot--video" href="board/%s"><span class="hm_shot_img"><img src="%s" alt="" loading="lazy">'
                     '<i class="fa-solid fa-circle-play" aria-hidden="true"></i></span><span class="hm_shot_cap">HAI Lab V-log</span></a>'
                     % (m.group(1), m.group(2)))
    return ('<section class="hm hm--life" aria-label="Life at HAI">'
            + head("Life at HAI", "Research, People, and Beyond", "함께 연구하고, 배우고, 성장하는 일상을 만나보세요.",
                   "board/gallery.html", "View Gallery")
            + '<div class="hm_life">%s</div></section>' % "".join(tiles))

# ───────────────────────── 5. 협력기관 띠 ─────────────────────────
PARTNERS = [
    ("logo-asan-medical-center.png", "서울아산병원 Asan Medical Center"),
    ("logo-microsoft.png", "Microsoft"),
    ("logo-hyundai.png", "현대자동차 Hyundai Motor Company"),
    ("logo-i-sens.png", "i-SENS"),
    ("logo-kitech.png", "KITECH 한국생산기술연구원"),
    ("logo-ubc.png", "The University of British Columbia"),
    (None, "Technion"),
    ("logo-smoe.png", "서울특별시교육청 Seoul Metropolitan Office of Education"),
]

def build_partners():
    def li(f, alt):
        if f is None:
            return '<li><span class="pband_txt">Technion<small>ISRAEL INSTITUTE OF TECHNOLOGY</small></span></li>'
        return '<li><img src="assets/img/%s" alt="%s" loading="lazy"></li>' % (f, e(alt))
    track = "".join(li(f, a) for f, a in PARTNERS)
    return ('<section class="pband" aria-label="Our Partners"><div class="inner">'
            + head("Our Partners", "Working with Leading Partners", "산업, 의료, 교육, 글로벌 연구기관과 함께합니다.",
                   "about/index.html#partners", "View All Partners")
            + '<div class="pband_marq"><ul class="pband_track">%s</ul><ul class="pband_track" aria-hidden="true">%s</ul></div>'
              '</div></section>' % (track, track))

# ───────────────────────── 끼워 넣기 ─────────────────────────
def main():
    p = os.path.join(ROOT, "index.html")
    s = io.open(p, encoding="utf-8", newline="").read()
    blocks = "\n".join([build_areas(), build_projects(), build_news(), build_life()])
    s, n = re.subn(r"<!-- home:start -->.*?<!-- home:end -->",
                   lambda m: "<!-- home:start -->\n%s\n<!-- home:end -->" % blocks, s, count=1, flags=re.S)
    assert n == 1, "index.html 에 <!-- home:start --> … <!-- home:end --> 가 없다"
    s, n = re.subn(r'<section class="pband".*?</section>', lambda m: build_partners(), s, count=1, flags=re.S)
    assert n == 1, "index.html 에 .pband 가 없다"
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("index.html: 연구 방향 %d · 과제 %d · 소식 %d · 일상 %d · 협력기관 %d"
          % (len(AREAS), blocks.count('class="hm_proj"'), blocks.count('class="nsub"'),
             blocks.count('class="hm_shot'), len(PARTNERS)))

if __name__ == "__main__":
    main()
