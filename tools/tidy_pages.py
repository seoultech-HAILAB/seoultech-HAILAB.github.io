#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전 페이지에 같은 규칙을 한 번에 적용한다.

    python tools/tidy_pages.py

페이지가 214장이라 손으로 고치면 반드시 몇 장이 빠진다. 여기서 하는 일:

  1. 푸터 메뉴 삭제 — 위 메뉴와 같은 것을 아래에 한 번 더 두고 있었다
  2. 검색·도우미 스크립트를 모든 페이지에 — 검색창은 어느 페이지에나 있는데
     정작 검색을 시키는 스크립트는 첫 화면에만 실려 있었다
  3. 도우미 버튼을 모든 페이지에 — 첫 화면에만 떠 있었다
  4. ?v= 캐시 번호를 파일 내용으로 다시 매김 — 값이 실제 파일과 어긋나 있어
     다시 찾아온 사람은 옛 CSS 를 계속 보게 된다
  5. 글 상세의 '이전 글/다음 글' 을 바로잡음 — 최신 글에 '다음 글' 이 달려 있었다
  6. 사진 격자가 이중으로 감싸여 있던 것을 한 겹으로
"""
import hashlib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean_post_html import tidy_flow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFLICT = re.compile(r"-DESKTOP-[^.]*\.html$", re.I)

PAGES = []
for d in ("", "about", "members", "research", "publications", "board"):
    p = os.path.join(ROOT, d) if d else ROOT
    for f in sorted(os.listdir(p)):
        # 구글·네이버 소유확인 파일은 페이지가 아니다 — 내용이 한 글자라도 바뀌면
        # 확인이 깨지므로 tidy 도, 사이트맵도 건드리지 않는다.
        if f.startswith(("google", "naver")):
            continue
        # OneDrive 가 두 대 이상에서 같은 파일을 만졌을 때 남기는 충돌 사본
        # (index-DESKTOP-이름.html). 배포되지 않는 곁가지인데 사이트맵에 들어가면
        # 검색엔진에 없는 주소를 알려 주고, tidy 도 헛일을 한다.
        if CONFLICT.search(f):
            continue
        if f.endswith(".html"):
            PAGES.append(os.path.join(d, f).replace("\\", "/"))


def stamp(rel_path):
    """파일 내용의 md5 앞 8자리. 내용이 바뀌면 주소가 바뀌므로 캐시가 알아서 비워진다."""
    with io.open(os.path.join(ROOT, rel_path), "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


STAMPS = {
    "assets/css/style.css": stamp("assets/css/style.css"),
    "assets/css/sub.css": stamp("assets/css/sub.css"),
    "assets/css/extra.css": stamp("assets/css/extra.css"),
    "assets/js/main.js": stamp("assets/js/main.js"),
    "assets/js/search.js": stamp("assets/js/search.js"),
    "assets/js/ask.js": stamp("assets/js/ask.js"),
}

AI_DOCK = """<!-- 도우미 — 답은 Cloudflare Worker(tools/hai-ask.worker.js)가 만든다.
     assets/js/ask.js 의 ASK_ENDPOINT 가 비어 있으면 '준비 중' 이라고만 답한다. -->
