#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""크롤해 둔 원본 게시글로 상세 페이지를 찍어낸다.

    python tools/build_post_pages.py <크롤json디렉터리>

목록만 있고 눌러도 갈 곳이 없던 News / Projects / Gallery 에 글마다 한 장씩 만든다.
껍데기(머리·메뉴·푸터)는 board/index.html 에서 그대로 떠 오므로, 메뉴가 바뀌면
이 스크립트를 다시 돌리면 상세 페이지도 따라온다.
"""
import hashlib, html, io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean_post_html import clean, fix_typos

# 사진마다 '어디를 보여줄지'. 격자에 맞추느라 잘릴 때 사람이 날아가지 않게
# tools/smart_crop.py 가 미리 계산해 둔 값이다 (원본은 그대로 둔다).
_FOCAL = {}
_fp = os.path.join(ROOT, "tools", "focal_points.json") if False else None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOARDS = [
    # (크롤파일, 출력접두사, 목록페이지, 메뉴이름, 상위메뉴)
    ("news2",     "board/news-",       "board/index.html",    "News",     "Board"),
    ("projects2", "research/project-", "research/index.html", "Projects", "Research"),
    ("gallery2",  "board/gallery-",    "board/gallery.html",  "Gallery",  "Board"),
    ("videos2",   "research/video-",   "research/videos.html", "Video",   "Research"),
    ("vlog2",     "board/vlog-",       "board/vlog.html",     "V-log",    "Board"),
]


def local_name(url, renames):
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    ext = os.path.splitext(url.split("?")[0])[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".jpg"
    n = f"p{h}{ext}"
    n = renames.get(n, n)
    return n if os.path.exists(os.path.join(ROOT, "assets", "img", "posts", n)) else None


def load_focal():
    p = os.path.join(ROOT, "tools", "focal_points.json")
    if not os.path.exists(p):
        return {}
    return json.load(io.open(p, encoding="utf-8"))


def apply_focal(body, focal):
    """<img> 에 object-position 을 달아 준다. 잘려도 사람이 남는 자리로."""
    def f(m):
        tag = m.group(0)
        src = re.search(r'src="[^"]*/([^"/]+)"', tag)
        if not src:
            return tag
        xy = focal.get(src.group(1))
        if not xy or xy == [50, 50]:
            return tag
        return tag[:-1] + f' style="object-position:{xy[0]}% {xy[1]}%">'
    return re.sub(r"<img[^>]*>", f, body)


def shell():
    """board/index.html 에서 머리와 꼬리를 떠 온다. 한 곳만 고치면 전부 따라오게."""
    s = io.open(os.path.join(ROOT, "board", "index.html"), encoding="utf-8").read()
    head = s[:s.index('<div class="content"')]
    tail = s[s.index("<footer"):]
    return head, tail


def page(head, tail, *, title, date, body, menu, parent, list_href, prev, nxt):
    nav = ""
    if prev:
        nav += f'<a class="pnav_i pnav_prev" href="{prev[0]}"><span>이전 글</span><b>{html.escape(prev[1])}</b></a>'
    if nxt:
        nav += f'<a class="pnav_i pnav_next" href="{nxt[0]}"><span>다음 글</span><b>{html.escape(nxt[1])}</b></a>'

    h = head.replace("<title>News | SeoulTech HAI Lab</title>",
                     f"<title>{html.escape(title)} | SeoulTech HAI Lab</title>")
    h = re.sub(r'<meta name="description" content="[^"]*">',
               f'<meta name="description" content="{html.escape(re.sub(chr(60)+"[^"+chr(62)+"]*"+chr(62), " ", body)[:150].strip())}">', h)
    return f"""{h}<div class="content" id="content">
    <div class="subCon">
      <div class="sub_titbox">
        <h2 class="tit">{menu}</h2>
        <div class="location"><ul id="LocationPath"><li><a class="home" href="../index.html">Home</a></li><li><span>{parent}</span></li><li><a href="../{list_href}">{menu}</a></li></ul></div>
      </div>
      <div class="sub_body">
        <article class="post">
          <header class="post_head">
            <h3 class="post_tit">{html.escape(title)}</h3>
            <p class="post_meta"><time>{date}</time></p>
          </header>
          <div class="post_body">
{body}
          </div>
          <nav class="pnav" aria-label="글 이동">{nav}</nav>
          <p class="post_back"><a class="pill" href="../{list_href}">목록으로</a></p>
        </article>
        <div class="lightbox" id="lightbox" hidden><button class="lb_close" aria-label="닫기">&times;</button><button class="lb_prev" aria-label="이전 사진">&#8249;</button><img class="lb_img" alt=""><button class="lb_next" aria-label="다음 사진">&#8250;</button><p class="lb_cap"></p></div>
      </div>
    </div>
  </div>
</div>

{tail}"""


def main():
    src = sys.argv[1]
    renames = json.load(io.open(os.path.join(ROOT, "tools", "rename_map.json"), encoding="utf-8"))
    head, tail = shell()
    focal = load_focal()
    print(f"초점 정보 {len(focal)}장")
    index = {}

    for key, prefix, list_href, menu, parent in BOARDS:
        p = os.path.join(src, key + ".json")
        if not os.path.exists(p):
            print("  건너뜀:", key); continue
        recs = json.load(io.open(p, encoding="utf-8"))
        imap = {}
        for r in recs:
            for u in r.get("imgs", []):
                n = local_name(u, renames)
                if n:
                    imap[u] = n

        made, entries = 0, []
        for i, r in enumerate(recs):
            body = apply_focal(fix_typos(clean(r.get("html", ""), imap)), focal)
            yt = (r.get("yt") or "").strip()
            if yt:
                # 목록에서 모달로 띄우던 것을 이 페이지 안으로 옮긴다.
                # 유튜브는 재생기가 클수록 높은 화질을 고르므로, 본문 폭을 꽉 채운다.
                body = (
                    '<div class="post_video"><iframe src="https://www.youtube.com/embed/' + yt +
                    '?rel=0&modestbranding=1&vq=hd1080" title="' + html.escape(r["title"]) +
                    '" allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
                    'gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy">'
                    '</iframe></div>' + body)
            if not body:
                body = "<p>내용이 없습니다.</p>"
            title = fix_typos(r["title"]).strip()
            fname = f"{prefix}{r['seq']}.html"
            prev = (os.path.basename(f"{prefix}{recs[i-1]['seq']}.html"), fix_typos(recs[i-1]["title"])) if i > 0 else None
            nxt = (os.path.basename(f"{prefix}{recs[i+1]['seq']}.html"), fix_typos(recs[i+1]["title"])) if i < len(recs) - 1 else None
            out = page(head, tail, title=title, date=r["date"], body=body, menu=menu,
                       parent=parent, list_href=list_href, prev=prev, nxt=nxt)
            io.open(os.path.join(ROOT, fname), "w", encoding="utf-8", newline="\n").write(out)
            entries.append({"seq": r["seq"], "title": title, "date": r["date"], "href": fname})
            made += 1
        index[key] = entries
        print(f"{menu:9} {made:3d}장  -> {prefix}*.html")

    io.open(os.path.join(ROOT, "tools", "post_index.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(index, ensure_ascii=False, indent=1))
    print("목록 연결용 tools/post_index.json 기록")


if __name__ == "__main__":
    main()
