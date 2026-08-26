#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""하위 페이지 15장을 순수 HTML 로 찍어내는 1회성 생성기.

    python _build_pages.py

산출물은 의존성 없는 정적 HTML 이다. **HTML 을 직접 손본 뒤에는 이 스크립트를 다시 돌리지 말 것**
(덮어쓴다). 콘텐츠를 계속 스크립트로 관리하고 싶으면 ../hai-lab-homepage 쪽 구조를 쓰는 게 맞다.

원본 사이트의 서브 페이지 골격을 그대로 따른다:
    .subCon > .sub_titbox(.tit + .location) + .sub_body
    섹션 제목 앞에는 원본과 같이 '›'(.subBullet) 를 붙인다.
"""
import hashlib
import html
import io
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "..", "hai-lab-homepage", "data")
SRC_IMG = os.path.join(ROOT, "..", "hai-lab-homepage")
IMG = os.path.join(ROOT, "assets", "img")

# 원본 사이트의 대메뉴 트리 (index.html 사이드바와 동일)
NAV = [
    ("About", [("Research Area", "about/index.html"), ("Lab log", "about/lab-log.html"),
               ("Facility", "about/facility.html"), ("Patent", "about/patents.html")]),
    ("Members", [("Professor", "members/index.html"), ("Researcher", "members/researcher.html"),
                 ("Alumni", "members/alumni.html"), ("History", "members/history.html")]),
    ("Research", [("Projects", "research/index.html"), ("Seminars", "research/seminars.html"),
                  ("Video", "research/videos.html")]),
    ("Publications", [("Publications", "publications/index.html")]),
    ("Board", [("News", "board/index.html"), ("Gallery", "board/gallery.html"),
               ("V-log", "board/vlog.html")]),
]

# 현재 렌더 중인 페이지의 깊이에 맞춘 상대경로 접두사. write() 가 매 페이지마다 갱신한다.
PREFIX = ""


def rel(path):
    """루트 기준 경로를 현재 페이지 기준 상대경로로."""
    return PREFIX + path

used_images = set()


def load(name):
    with io.open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def e(s):
    return html.escape(str(s or ""), quote=True)


def img(src, alt="", cls=""):
    """이미지 경로를 클론 폴더 기준으로 바꾸고 복사 대상에 등록."""
    if not src:
        return '<span class="noimg" aria-hidden="true"></span>'
    if src.startswith("http"):
        return '<img src="%s" alt="%s"%s loading="lazy">' % (e(src), e(alt), _cls(cls))
    used_images.add(src)
    return '<img src="%sassets/img/%s" alt="%s"%s loading="lazy">' % (
        PREFIX, e(os.path.basename(src)), e(alt), _cls(cls))


def _cls(c):
    return ' class="%s"' % e(c) if c else ""


def link(url, label, cls="lnk"):
    if not url:
        return e(label)
    return '<a class="%s" href="%s" target="_blank" rel="noopener">%s</a>' % (e(cls), e(url), e(label))



def asset(rel_path):
    """assets/... 경로에 내용 해시를 붙인다. 파일이 바뀌면 URL 이 바뀌므로
    브라우저가 옛 CSS/JS 를 계속 물고 있는 사고가 구조적으로 생기지 않는다."""
    full = os.path.join(ROOT, rel_path)
    try:
        h = hashlib.md5(io.open(full, "rb").read()).hexdigest()[:8]
    except OSError:
        return PREFIX + rel_path
    return "%s%s?v=%s" % (PREFIX, rel_path, h)


# ------------------------------------------------------------------ 골격
def sidebar(active_file):
    out = []
    for top, subs in NAV:
        files = [f for _, f in subs]
        is_open = active_file in files
        if len(subs) == 1:
            out.append(
                '<li><a href="%s" class="d1 no-sub%s">%s</a></li>'
                % (rel(subs[0][1]), " on" if is_open else "", e(top)))
            continue
        items = "".join(
            '<li><a href="%s"%s>%s</a></li>'
            % (rel(f), ' class="on"' if f == active_file else "", e(lb))
            for lb, f in subs)
        out.append(
            '<li class="%s"><a href="#" class="d1">%s</a><ul class="depth2">%s</ul></li>'
            % ("is-open" if is_open else "", e(top), items))
    return "".join(out)


def crumb(top, label, file):
    # 대메뉴와 페이지명이 같으면(Publications) 한 번만 노출한다
    mid = "" if top == label else '<li><span>%s</span></li>' % e(top)
    return (
        '<div class="location"><ul id="LocationPath">'
        '<li><a class="home" href="%s">Home</a></li>' % rel("index.html") +
        '%s<li><a href="%s">%s</a></li>'
        "</ul></div>" % (mid, rel(file), e(label)))


PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | SeoulTech HAI Lab</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/moonspam/NanumSquare@2.0/nanumsquare.css">
<link rel="stylesheet" href="{css_style}">
<link rel="stylesheet" href="{css_sub}">
<link rel="stylesheet" href="{css_extra}">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
</head>
<body>
<a class="skip" href="#content">본문 바로가기</a>

<div class="wrap">
  <div class="head-group">
    <div class="menu">
      <h1 class="logo"><a href="{home}"><img src="{logo}" alt="SeoulTech HAI Lab"></a></h1>
      <button class="m-toggle" aria-expanded="false" aria-controls="lnb" aria-label="전체메뉴 열기">
        <span></span><span></span><span></span>
      </button>
      <nav id="lnb" class="lnb" aria-label="주요 메뉴">
        <ul class="depth1">{nav}</ul>
      </nav>
    </div>
  </div>

  <div class="content" id="content">
    <div class="subCon">
      <div class="sub_titbox">
        <h2 class="tit">{title}</h2>
        {crumb}
      </div>
      <div class="sub_body">
{body}
      </div>
    </div>
  </div>
</div>

<footer id="footer">
  <div class="inner">
    <ul class="foot_menu">
      <li><a href="{f_about}">About</a></li>
      <li><a href="{f_members}">Members</a></li>
      <li><a href="{f_research}">Research</a></li>
      <li><a href="{f_pubs}">Publications</a></li>
      <li><a href="{f_board}">Board</a></li>
    </ul>
    <div class="foot_info">
      <p class="addr">서울특별시 노원구 공릉로 232 국립서울과학기술대학교 상상관 405호</p>
      <p class="tel">TEL. 02-970-9777 &nbsp;&nbsp; E-MAIL. kwseo@seoultech.ac.kr</p>
      <p class="copy">COPYRIGHT © SeoulTech HAI Lab. ALL RIGHTS RESERVED.</p>
    </div>
  </div>
</footer>

<script src="{js_main}"></script>
</body>
</html>
"""