<div class="ai_dock">
  <div class="ai_panel" id="aiPanel" role="dialog" aria-label="HAI Lab 도우미" hidden>
    <div class="ai_top">
      <span class="ai_avatar">HAI</span>
      <span class="ai_who">
        <b>HAI Lab 도우미</b>
        <span class="state">최대한 신속하게 응답드리겠습니다</span>
      </span>
      <button class="ai_x" aria-label="닫기">&times;</button>
    </div>
    <div class="ai_body">
      <p class="ai_msg">안녕하세요, HAI Lab 안내 도우미입니다.<br>궁금한 것을 문의해 보세요!</p>
      <div class="ai_sugg">
        <span>대학원 지원은 어떻게 하나요?</span>
        <span>최근 CHI 논문이 궁금해요</span>
        <span>연구실 위치가 어디인가요?</span>
      </div>
    </div>
    <div class="ai_input">
      <span class="ph">메시지를 입력하세요.</span>
      <span class="send" aria-hidden="true">&#10148;</span>
    </div>
  </div>

  <button class="ai_fab" id="aiFab" aria-expanded="false" aria-controls="aiPanel"
          aria-label="AI 도우미 열기">
    <svg class="ai_fab_i ai_fab_chat" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M20.8 11.6a8.2 8.2 0 0 1-8.8 8.2 9 9 0 0 1-3.1-.6L4 20.8l1.3-4.3a8 8 0 0 1-1.6-4.9 8.2 8.2 0 0 1 8.2-8.2h.5a8.2 8.2 0 0 1 8.4 8.2z"/>
      <circle cx="8.7" cy="11.8" r="1.1" fill="currentColor" stroke="none"/>
      <circle cx="12" cy="11.8" r="1.1" fill="currentColor" stroke="none"/>
      <circle cx="15.3" cy="11.8" r="1.1" fill="currentColor" stroke="none"/>
    </svg>
    <svg class="ai_fab_i ai_fab_close" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2.1" stroke-linecap="round" aria-hidden="true">
      <path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>
    </svg>
  </button>
