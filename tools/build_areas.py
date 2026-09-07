#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Research Areas(about/index.html)의 본문을 목록 페이지에서 채운다.

    python tools/build_areas.py

분야 셋(Agentic AI · Physical AI · AI for Social Good)마다 한 줄씩:
  왼쪽  번호·아이콘·제목·설명·키워드 (AREAS 에 적어 둔다)
  가운데 Selected Projects — research/index.html 의 과제 두 개 (번호로 고른다, 한 줄 소개는 BLURB)
  오른쪽 Selected Publications — publications/index.html 의 논문 두 편 (제목 앞머리로 고른다. 학술지와 CHI 만 고른다)
맨 아래 Our Partners 띠는 첫 화면과 같은 꼴이되 협력기관 전부를 흘린다.
<!-- areas:start --> … <!-- areas:end -->, <!-- partners:start --> … <!-- partners:end --> 사이만 바꾼다.
과제·논문이 바뀌면 여기 목록을 고치고 다시 돌린 뒤 tidy_pages.py 로 마무리한다.
"""
import html
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def rd(rel): return io.open(os.path.join(ROOT, rel), encoding="utf-8", newline="").read()
def wr(rel, s): io.open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="").write(s)
def e(s): return html.escape(s, quote=True)
def plain(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

AREAS = [
    dict(no="01", ico="fa-solid fa-brain", tit="Agentic AI",
         desc="AI systems that reason, act, and collaborate with humans.",
         tags=["LLM Agents", "Multi-Agent Systems", "Human-Agent Interaction", "Human-in-the-Loop AI"],
         projects=["259", "257"],
         pubs=["Design System-Compliant User Interface Generation", "Assessing Critical Thinking through a Multi-Agent LLM-Based Debate"]),
    dict(no="02", ico="fa-solid fa-robot", tit="Physical AI",
         desc="AI systems that perceive, understand, and interact with the physical world.",
         tags=["Vision-Language-Action", "Multimodal AI", "Embodied AI", "Human Sensing & Behavior"],
         projects=["256", "258"],
         pubs=["Assessing Adaptive Behavior in Individuals with Intellectual Disability", "Exploring the Relationship between Behavioral and Neurological Impairments"]),
    dict(no="03", ico="fa-solid fa-people-group", tit="AI for Social Good",
         desc="Applying AI to real-world challenges for a more inclusive and sustainable society.",
         tags=["Healthcare & Well-being", "Education & Learning", "Accessibility & Inclusion", "Future of Work"],
         projects=["183", "255"],
         pubs=["LLM-based chatbots for academic stress counseling", "Enhancing academic stress assessment through self-disclosure chatbots"]),
]
BLURB = {  # 과제 번호 → 한 줄 소개
    "259": "Automated accessibility diagnosis and UI generation with expert-context multi-agent AI.",
    "257": "An organize–monitor–analyze agent for automated quality control of measurement data.",
    "256": "A 70B-scale expandable vision-language-action foundation model on aggregated distributed GPUs.",
    "258": "Agentic vision-language-action models that evaluate UI/UX from user behavior.",
    "183": "Real-time on-device AI for self-guided hemorrhage management in vascular intervention.",
    "255": "Usability evaluation of a compound AI tutoring system built on LLMs and multimodal data.",
}
SHORT = {"Ministry of Science and ICT": "MSIT", "Ministry of Trade, Industry and Energy": "MOTIE",
         "National Research Foundation of Korea": "NRF", "Public–Private Joint Tech Commercialization R&D": "Public–Private R&D",
         "RISE Program": "RISE"}

def projects():
    s = rd("research/index.html"); out = {}
    for a in re.findall(r'<article class="proj".*?</article>', s, re.S):
        m = re.search(r'<h4><a href="project/(\d+)\.html">(.*?)</a>', a, re.S)
        tm = re.search(r"<time>(.*?)</time>", a).group(1)
        chips = [plain(c) for c in re.findall(r'<span class="tag">(.*?)</span>', a, re.S)]
        name = chips[1].split(" (")[0].strip() if len(chips) > 1 else ""
        out[m.group(1)] = dict(
            title=m.group(2), on='class="tag on"' in a,
            period=re.sub(r"(\d{4}\.\d{2})\.\d{2}", r"\1", tm).replace(" ~ ", " – "),
            sponsor=SHORT.get(name, name), img=re.search(r'<img src="\.\./([^"]+)"', a).group(1))
    return out

def pubs():
    s = rd("publications/index.html"); out = []
    for li in re.findall(r'<li class="pub".*?</li>', s, re.S):
        out.append(dict(
            title=re.search(r"<h4>(.*?)</h4>", li, re.S).group(1),
            kind=re.search(r'<span class="kind [^"]*">.*?</span>', li, re.S).group(0).replace("<br>", " · "),
            badges="".join(re.findall(r'<span class="bdg[^"]*">.*?</span>', li)),
            authors=re.search(r'<p class="authors">(.*?)</p>', li, re.S).group(1),
            venue=re.search(r'<p class="venue">(.*?)</p>', li, re.S).group(1),
            link=(re.search(r'class="pub_go" href="([^"]+)"', li) or [None, ""])[1]))
    return out

def find_pub(all_pubs, prefix):
    for p in all_pubs:
        if plain(p["title"]).lower().startswith(prefix.lower()): return p
    raise SystemExit("논문을 못 찾음: " + prefix)

def build_areas():
    P, L = projects(), pubs(); rows = []
    for i, a in enumerate(AREAS, 1):
        cards = []
        for q in a["projects"]:
            p = P[q]
            cards.append('<a class="sp" href="../research/project/%s.html"><span class="sp_img"><img src="../%s" alt="" loading="lazy"></span>'
                         '<span class="sp_badges"><span class="hm_badge hm_badge--on">%s</span><span class="hm_badge">%s</span></span>'
                         '<strong class="sp_tit">%s</strong><span class="sp_desc">%s</span><span class="sp_meta">%s</span></a>'
                         % (q, p["img"], "Ongoing" if p["on"] else "Completed", e(p["sponsor"]), p["title"], e(BLURB.get(q, "")), e(p["period"])))
        items = []
        for pre in a["pubs"]:
            p = find_pub(L, pre)
            go = '<a class="pub_go" href="%s" target="_blank" rel="noopener" aria-label="Open paper"><span aria-hidden="true">→</span></a>' % p["link"] if p["link"] else ""
            items.append('<div class="spub"><div><p class="spub_b">%s%s</p><strong class="spub_tit">%s</strong>'
                         '<p class="spub_au">%s</p><p class="spub_v">%s</p></div>%s</div>'
                         % (p["kind"], p["badges"], p["title"], p["authors"], p["venue"], go))
        rows.append(
            '<div class="area area--%d"><div class="area_l"><span class="area_no">%s</span>'
            '<div class="area_head"><span class="area_ico"><i class="%s" aria-hidden="true"></i></span><div><h4 class="area_tit">%s</h4>'
            '<p class="area_desc">%s</p></div></div><div class="area_tags">%s</div></div>'
            '<div class="area_c"><div class="sel_head"><b>Selected Projects</b><a href="../research/index.html">View all projects <span aria-hidden="true">→</span></a></div>'
            '<div class="sel_projs">%s</div></div>'
            '<div class="area_r"><div class="sel_head"><b>Selected Publications</b><a href="../publications/index.html">View all publications <span aria-hidden="true">→</span></a></div>'
            '<div class="sel_pubs">%s</div></div></div>'
            % (i, a["no"], a["ico"], e(a["tit"]), e(a["desc"]), "".join("<span>%s</span>" % e(t) for t in a["tags"]), "".join(cards), "".join(items)))
    return ('<section class="sec areas" id="areas"><h3 class="sec_tit"><i class="subBullet" aria-hidden="true">›</i>Research Areas</h3>'
            '<div class="area_list">%s</div></section>' % "".join(rows))

def partner_logos(s):
    """지금 페이지의 협력기관 블록에서 (파일, 이름) 을 순서대로 — 처음엔 분야별 판, 다음부터는 띠 자체."""
    m = re.search(r'<div class="partners">.*?</div>\s*</section>', s, re.S) or re.search(r"<!-- partners:start -->.*?<!-- partners:end -->", s, re.S)
    block = m.group(0)
    out = []
    for mm in re.finditer(r'<img[^>]*src="\.\./assets/img/([^"]+)"[^>]*alt="([^"]*)"|<img[^>]*alt="([^"]*)"[^>]*src="\.\./assets/img/([^"]+)"|<li class="pname">([^<]*)</li>|<span class="pband_txt">([^<]*)<', block):
        if mm.group(1): out.append((mm.group(1), html.unescape(mm.group(2))))
        elif mm.group(4): out.append((mm.group(4), html.unescape(mm.group(3))))
        else: out.append((None, html.unescape(mm.group(5) or mm.group(6))))
    return out

def build_partners(logos):
    def li(f, name):
        if f is None: return '<li><span class="pband_txt">%s</span></li>' % e(name)
        return '<li><img src="../assets/img/%s" alt="%s" loading="lazy"></li>' % (f, e(name))
    track = "".join(li(f, n) for f, n in logos)
    dur = max(70, round(70 * len(logos) / 8))
    return ('<section class="sec pband pband--in" id="partners" aria-label="Our Partners"><div class="inner">'
            '<div class="pband_head"><div><span class="hm_kicker">Our Partners</span><h3>Working with Leading Partners</h3>'
            '<p class="hm_sub">We collaborate with experts across healthcare, education, industry, government, and global academia.</p></div></div>'
            '<div class="pband_marq"><ul class="pband_track" style="animation-duration:%ds">%s</ul><ul class="pband_track" style="animation-duration:%ds" aria-hidden="true">%s</ul></div>'
            '</div></section>' % (dur, track, dur, track))

def main():
    p = "about/index.html"; s = rd(p)
    if "<!-- areas:start -->" not in s:
        i = s.find('<section class="sec">\n<h3 class="sec_tit"><i class="subBullet" aria-hidden="true">›</i>Research Areas</h3>')
        assert i > 0, "Research Areas 절이 없다"
        j = s.find("</section>", i) + len("</section>")
        s = s[:i] + "<!-- areas:start -->\n<!-- areas:end -->" + s[j:]
    if "<!-- partners:start -->" not in s:
        logos = partner_logos(s)
        i = s.find('<section class="sec" id="partners">'); assert i > 0, "협력기관 절이 없다"
        j = s.find("</section>", i) + len("</section>")
        s = s[:i] + "<!-- partners:start -->\n<!-- partners:end -->" + s[j:]
    else:
        logos = partner_logos(s)
    s = re.sub(r"<!-- areas:start -->.*?<!-- areas:end -->", lambda m: "<!-- areas:start -->\n%s\n<!-- areas:end -->" % build_areas(), s, count=1, flags=re.S)
    s = re.sub(r"<!-- partners:start -->.*?<!-- partners:end -->", lambda m: "<!-- partners:start -->\n%s\n<!-- partners:end -->" % build_partners(logos), s, count=1, flags=re.S)
    wr(p, s)
    print("about/index.html: 분야 %d · 협력기관 로고 %d" % (len(AREAS), len(logos)))

if __name__ == "__main__":
    main()