def write(file, top, title, body, desc=""):
    global PREFIX
    PREFIX = "../" * file.count("/")          # about/lab-log.html -> "../"
    out = PAGE.format(
        title=e(title), desc=e(desc or "SeoulTech HAI Lab — %s" % title),
        nav=sidebar(file), crumb=crumb(top, title, file), body=body,
        css_style=asset("assets/css/style.css"), css_sub=asset("assets/css/sub.css"),
        css_extra=asset("assets/css/extra.css"), js_main=asset("assets/js/main.js"),
        home=rel("index.html"), logo=PREFIX + "assets/img/logo.png",
        f_about=rel("about/index.html"), f_members=rel("members/index.html"),
        f_research=rel("research/index.html"), f_pubs=rel("publications/index.html"),
        f_board=rel("board/index.html"))
    dest = os.path.join(ROOT, file)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    io.open(dest, "w", encoding="utf-8").write(out)
    print("  %-26s %6d bytes" % (file, len(out.encode("utf-8"))))


def sect(title, inner):
    """원본과 같은 '› 제목' 섹션 블록."""
    return ('<section class="sec">\n<h3 class="sec_tit">'
            '<i class="subBullet" aria-hidden="true">›</i>%s</h3>\n%s\n</section>\n'
            % (e(title), inner))


