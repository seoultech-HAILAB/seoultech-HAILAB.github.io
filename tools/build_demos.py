#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Research > Demos 의 목록과 상세를 tools/demos_data.json 으로 찍는다.

    python tools/build_demos.py

Projects 와 같은 짜임이다 — 목록에서 고르고 들어가면 그 하나만 있다.
상세는 네 단이다: Try It · Video · Notes · Publications.

상세는 영어 단일이다. 시연물(키오스크 화면·챗봇 프로토콜)이 영문 연구 산출물이라
반쪽만 옮기면 더 어색했다 — Publications 처럼 한국어 사이트 안의 영문 콘텐츠로 둔다.
한글 짝(title_ko·lead_ko·know[].ko)은 검색 색인 전용이다 (build_search_index.py).

시연 자체는 여기서 만들지 않는다. assets/demos/ 에 있는 실제 구현을 불러다 앉힐 뿐이다.
그 구현은 논문에 쓴 것 그대로다 — 키오스크는 JMIR 검증 연구의 화면(panel01~08)을
클릭 판정까지, 자기노출 챗봇은 연구 프로토콜의 문장을 그대로 읽는다.

데모를 더할 때는 json 에 항목을 넣고 이 스크립트를 돌린 뒤 tidy_pages.py 를 돌린다.
"""
import html
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "research", "videos.html")   # 머리·꼬리를 빌려 온다


def e(t):
    return html.escape(str(t or ""), quote=True)


def load():
    p = os.path.join(ROOT, "tools", "demos_data.json")
    return json.loads(io.open(p, encoding="utf-8").read())


def paper(x):
    """바탕이 된 논문 한 줄. url 이 있으면 제목이 곧 링크다.

    "group" 이 붙은 항목 앞에는 소제목 줄을 하나 깐다 — 키오스크는 검증 연구
    세 편과 후속 연구 여덟 편이 있어, 한 줄로 쭉 늘어놓으면 어느 것이
    이 데모의 논문인지 안 보인다."""
    head = ""
    if x.get("group"):
        head = '<li class="dp_group">%s</li>' % e(x["group"])
    tit = e(x["title"])
    if x.get("url"):
        tit = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(x["url"]), tit)
    note = ' <span class="dp_note">%s</span>' % e(x["note"]) if x.get("note") else ""
    return (head +
            '<li><span class="dp_y">%s</span>'
            '<span class="dp_b"><b>%s</b>'
            '<span class="dp_v">%s%s</span></span></li>'
            % (e(x["year"]), tit, e(x["venue"]), note))


def skeleton(title, crumb_leaf, body, desc, head=None):
    """videos.html 의 골격에 제목과 본문만 갈아 끼운다.

    head 는 페이지 머리(h2.tit)에 적을 이름이다. 상세에서는 글 제목이 아니라
    구역 이름("Demos")을 넣는다 — Projects 상세가 그렇게 한다."""
    s = io.open(TPL, encoding="utf-8").read()
    s = re.sub(r"<title>[^<]*</title>",
               "<title>%s | SeoulTech HAI Lab</title>" % e(title), s)
    s = re.sub(r'<meta name="description" content="[^"]*">',
               '<meta name="description" content="%s">' % e(desc), s)
    s = s.replace('<h2 class="tit">Video</h2>',
                  '<h2 class="tit">%s</h2>' % e(head or title))
    # 빵부스러기의 마지막 칸(Video)을 이 페이지 것으로 바꾼다.
    # 문서 전체에서 찾으면 네비의 Video 항목을 먼저 만나 메뉴가 망가진다 —
    # 실제로 데모 두 페이지의 메뉴에 글 제목이 박혀 있었다. 그 블록 안에서만 바꾼다.
    def _crumb(m):
        return re.sub(r'<li><a href="[^"]*research/videos\.html"[^>]*>Video</a></li>',
                      crumb_leaf, m.group(0), count=1)
    s = re.sub(r'<ul id="LocationPath">.*?</ul>', _crumb, s, count=1, flags=re.S)
    s = re.sub(r'(<div class="sub_body">).*?(\s*</div>\s*</div>\s*</main>)',
               lambda m: m.group(1) + "\n" + body + m.group(2), s, flags=re.S)
    s = re.sub(r'<script src="\.\./assets/js/video\.js[^"]*"></script>\s*', "", s)
    # 골격을 videos.html 에서 빌려 오면서 네비의 현재 표시(class="on")까지 딸려 왔다 —
    # 데모 페이지의 드롭다운에 Video 가 켜져 있었다. Demos 로 옮긴다.
    m = re.search(r'<nav [^>]*class="lnb".*?</nav>', s, re.S)
    if m:
        nav = m.group(0)
        nav = nav.replace('research/videos.html" class="on"', 'research/videos.html"')
        nav = re.sub(r'(<a href="[^"]*research/demos\.html")>', r'\1 class="on">', nav, count=1)
        s = s[:m.start()] + nav + s[m.end():]
    return s


def card(d):
    """목록 카드. 두 건뿐이라 전폭 가로줄로 깔면 오른쪽이 통째로 비어 보였다 —
    Projects(28건)의 짜임을 그대로 쓰던 자리다. 격자 칸으로 세운다."""
    tags = "".join('<span class="tag">%s</span>' % e(t) for t in d["tags"])
    # 카드 그림은 영상 포스터 — 영상용으로 만든 장면이라 카드에서도 설명이 된다.
    # 없으면 유튜브 자동 프레임으로 물러난다.
    thumb = ("../" + e(d["poster"])) if d.get("poster") else (
        "https://img.youtube.com/vi/%s/hqdefault.jpg" % e(d["youtube"]))
    # alt 는 제목으로 채운다 — Projects·Gallery 목록이 그렇게 한다. 여기만
    # 비워 두고 있었고, 그래서 손으로 채운 것이 build 때마다 지워졌다.
    return (
        '<a class="dcard" href="demo-%s.html">'
        '<span class="dcard_shot"><img src="%s" alt="%s" loading="lazy"></span>'
        '<span class="dcard_body">'
        '<span class="tag on">%s</span>'
        '<span class="dcard_tit">%s</span>'
        '<span class="dcard_lead">%s</span>'
        '<span class="chips">%s</span>'
        "</span></a>"
        % (e(d["slug"]), thumb, e(d["title"]), e(d["category"]),
           e(d["title"]), e(d["lead"]), tags))


def list_page(demos, desc=None):
    """목록 페이지.

    설명글(meta description)은 demos_data.json 의 list_desc 를 쓴다. 검색결과에
    그대로 실리는 문장이라 "시연 2건" 같은 기계 문장으로는 약하다. 손으로 고친
    것을 페이지에 두면 다음 build 에 지워지므로 데이터 쪽에 둔다 — 실제로
    한 번 지워졌다. {n} 자리에 건수가 들어가 데모를 더해도 숫자는 따라온다."""
    body = '<div class="dcards">%s</div>' % "".join(card(d) for d in demos)
    desc = (desc or "HAI Lab 연구를 직접 해 보는 시연 {n}건").format(n=len(demos))
    return skeleton("Demos", '<li><a href="../research/demos.html">Demos</a></li>',
                    body, desc)


def detail_page(d):
    pl = d.get("play")

    def sec(title, inner):
        return ('<section class="sec"><h3 class="sec_tit">'
                '<i class="subBullet" aria-hidden="true">›</i>%s</h3>%s</section>'
                % (title, inner))

    play = ""
    if pl:
        play = sec("Try It", '<div class="demo_play">%s</div>' % pl["mount"])

    watch = ""
    if d.get("video"):
        # bogyeompark.github.io 에서 데모용으로 만든 영상 — 유튜브 중계 없이 직접 싣는다.
        # preload="none" 이라 포스터만 먼저 오고, 영상은 누를 때 받는다.
        watch = sec("Video",
                    '<div class="demo_video"><video controls playsinline preload="none" '
                    'poster="../%s" width="1280" height="720">'
                    '<source src="../%s" type="video/mp4"></video></div>'
                    % (e(d["poster"]), e(d["video"])))
    elif d.get("youtube"):
        watch = sec("Video",
                    '<div class="demo_video"><iframe src="https://www.youtube.com/embed/%s?rel=0" '
                    'title="%s" loading="lazy" '
                    'allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture" '
                    "allowfullscreen></iframe></div>"
                    % (e(d["youtube"]), e(d["title"])))

    # know 에는 <b> 를 쓰므로 이스케이프하지 않는다
    know = sec("Notes", '<ul class="demo_know">%s</ul>'
               % "".join("<li>%s</li>" % x["en"] for x in d["know"]))

    # 학회 이름만 적어 두고 논문으로 가는 길이 없었다. 제목·학회·연도를 적고 링크를 단다.
    papers = sec("Publications",
                 '<ul class="demo_papers">%s</ul>'
                 '<p class="demo_back"><a class="pill" href="demos.html">← All demos</a></p>'
                 % "".join(paper(x) for x in d["papers"]))

    body = (
        '<article class="demo">'
        '<p class="demo_top"><span class="tag on">%s</span></p>'
        '<h3 class="demo_title">%s</h3>'
        '<p class="demo_sub">%s</p>'
        '<p class="demo_people">%s</p>'
        "%s%s%s%s</article>"
        % (e(d["category"]), e(d["title"]), e(d["lead"]), e(d["people"]),
           play, watch, know, papers))

    # 머리에 같은 말이 겹쳐 있었다 — 글 제목이 h2.tit·빵부스러기·본문에 세 번 나왔다.
    # Projects 상세처럼 머리와 빵부스러기는 구역 이름("Demos")에서 멈추고,
    # 글 제목은 본문에 한 번만 둔다.
    crumb = '<li><a href="../research/demos.html">Demos</a></li>'
    page = skeleton(d["title"], crumb, body, d["lead"][:150], head="Demos")

    if pl:
        css_tag = '<link rel="stylesheet" href="../%s">' % pl["css"]
        anchor_css = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com'
        page = page.replace(anchor_css, css_tag + "\n" + anchor_css, 1)

        # 시연이 먼저 읽어야 하는 자료 파일(data)을 평범한 스크립트로 앞에 싣는다.
        # 키오스크가 이것 없이 나가 있었다 — 화면 그림은 글자를 뺀 판(-en.webp)인데
        # 글자를 담은 kiosk-en.js 가 실리지 않아, 여덟 장이 전부 백지로 떴다.
        # module 은 defer 라 평범한 스크립트가 항상 먼저 돈다.
        tags = ['<script src="../%s"></script>' % e(x) for x in pl.get("data", [])]
        tags.append('<script type="module" src="../%s"></script>' % e(pl["js"]))
        anchor_js = '<script src="../assets/js/main.js'
        page = page.replace(anchor_js, "\n".join(tags) + "\n" + anchor_js, 1)
    return page


def main():
    data = load()
    demos = data["demos"]
    out = os.path.join(ROOT, "research")

    # 목록에서 뺀 데모의 상세 페이지가 남아 있으면 걷어낸다
    keep = {"demo-%s.html" % d["slug"] for d in demos}
    for f in sorted(os.listdir(out)):
        if f.startswith("demo-") and f.endswith(".html") and f not in keep:
            os.remove(os.path.join(out, f))
            print("  지움  research/%s" % f)

    io.open(os.path.join(out, "demos.html"), "w", encoding="utf-8",
            newline="\n").write(list_page(demos, data.get("list_desc")))
    print("  research/demos.html        목록 %d건" % len(demos))

    for d in demos:
        p = os.path.join(out, "demo-%s.html" % d["slug"])
        io.open(p, "w", encoding="utf-8", newline="\n").write(detail_page(d))
        print("  research/demo-%-16s %s" % (d["slug"] + ".html", d["title"]))

    print("\n다음: python tools/tidy_pages.py")


if __name__ == "__main__":
    main()