</div>
"""


def drop_footer_menu(s):
    return re.sub(r'\s*<ul class="foot_menu">.*?</ul>', "", s, flags=re.S)


def drop_video_js(s):
    """영상은 이제 글마다 제 페이지에서 재생한다. 목록에서 모달로 띄우던 시절의
    video.js 는 걸릴 대상(data-yt)이 한 군데도 없어 받아만 놓고 아무것도 하지 않는다."""
    return re.sub(r'\s*<script src="[^"]*assets/js/video\.js[^"]*"></script>', "", s)


def mark_project(s, rel):
    """과제 글에는 표식을 남긴다. 과제 구성도는 본문에서 이미 크게 보이므로
    사진처럼 눌러서 키울 필요가 없다 (CSS 가 이 표식을 보고 돋보기를 끈다)."""
    if not rel.startswith("research/project-"):
        return s
    return s.replace('<main class="content" id="content">',
                     '<main class="content" id="content" data-kind="project">')


SITE = "https://hai.seoultech.ac.kr"
GA_ID = "G-NW8LVNH5C4"   # Google Analytics 4 측정 ID — 방문 통계. 도메인이 바뀌어도 그대로 쓴다.


def ga_tag(s):
    """GA4 추적 코드를 전 페이지 <head> 끝에 심는다. 매 실행 갈아 끼워서
    ID 를 바꾸면 다음 tidy 때 전 페이지가 따라온다."""
    block = (
        "<!-- Google tag (gtag.js) -->\n"
        '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
        "<script>\n"
        "window.dataLayer = window.dataLayer || [];\n"
        "function gtag(){dataLayer.push(arguments);}\n"
        "gtag('js', new Date());\n"
        "gtag('config', '%s');\n"
        "</script>\n" % (GA_ID, GA_ID))
    # 주석 + <script> 두 개가 한 덩어리다. 비탐욕 .*? 는 첫 </script> 에서 멈춰
    # 안쪽 스크립트를 고아로 남겼다 — 두 개를 못박아 지운다.
    s = re.sub(r'<!-- Google tag \(gtag\.js\) -->\n(?:<script[^>]*>.*?</script>\n){2}',
               "", s, flags=re.S)
    # 위 버그가 이미 남긴 고아 스크립트도 쓸어낸다
    s = re.sub(r'<script>\nwindow\.dataLayer = window\.dataLayer \|\| \[\];\n.*?</script>\n',
               "", s, flags=re.S)
    return s.replace("</head>", block + "</head>", 1)


def share_image(s, rel):
    """링크를 공유했을 때 뜰 그림.

    전에는 어느 쪽이든 로고를 박았다. 그래서 사진 한 장 보여 주려고 붙인 갤러리
    글도 카카오톡에서는 죄다 같은 로고로 보였다. 글에 사진이나 영상이 있으면
    그것을 쓰고, 없을 때만 로고로 돌아간다."""
    seg = re.search(r'<div class="post_(?:gal|body|video)">.*?'
                    r'(?=<nav class="pnav"|<p class="post_back")', s, re.S)
    body = seg.group(0) if seg else ""
    if not body:
        mn = re.search(r'<main class="content"[^>]*>(.*?)</main>', s, re.S)
        if mn and "youtube.com/embed/" in mn.group(1):
            body = mn.group(1)
    pic = re.search(r'<img[^>]*src="([^"]+)"', body)
    if pic and not pic.group(1).startswith("http"):
        d = os.path.dirname(rel)
        return SITE + "/" + os.path.normpath(os.path.join(d, pic.group(1))).replace("\\", "/")
    if pic:
        return pic.group(1)
    yt = re.search(r"youtube\.com/embed/([\w-]+)", body)
    if yt:
        return "https://img.youtube.com/vi/%s/hqdefault.jpg" % yt.group(1)
    return SITE + "/assets/img/logo.png"


def og_tags(s, rel):
    """카카오톡·슬랙에 링크를 붙였을 때 제목·설명·로고가 나오게 한다.

    값은 그 페이지의 <title> 과 meta description 을 그대로 쓴다 — 따로 관리할
    원본을 만들지 않는다. 이미 있으면 (매 실행마다) 값만 갈아 끼운다."""
    t = re.search(r"<title>([^<]*)</title>", s)
    d = re.search(r'<meta name="description" content="([^"]*)"', s)
    if not t:
        return s
    url = SITE + "/" + ("" if rel == "index.html" else rel)
    lines = [
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="SeoulTech HAI Lab">',
        '<meta property="og:title" content="%s">' % t.group(1),
        '<meta property="og:description" content="%s">' % (d.group(1) if d else ""),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:image" content="%s">' % share_image(s, rel),
    ]
    s = re.sub(r'<meta property="og:[^>]*>\n?', "", s)          # 옛 블록 제거
    return s.replace("</title>", "</title>\n" + "\n".join(lines), 1)


VERIFY = {                                                        # 검색엔진 소유확인
    "naver-site-verification": "300a5b312990f7dc0e604f27f37ef4d352cd4d7c",       # 서치어드바이저
    "google-site-verification": "wjyXYWtsuy4igho-QR3Pp2yWKfvkWzuovUJAWu79iEM",   # Search Console
}


def verify_tags(s, rel):
    """소유확인 메타태그 — 둘 다 등록한 주소(홈)만 보므로 홈에만 심는다.
    매 실행 갈아 끼워서 값이 바뀌어도 tidy 한 번이면 따라온다. 홈이 아닌 쪽에서는
    지우기만 하므로, 손으로 붙여 엉뚱한 쪽에 퍼진 것이 있으면 여기서 거둬진다."""
    for name in VERIFY:
        s = re.sub(r'<meta name="%s"[^>]*>\n?' % name, "", s)
    if rel != "index.html":
        return s
    tags = "\n".join('<meta name="%s" content="%s" />' % (n, v) for n, v in VERIFY.items())
    return s.replace("</title>", "</title>\n" + tags, 1)


def canonical(s, rel):
    """정본 주소 표시. 같은 페이지가 ?v= 같은 변형 주소로 긁히면 검색엔진이
    서로 다른 문서로 세므로, 어느 주소가 원본인지 못박아 둔다. 매 실행 갱신."""
    url = SITE + "/" + ("" if rel == "index.html" else rel)
    s = re.sub(r'<link rel="canonical"[^>]*>\n?', "", s)
    return s.replace("</title>", '</title>\n<link rel="canonical" href="%s">' % url, 1)


def write_sitemap():
    """sitemap.xml + robots.txt — 구글 서치콘솔과 네이버 서치어드바이저에
    제출하는 파일. 페이지 목록(PAGES)에서 만들므로 글이 늘면 같이 는다."""
    # 404 는 검색에 올릴 쪽이 아니다 (noindex). 사이트맵에 넣으면 서치콘솔이
    # "색인 안 됨" 으로 계속 집어낸다.
    urls = [SITE + "/" + ("" if rel == "index.html" else rel)
            for rel in sorted(PAGES) if rel != "404.html"]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += ["<url><loc>%s</loc></url>" % u for u in urls]
    xml.append("</urlset>")
    io.open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8",
            newline="\n").write("\n".join(xml) + "\n")
    io.open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8", newline="\n").write(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)
    print("  sitemap.xml %d개 주소 / robots.txt" % len(urls))


def add_demos_nav(s, rel):
    """Research 메뉴에 Demos 를 넣는다.

    네비가 페이지마다 인라인이라 페이지를 새로 만들 때마다 빠지기 쉽다.
    (실제로 demos.html 자신의 메뉴에 Demos 가 없었다.)"""
    pre = "../" if "/" in rel else ""
    item = '<li><a href="%sresearch/demos.html">Demos</a></li>' % pre
    if item in s:
        return s
    m = re.search(r'<nav [^>]*class="lnb".*?</nav>', s, re.S)
    if not m:
        return s
    vid = re.compile(r'<li><a href="[^"]*research/videos\.html"[^>]*>Video</a></li>')
    if not vid.search(m.group(0)):
        return s
    nav = vid.sub(lambda x: x.group(0) + item, m.group(0), count=1)
    return s[:m.start()] + nav + s[m.end():]


def main_landmark(s):
    """본문을 <main> 으로. 화면 낭독기가 '본문으로' 한 번에 건너뛸 수 있게 한다.
    CSS 는 .content 클래스로 잡고 있어 모양은 그대로다."""
    s = s.replace('<div class="content" id="content">', '<main class="content" id="content">')
    if "<main class=" not in s:
        return s
    # 짝이 되는 </div> 를 </main> 으로 (본문 끝은 항상 '</div><!-- /.content -->'
    # 또는 푸터 직전의 닫는 태그 두 개다)
    s = s.replace('</div><!-- /.content -->', '</main><!-- /.content -->')
    if "</main>" not in s:
        i = s.find("</div>\n</div>\n\n<footer")
        if i > 0:
            s = s[:i] + "</main>\n</div>\n\n<footer" + s[i + len("</div>\n</div>\n\n<footer"):]
    return s


def restamp(s):
    def f(m):
        path, _ = m.group(1), m.group(2)
        key = path.lstrip("./").replace("../", "")
        v = STAMPS.get(key)
        return '%s?v=%s' % (path, v) if v else m.group(0)
    return re.sub(r'((?:\.\./)?assets/(?:css|js)/[a-z_.]+)\?v=([a-z0-9]+)', f, s)


def add_scripts(s, prefix):
    """검색·도우미 스크립트를 main.js 앞에 세운다 (없을 때만).

    이름이 페이지 어딘가에 있는지로 판단하면 안 된다. 도우미 마크업의 주석에도
    'assets/js/ask.js' 라고 적혀 있어서, 그것을 보고 이미 있다고 넘겨 버렸다.
    실제 <script> 태그가 있는지로만 판단한다."""
    main = '<script src="%sassets/js/main.js' % prefix
    i = s.find(main)
    if i < 0:
        return s
    add = []
    for name in ("search.js", "ask.js"):
        tag = re.compile(r'<script src="[^"]*assets/js/%s' % re.escape(name))
        if not tag.search(s):
            add.append('<script src="%sassets/js/%s?v=%s"></script>\n'
                       % (prefix, name, STAMPS["assets/js/" + name]))
    return s[:i] + "".join(add) + s[i:] if add else s


def add_ai_dock(s, prefix):
    """도우미 블록을 모든 쪽에 — 있으면 걷어내고 다시 넣는다.

    전에는 있으면 그냥 넘어갔다. 그래서 위 AI_DOCK 을 고쳐도 이미 붙어 있던 쪽은
    옛 모습 그대로였다. 정규식으로 갈아 끼우려다 패널 안의 닫기 버튼에서 먼저
    끊겨 블록이 두 겹이 된 적도 있다. 블록은 늘 본문 끝 <script> 앞에 있으니,
    그 구간을 통째로 들어내고 새로 넣는 편이 어떤 상태에서든 스스로 복구된다."""
    i = s.find("<!-- 도우미")
    if i < 0:
        i = s.find('<div class="ai_dock">')
    if i >= 0:
        j = s.find("<script", i)
        if j > i:
            s = s[:i] + s[j:]
    i = s.find("<script")
    return s[:i] + AI_DOCK + '\n' + s[i:] if i > 0 else s


def unnest_gallery(s):
    """사진 격자가 격자를 감싸고 있으면 한 겹으로 편다.

    원본 정리기가 문단 안의 사진을 격자로 묶은 뒤, 같은 사진들을 한 번 더 묶어서
    격자 안에 격자가 들어갔다. 안쪽 격자도 폭 1200px 규칙을 그대로 받아
    바깥 칸(592px)을 밀어내는 바람에 페이지에 가로 스크롤이 생겼다."""
    if '<div class="post_gal"><div class="post_gal">' not in s:
        return s
    out, i = [], 0
    open_tag = '<div class="post_gal">'
    while True:
        j = s.find(open_tag, i)
        if j < 0:
            out.append(s[i:])
            break
        out.append(s[i:j])
        # 이 격자의 끝(닫는 div)을 찾아 안쪽 격자만 벗긴다
        depth, k = 0, j
        while k < len(s):
            nd = s.find("<div", k)
            cd = s.find("</div>", k)
            if cd < 0:
                break
            if 0 <= nd < cd:
                depth += 1
                k = nd + 4
            else:
                depth -= 1
                k = cd + 6
                if depth == 0:
                    break
        block = s[j:k]
        inner = block[len(open_tag):-len("</div>")]
        inner = inner.replace(open_tag, "").replace("</div>", "")
        out.append(open_tag + inner + "</div>")
        i = k
    return "".join(out)


def fix_pnav(s):
    """목록이 최신 글부터라 배열의 앞 항목이 '더 새 글' 이다. 그런데 라벨은
    그대로 '이전 글' 이 붙어 있어서, 맨 위 최신 글에 '다음 글' 이 달려 있었다.
    라벨과 자리(더 새 글이 위)를 함께 바로잡는다."""
    m = re.search(r'<nav class="pnav"[^>]*>(.*?)</nav>', s, re.S)
    if not m:
        return s
    items = re.findall(r'<a class="pnav_i pnav_(prev|next)" href="([^"]+)">'
                       r'<span>[^<]*</span><b>(.*?)</b></a>', m.group(1), re.S)
    if not items:
        return s
    newer = older = None
    for kind, href, title in items:
        if kind == "prev":      # 배열 앞 = 더 새 글
            newer = (href, title)
        else:
            older = (href, title)
    rows = ""
    if newer:
        rows += ('<a class="pnav_i" href="%s"><span>다음 글</span><b>%s</b></a>'
                 % (newer[0], newer[1]))
    if older:
        rows += ('<a class="pnav_i" href="%s"><span>이전 글</span><b>%s</b></a>'
                 % (older[0], older[1]))
    return s[:m.start()] + '<nav class="pnav" aria-label="글 이동">%s</nav>' % rows + s[m.end():]


def tidy_body(s):
    """글 본문의 문단 간격을 한 가지로 맞춘다 (clean_post_html.tidy_flow)."""
    m = re.search(r'(<div class="post_body">)(.*?)(\n\s*</div>)', s, re.S)
    if not m:
        return s
    body = tidy_flow(m.group(2).strip())
    return s[:m.start()] + m.group(1) + "\n" + body + m.group(3) + s[m.end():]


def main():
    changed = 0
    for rel in PAGES:
        full = os.path.join(ROOT, rel)
        s0 = io.open(full, encoding="utf-8").read()
        prefix = "../" if "/" in rel else ""

        s = drop_footer_menu(s0)
        s = drop_video_js(s)
        s = main_landmark(s)
        s = mark_project(s, rel)
        s = add_demos_nav(s, rel)
        s = og_tags(s, rel)
        s = canonical(s, rel)
        s = verify_tags(s, rel)
        s = ga_tag(s)
        s = unnest_gallery(s)
        s = tidy_body(s)
        s = fix_pnav(s)
        s = add_ai_dock(s, prefix)
        s = add_scripts(s, prefix)
        s = restamp(s)

        if s != s0:
            io.open(full, "w", encoding="utf-8", newline="\n").write(s)
            changed += 1
    write_sitemap()
    print("%d/%d 장 수정" % (changed, len(PAGES)))
    for k, v in STAMPS.items():
        print("  %-24s ?v=%s" % (k, v))


if __name__ == "__main__":
    main()