def filter_bar(values, axis="year", label="연도", all_label="전체"):
    """다축 필터 바. axis 는 항목의 data-<axis> 와 짝을 이룬다."""
    if len(values) < 2:
        return ""
    btns = '<button class="fbtn is-on" data-val="all">%s</button>' % e(all_label) + "".join(
        '<button class="fbtn" data-val="%s">%s</button>' % (e(v), e(lb)) for v, lb in values)
    return ('<div class="filterbar" data-axis="%s" role="group" aria-label="%s 선택">'
            '<span class="fcap">%s</span>%s'
            '<span class="fcount" aria-live="polite"></span></div>'
            % (e(axis), e(label), e(label), btns))


def cat_key(category):
    """'International · Journals' 같은 표시용 문자열을 안전한 필터 키로."""
    return (category or "").replace(" ", "-").replace("·", "").replace("--", "-").lower()


def year_filter(years, label="연도"):
    return filter_bar([(y, y) for y in years], "year", label)


# ------------------------------------------------------------------ 페이지
def p_about():
    a = load("about.json")
    areas = "".join(
        '<div class="track"><p class="track-title">%s</p><p class="track-desc">%s</p></div>'
        % (e(x["title"]), e(x["description"])) for x in a["areas"])
    doms = "".join('<li><b>%s</b><span>%s</span></li>' % (e(d["label"]), e(d["detail"]))
                   for d in a["domains"])
    body = (
        sect("HAI Lab Overview",
             '<p class="para">%s</p><p class="para en">%s</p>' % (e(a["overview_ko"]), e(a["overview_en"])))
        + sect("Research Areas", '<div class="tracks">%s</div>' % areas)
        + sect("Application Domains", '<ul class="domains">%s</ul>' % doms)
        + sect("Collaborators", '<figure class="collab">%s</figure>'
               % img(a["collaborators_image"], "HAI Lab 협력 기관")))
    write("about/index.html", "About", "Research Area", body, a["overview_ko"][:150])


def p_lablog():
    rows = load("lablog.json")
    years = sorted({r["year"] for r in rows if r["year"]}, reverse=True)
    items = "".join(
        '<li class="lrow" data-year="%s"><time>%s</time><p>%s</p>%s</li>'
        % (e(r["year"]), e(r["date"]), e(r["title"]),
           '<span class="tag">%s</span>' % e(r["tag"]) if r["tag"] else "")
        for r in rows)
    write("about/lab-log.html", "About", "Lab log",
          year_filter(years) + '<ul class="llist" data-filter="year">%s</ul>' % items
          + '<p class="empty" hidden>해당 연도의 기록이 없습니다.</p>',
          "연구실 기록 %d건" % len(rows))


def p_facility():
    rows = load("facility.json")
    items = "".join(
        '<article class="fac"><div class="fac_img">%s</div><div class="fac_body">'
        '<h4>%s <span class="qty">%s</span></h4><ul>%s</ul></div></article>'
        % (img(r["photo"], r["title"]), e(r["title"]), e(r["qty"]),
           "".join("<li>%s</li>" % e(s.strip()) for s in r["spec"].split("/") if s.strip()))
        for r in rows)
    write("about/facility.html", "About", "Facility", '<div class="facs">%s</div>' % items,
          "연구 장비 %d종" % len(rows))


def p_patents():
    rows = load("patents.json")
    years = sorted({r["year"] for r in rows if r["year"]}, reverse=True)
    items = "".join(
        '<li class="pat" data-year="%s"><span class="pat_y">%s</span><div>'
        '<h4>%s</h4><p class="inv">%s</p>'
        '<p class="meta"><span class="tag">%s</span>%s</p><p class="assignee">%s</p>'
        "</div></li>"
        % (e(r["year"]), e(r["year"]), e(r["title"]), e(r["inventors"]),
           e(r["kind"]), e(r["number"]), e(r["assignee"]))
        for r in rows)
    write("about/patents.html", "About", "Patent",
          year_filter(years) + '<ol class="patlist" data-filter="year">%s</ol>' % items
          + '<p class="empty" hidden>해당 연도의 특허가 없습니다.</p>',
          "특허 %d건" % len(rows))


