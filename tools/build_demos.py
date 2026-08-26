#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Research > Demos 의 목록과 상세를 tools/demos_data.json 으로 찍는다.

    python tools/build_demos.py

Projects 와 같은 짜임이다 — 목록에서 고르고 들어가면 그 하나만 있다.
상세는 세 단으로 나뉜다: 해 보기 · 보기 · 알아 둘 것.

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
    return json.loads(io.open(p, encoding="utf-8").read())["demos"]


def skeleton(title, crumb_leaf, body, desc):
    """videos.html 의 골격에 제목과 본문만 갈아 끼운다."""
    s = io.open(TPL, encoding="utf-8").read()
    s = re.sub(r"<title>[^<]*</title>",
               "<title>%s | SeoulTech HAI Lab</title>" % e(title), s)
    s = re.sub(r'<meta name="description" content="[^"]*">',
               '<meta name="description" content="%s">' % e(desc), s)
    s = s.replace('<h2 class="tit">Video</h2>', '<h2 class="tit">%s</h2>' % e(title))
    # 빵부스러기의 마지막 칸(Video)을 이 페이지 것으로 바꾼다.
    # 붙이기만 하면 'Research > Video > Demos' 가 된다.
    s = re.sub(r'<li><a href="[^"]*research/videos\.html"[^>]*>Video</a></li>',
               crumb_leaf, s, count=1)
    s = re.sub(r'(<div class="sub_body">).*?(\s*</div>\s*</div>\s*</main>)',
               lambda m: m.group(1) + "\n" + body + m.group(2), s, flags=re.S)
    s = re.sub(r'<script src="\.\./assets/js/video\.js[^"]*"></script>\s*', "", s)
    return s


def card(d):
    tags = "".join('<span class="tag">%s</span>' % e(t) for t in d["tags"])
    thumb = "https://img.youtube.com/vi/%s/hqdefault.jpg" % e(d["youtube"])
    return (
        '<article class="proj demo_card">'
        '<div class="proj_img"><img src="%s" alt="%s" loading="lazy"></div>'
        '<div class="proj_body">'
        '<p class="proj_top"><span class="tag on">%s</span></p>'
        '<h4><a href="demo-%s.html">%s</a></h4>'
        '<p class="demo_lead">%s</p>'
        '<p class="chips">%s</p>'
        "</div></article>"
        % (thumb, e(d["title"]), e(d["category"]), e(d["slug"]),
           e(d["title"]), e(d["lead"]), tags))


def list_page(demos):
    body = ('<p class="lead">논문으로 읽던 것을 직접 해 보는 자리입니다. '
            "연구에 쓴 것을 그대로 옮겨 두었습니다.</p>\n"
            '<div class="projs">%s</div>' % "".join(card(d) for d in demos))
    return skeleton("Demos", '<li><a href="../research/demos.html">Demos</a></li>',
                    body, "HAI Lab 연구를 직접 해 보는 시연 %d건" % len(demos))


def detail_page(d):
    pl = d.get("play")

    play = ""
    if pl:
        play = ('<section class="sec"><h3 class="sec_tit">'
                '<i class="subBullet" aria-hidden="true">›</i>해 보기</h3>'
                '<div class="demo_play">%s</div>'
                '<p class="demo_pnote">%s</p></section>'
                % (pl["mount"], e(pl.get("note", ""))))

    watch = ""
    if d.get("youtube"):
        watch = ('<section class="sec"><h3 class="sec_tit">'
                 '<i class="subBullet" aria-hidden="true">›</i>보기</h3>'
                 '<div class="demo_video"><iframe src="https://www.youtube.com/embed/%s?rel=0" '
                 'title="%s" loading="lazy" '
                 'allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture" '
                 "allowfullscreen></iframe></div>"
                 '<p class="demo_vnote">%s</p></section>'
                 % (e(d["youtube"]), e(d["title"]), e(d.get("watch_note", ""))))

    # know 에는 <b> 를 쓰므로 이스케이프하지 않는다
    know = "".join("<li>%s</li>" % x for x in d["know"])
    papers = "".join('<li><b>%s</b><span>%s</span></li>' % (e(x["label"]), e(x["note"]))
                     for x in d["papers"])

    body = (
        '<p class="demo_crumb"><a href="demos.html">Demos</a> <span>/</span> %s</p>'
        '<h3 class="demo_title">%s</h3>'
        '<p class="demo_sub">%s</p>'
        '<p class="demo_people">%s</p>'
        "%s%s"
        '<section class="sec"><h3 class="sec_tit">'
        '<i class="subBullet" aria-hidden="true">›</i>알아 둘 것</h3>'
        '<ul class="demo_know">%s</ul></section>'
        '<section class="sec"><h3 class="sec_tit">'
        '<i class="subBullet" aria-hidden="true">›</i>바탕이 된 연구</h3>'
        '<ul class="demo_papers">%s</ul>'
        '<p class="demo_back"><a class="pill" href="demos.html">← 데모 목록</a></p></section>'
        % (e(d["category"]), e(d["title"]), e(d["lead"]), e(d["people"]),
           play, watch, know, papers))

    crumb = ('<li><a href="../research/demos.html">Demos</a></li>'
             '<li><a href="../research/demo-%s.html">%s</a></li>'
             % (e(d["slug"]), e(d["title"])))
    page = skeleton(d["title"], crumb, body, d["lead"][:150])

    if pl:
        css_tag = '<link rel="stylesheet" href="../%s">' % pl["css"]
        anchor_css = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com'
        page = page.replace(anchor_css, css_tag + "\n" + anchor_css, 1)

        js_tag = '<script type="module" src="../%s"></script>' % pl["js"]
        anchor_js = '<script src="../assets/js/main.js'
        page = page.replace(anchor_js, js_tag + "\n" + anchor_js, 1)
    return page


def main():
    demos = load()
    out = os.path.join(ROOT, "research")

    # 목록에서 뺀 데모의 상세 페이지가 남아 있으면 걷어낸다
    keep = {"demo-%s.html" % d["slug"] for d in demos}
    for f in sorted(os.listdir(out)):
        if f.startswith("demo-") and f.endswith(".html") and f not in keep:
            os.remove(os.path.join(out, f))
            print("  지움  research/%s" % f)

    io.open(os.path.join(out, "demos.html"), "w", encoding="utf-8",
            newline="\n").write(list_page(demos))
    print("  research/demos.html        목록 %d건" % len(demos))

    for d in demos:
        p = os.path.join(out, "demo-%s.html" % d["slug"])
        io.open(p, "w", encoding="utf-8", newline="\n").write(detail_page(d))
        print("  research/demo-%-16s %s" % (d["slug"] + ".html", d["title"]))

    print("\n다음: python tools/tidy_pages.py")


if __name__ == "__main__":
    main()