def p_professor():
    p = load("professor.json")
    order = ["Education", "Careers", "Professional Activities", "Grants", "Awards",
             "Patents", "Teaching Courses", "Talks", "News"]
    blocks = []
    for k in order:
        rows = p["cv"].get(k) or []
        if not rows:
            continue
        li = "".join("<li>%s</li>" % (link(r["link"], r["text"], "cvlnk") if r["link"] else e(r["text"]))
                     for r in rows)
        blocks.append('<div class="cvb"><h4>%s <span class="n">%d</span></h4><ul>%s</ul></div>'
                      % (e(k), len(rows), li))
    prof = (
        '<div class="prof">'
        '<div class="prof_img">%s</div>'
        '<div class="prof_body">'
        '<h3>%s <span class="ko">%s</span></h3>'
        '<p class="role">%s</p><p class="aff">%s</p>'
        '<p class="major"><b>Research</b> %s</p>'
        '<dl class="prof_meta"><dt>Office</dt><dd>%s</dd><dt>Tel</dt><dd>%s</dd>'
        '<dt>Email</dt><dd><a href="mailto:%s">%s</a></dd></dl>'
        '<p>%s</p></div></div>'
        % (img(p["photo"], p["name"]), e(p["name"]), e(p["name_ko"]), e(p["role"]),
           e(p["affiliation"]), e(p["interests"]), e(p["office"]), e(p["tel"]),
           e(p["email"]), e(p["email"]), link(p["scholar"], "Google Scholar", "btn")))
    write("members/index.html", "Members", "Professor",
          prof + '<div class="cv">%s</div>' % "".join(blocks),
          "%s, %s" % (p["name"], p["role"]))



# 연구원별 소셜 링크. 값이 비어 있으면 아이콘은 나오되 링크는 걸리지 않는다(데모).
# 실제 주소가 정해지면 여기만 채우면 members.html 에 그대로 반영된다.
SOCIAL = {
    "Seung Eon Cha":  {"linkedin": "", "github": ""},
    "Daeun Kim":      {"linkedin": "", "github": ""},
    "Myeong Gi Seong": {"linkedin": "https://www.linkedin.com/in/sungmyeonggi", "github": "https://github.com/SUNGMYEONGGI"},
    "Yushin Kim":     {"linkedin": "", "github": ""},
}


def social_icons(name):
    s = SOCIAL.get(name)
    if not s:
        return ""
    out = []
    for key, icon, label in (("linkedin", "fa-linkedin", "LinkedIn"),
                             ("github", "fa-github", "GitHub")):
        url = s.get(key) or ""
        cls = "soc soc-%s" % key
        if url:
            out.append('<a class="%s" href="%s" target="_blank" rel="noopener" '
                       'aria-label="%s %s"><i class="fa-brands %s" aria-hidden="true"></i></a>'
                       % (cls, e(url), e(name), label, icon))
        else:
            out.append('<span class="%s is-demo" role="img" aria-label="%s %s (준비 중)">'
                       '<i class="fa-brands %s" aria-hidden="true"></i></span>'
                       % (cls, e(name), label, icon))
    return '<p class="socials">%s</p>' % "".join(out)


def person(m, badge=True):
    lnks = []
    if m.get("email"):
        lnks.append('<a class="pill" href="mailto:%s">Email</a>' % e(m["email"]))
    if m.get("scholar"):
        lnks.append(link(m["scholar"], "Scholar", "pill"))
    b = '<span class="mbadge">%s</span>' % e(m["badge"]) if badge and m.get("badge") else ""
    return ('<article class="mcard"><div class="mphoto">%s%s</div>'
            '<h4>%s</h4><p class="mrole">%s</p><p class="mint">%s</p>'
            '<p class="mlnk">%s</p>%s</article>'
            % (img(m.get("photo"), m["name"]), b, e(m["name"]),
               e(m.get("role", "")), e(m.get("interests", "")), "".join(lnks),
               social_icons(m["name"])))


def p_members():
    d = load("members.json")
    groups = "".join(
        '<section class="sec"><h3 class="sec_tit"><i class="subBullet" aria-hidden="true">›</i>%s '
        '<span class="n">%d</span></h3><div class="mgrid">%s</div></section>'
        % (e(g["group"]), len(g["people"]), "".join(person(x) for x in g["people"]))
        for g in d["groups"])
    shot = ('<figure class="team_shot">%s<figcaption>%s</figcaption></figure>'
            % (img(d["photo"], d["photo_caption"]), e(d["photo_caption"])))
    write("members/researcher.html", "Members", "Researcher", shot + groups, "HAI Lab 구성원")


def p_alumni():
    d = load("alumni.json")
    years = sorted({a["year"] for a in d["alumni"] if a["year"]}, reverse=True)

    def card(a, vis=False):
        works = ""
        if a.get("works"):
            li = "".join("<li>%s</li>" % (link(w["link"], w["text"], "cvlnk") if w["link"] else e(w["text"]))
                         for w in a["works"])
            works = ('<details class="works"><summary>Paper works <span class="n">%d</span></summary>'
                     "<ol>%s</ol></details>" % (len(a["works"]), li))
        role = link(a["link"], a["role"], "lnk") if a.get("link") else e(a.get("role", ""))
        extra = ('<p class="diss"><b>Dissertation</b> %s</p>' % e(a["dissertation"])) if a.get("dissertation") \
            else ('<p class="diss"><b>Research</b> %s</p>' % e(a.get("interests", "")) if a.get("interests") else "")
        return ('<article class="acard"%s><div class="aphoto">%s</div><div class="abody">'
                '<p class="ayear">%s</p><h4>%s</h4><p class="anow">%s</p>%s%s</div></article>'
                % ("" if vis else ' data-year="%s"' % e(a["year"]),
                   img(a.get("photo"), a["name"]), e(a.get("year", "")), e(a["name"]), role, extra, works))

    body = (
        '<section class="sec"><h3 class="sec_tit"><i class="subBullet" aria-hidden="true">›</i>'
        'Visiting Faculty <span class="n">%d</span></h3><div class="acards">%s</div></section>'
        % (len(d["visiting"]), "".join(card(v, True) for v in d["visiting"]))
        + '<section class="sec"><h3 class="sec_tit"><i class="subBullet" aria-hidden="true">›</i>'
          'Alumni (M.S.) <span class="n">%d</span></h3>%s'
          '<div class="acards" data-filter="year">%s</div>'
          '<p class="empty" hidden>해당 연도의 졸업생이 없습니다.</p></section>'
          % (len(d["alumni"]), year_filter(years, "졸업연도"),
             "".join(card(a) for a in d["alumni"])))
    write("members/alumni.html", "Members", "Alumni", body, "졸업생과 방문 교수")


def p_history():
    rows = load("history.json")
    by = {}
    for r in rows:
        by.setdefault(r["role"], []).append(r)
    blocks = []
    for role, items in by.items():
        li = "".join(
            '<li class="hrow%s">%s<div><p class="hname">%s</p><p class="hwhen">%s</p></div>%s</li>'
            % (" now" if r["current"] else "", img(r["photo"], r["name"]),
               e(r["name"]), e(r["period"]),
               '<span class="tag on">현재</span>' if r["current"] else "")
            for r in items)
        blocks.append(sect(role, '<ul class="hlist">%s</ul>' % li))
    write("members/history.html", "Members", "History", "".join(blocks), "연구실 운영 이력")


def p_projects():
    rows = load("projects.json")
    years = sorted({re.sub(r"\D", "", p["period"])[:4] for p in rows if p["period"]}, reverse=True)

    def card(p):
        meta = [m.strip() for m in p["meta"].split("/")
                if m.strip() and not m.strip().startswith(("게시일", "nttSeq"))]
        chips = "".join('<span class="tag">%s</span>' % e(m) for m in meta[:4])
        y = re.sub(r"\D", "", p["period"])[:4]
        return ('<article class="proj" data-year="%s"><div class="proj_img">%s</div>'
                '<div class="proj_body"><p class="proj_top"><span class="tag %s">%s</span>'
                '<time>%s</time></p><h4>%s</h4><p class="proj_desc">%s</p>'
                '<p class="chips">%s</p></div></article>'
                % (e(y), img(p["photo"], p["title"]),
                   "on" if p["status"] == "ongoing" else "off",
                   "Ongoing" if p["status"] == "ongoing" else "Completed",
                   e(p["period"].split("(")[0].strip()), e(p["title"]), e(p["description"]), chips))

    n_on = sum(1 for p in rows if p["status"] == "ongoing")
    write("research/index.html", "Research", "Projects",
          '<p class="lead">총 %d개 과제 · 진행 중 %d개</p>' % (len(rows), n_on)
          + year_filter(years, "시작연도")
          + '<div class="projs" data-filter="year">%s</div>' % "".join(card(p) for p in rows)
          + '<p class="empty" hidden>해당 연도의 과제가 없습니다.</p>',
          "연구 과제 %d건" % len(rows))


def p_seminars():
    rows = load("seminars.json")
    terms = []
    for r in rows:
        if r["term"] and r["term"] not in terms:
            terms.append(r["term"])
    li = "".join(
        '<li class="sem" data-term="%s"><time>%s</time><div><h4>%s</h4>'
        '<p class="by">%s</p><p class="term">%s</p>%s</div>%s</li>'
        % (e(r["term"]), e(r["date"]), e(r["title"]), e(r["presenter"]), e(r["term"]),
           '<p class="note">%s</p>' % e(r["note"]) if r["note"] else "",
           link(r["link"], "Slides", "pill") if r["link"] else "")
        for r in rows)
    write("research/seminars.html", "Research", "Seminars",
          '<p class="lead">랩 세미나 발표 자료 %d건 · %d개 학기</p>' % (len(rows), len(terms))
          + filter_bar([(t, t) for t in terms], "term", "학기")
          + '<ul class="semlist" data-filter="term">%s</ul>' % li
          + '<p class="empty" hidden>해당 학기의 세미나가 없습니다.</p>',
          "세미나 %d건" % len(rows))


def vid_grid(items):
    return '<div class="vids">%s</div>' % "".join(
        '<a class="vid" href="%s" target="_blank" rel="noopener">'
        '<span class="vthumb">%s<span class="play"></span></span>'
        '<span class="vtit">%s</span></a>'
        % (e(v["url"]), img(v["thumb"], v["title"]), e(v["title"])) for v in items)


def p_videos():
    d = load("videos.json")
    write("research/videos.html", "Research", "Video",
          '<p class="lead">논문 발표 영상 %d편</p>' % len(d["research"]) + vid_grid(d["research"]),
          "연구 발표 영상")


def p_vlog():
    d = load("videos.json")
    write("board/vlog.html", "Board", "V-log",
          '<p class="lead">학회 참관기와 연구실 일상 %d편</p>' % len(d["vlog"]) + vid_grid(d["vlog"]),
          "연구실 브이로그")


def p_publications():
    pubs = load("publications.json")
    years = sorted({p["year"] for p in pubs if p["year"]}, reverse=True)
    cnt = {}
    for p in pubs:
        cnt[p["category"]] = cnt.get(p["category"], 0) + 1
    summary = "".join('<li><b>%d</b><span>%s</span></li>' % (v, e(k))
                      for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]))

    def row(p):
        badges = "".join('<span class="bdg">%s</span>' % e(b) for b in p["badges"])
        lnks = []
        if p["link"]:
            lnks.append(link(p["link"], "Paper", "pill"))
        for l in p["links"]:
            lnks.append(link(l["url"], l["label"], "pill"))
        intl = p["category"].startswith("International")
        kind = "Journal" if "Journal" in p["category"] else "Conference"
        return ('<li class="pub" data-year="%s" data-cat="%s"><span class="pub_y">%s</span><div class="pub_b">'
                '<p class="pub_m"><span class="kind %s">%s</span>%s</p>'
                '<h4>%s</h4><p class="authors">%s</p><p class="venue">%s</p>%s</div></li>'
                % (e(p["year"]), e(cat_key(p["category"])), e(p["year"]), "intl" if intl else "dom",
                   e("%s · %s" % ("International" if intl else "Domestic", kind)),
                   badges, e(p["title"]), e(p["authors"]), e(p["venue"]),
                   '<p class="plnk">%s</p>' % "".join(lnks) if lnks else ""))

    cats = [(cat_key(k), "%s (%d)" % (k, v))
            for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])]
    write("publications/index.html", "Publications", "Publications",
          '<ul class="pubsum">%s</ul>' % summary
          + filter_bar(cats, "cat", "구분") + year_filter(years)
          + '<ol class="publist" data-filter="year">%s</ol>' % "".join(row(p) for p in pubs)
          + '<p class="empty" hidden>해당 연도의 논문이 없습니다.</p>',
          "논문 %d편" % len(pubs))


def p_news():
    rows = load("news.json")
    years = sorted({r["year"] for r in rows if r["year"]}, reverse=True)
    items = "".join('<li class="lrow" data-year="%s"><time>%s</time><p>%s</p></li>'
                    % (e(r["year"]), e(r["date"]), e(r["title"])) for r in rows)
    write("board/index.html", "Board", "News",
          year_filter(years) + '<ul class="llist" data-filter="year">%s</ul>' % items
          + '<p class="empty" hidden>해당 연도의 소식이 없습니다.</p>',
          "연구실 소식 %d건" % len(rows))


def p_gallery():
    rows = load("gallery.json")
    years = sorted({r["year"] for r in rows if r["year"]}, reverse=True)
    items = "".join(
        '<figure class="gitem" data-year="%s">'
        '<button class="gbtn" data-full="%sassets/img/%s" data-cap="%s">'
        '<span class="thumb">%s<span class="plus">+</span></span></button>'
        '<figcaption><time>%s</time>%s</figcaption></figure>'
        % (e(r["year"]), PREFIX, e(os.path.basename(r["photo"])), e(r["title"]),
           img(r["photo"], r["title"]), e(r["date"]), e(r["title"]))
        for r in rows if r.get("photo"))
    lb = ('<div class="lightbox" id="lightbox" hidden>'
          '<button class="lb_close" aria-label="닫기">&times;</button>'
          '<button class="lb_prev" aria-label="이전 사진">&#8249;</button>'
          '<img class="lb_img" alt="">'
          '<button class="lb_next" aria-label="다음 사진">&#8250;</button>'
          '<p class="lb_cap"></p></div>')
    write("board/gallery.html", "Board", "Gallery",
          year_filter(years) + '<div class="gallery" data-filter="year">%s</div>' % items
          + '<p class="empty" hidden>해당 연도의 사진이 없습니다.</p>' + lb,
          "연구실 사진 %d장" % len(rows))


# (빌더, 출력 경로) — 경로를 먼저 알아야 본문 안의 이미지 경로를 정확히 만들 수 있다.
PAGES = [
    (p_about, "about/index.html"), (p_lablog, "about/lab-log.html"),
    (p_facility, "about/facility.html"), (p_patents, "about/patents.html"),
    (p_professor, "members/index.html"), (p_members, "members/researcher.html"),
    (p_alumni, "members/alumni.html"), (p_history, "members/history.html"),
    (p_projects, "research/index.html"), (p_seminars, "research/seminars.html"),
    (p_videos, "research/videos.html"), (p_publications, "publications/index.html"),
    (p_news, "board/index.html"), (p_gallery, "board/gallery.html"),
    (p_vlog, "board/vlog.html"),
]


def main():
    global PREFIX
    print("페이지 생성:")
    for fn, path in PAGES:
        # 본문(img·data-full)이 만들어지기 전에 깊이를 확정해 둔다
        PREFIX = "../" * path.count("/")
        fn()
    # 참조된 이미지를 클론 폴더로 복사
    os.makedirs(IMG, exist_ok=True)
    copied = missing = 0
    for rel in sorted(used_images):
        s = os.path.join(SRC_IMG, rel)
        d = os.path.join(IMG, os.path.basename(rel))
        if os.path.exists(s):
            if not os.path.exists(d):
                shutil.copy2(s, d)
            copied += 1
        else:
            missing += 1
            print("  [없음]", rel)
    print("\n이미지 %d개 확보 (누락 %d)" % (copied, missing))
    print("assets/img 파일 수:", len(os.listdir(IMG)))


if __name__ == "__main__":
    main()
