#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/search-index.json 을 만든다.

    python tools/build_search_index.py

GitHub Pages 는 정적이라 검색 서버가 없다. 페이지에서 제목·항목만 뽑아
브라우저가 훑을 수 있는 평평한 목록으로 저장한다. 홈은 다른 페이지의
내용을 그대로 다시 보여주는 자리라 색인에서 뺀다 (넣으면 결과가 홈 중복으로 덮인다).
"""
import io, os, re, json, html, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = {
    "about/index.html": ("Research Area", "About"),
    "about/lab-log.html": ("Lab log", "About"),
    "about/facility.html": ("Facility", "About"),
    "about/patents.html": ("Patent", "About"),
    "members/index.html": ("Professor", "Members"),
    "members/researcher.html": ("Researcher", "Members"),
    "members/alumni.html": ("Alumni", "Members"),
    "members/history.html": ("History", "Members"),
    "research/index.html": ("Projects", "Research"),
    "research/seminars.html": ("Seminars", "Research"),
    "research/videos.html": ("Video", "Research"),
    "publications/index.html": ("Publications", "Publications"),
    "board/index.html": ("News", "Board"),
    "board/gallery.html": ("Gallery", "Board"),
    "board/vlog.html": ("V-log", "Board"),
}

FIELDS = re.compile(
    r'<h[34][^>]*>(.*?)</h[34]>'
    r'|<span class="gal_tit">(.*?)</span>'
    r'|<span class="subject">(.*?)</span>'
    r'|<span class="mvp_tit">(.*?)</span>'
    r'|<p class="mrole">(.*?)</p>'
    r'|<p class="proj_desc">(.*?)</p>'
    r'|<li class="lrow"[^>]*>(.*?)</li>', re.S)


def load_aliases():
    """영문 이름에 한글 표기를 붙여 준다. '박보겸' 으로 쳐도 'Bogyeom Park' 이 걸리게 하는 표.
    부분 일치라 '보겸' 만 쳐도 찾는다. tools/name_aliases.json 에서 관리한다."""
    p = os.path.join(ROOT, "tools", "name_aliases.json")
    if not os.path.exists(p):
        return {}
    raw = json.loads(io.open(p, encoding="utf-8").read())
    return {k: v for k, v in raw.items() if not k.startswith("_") and v}


def clean(t):
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def main():
    aliases = load_aliases()
    recs = []
    for path, (title, section) in PAGES.items():
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            print("  건너뜀 (없음):", path)
            continue
        src = io.open(full, encoding="utf-8").read()
        m = re.search(r'<div class="sub_body">(.*?)</div>\s*</div>', src, re.S)
        body = m.group(1) if m else src
        seen = set()
        for f in FIELDS.finditer(body):
            t = clean(next(g for g in f.groups() if g is not None))
            if len(t) < 4 or len(t) > 240 or t in seen:
                continue
            seen.add(t)
            rec = {"t": t, "p": path, "s": section, "pt": title}
            # 이 조각에 등장하는 이름의 다른 표기를 숨은 검색어로 붙인다
            extra = [a for name, al in aliases.items() if name in t for a in al]
            if extra:
                rec["a"] = " ".join(extra)
            recs.append(rec)

    out = os.path.join(ROOT, "assets", "search-index.json")
    io.open(out, "w", encoding="utf-8", newline="\n").write(
        json.dumps(recs, ensure_ascii=False, separators=(",", ":")))
    print(f"색인 {len(recs)}건 -> assets/search-index.json ({os.path.getsize(out)//1024} KB)")
    for s, n in collections.Counter(r["s"] for r in recs).most_common():
        print(f"  {n:4d}  {s}")
    tagged = sum(1 for r in recs if "a" in r)
    print(f"  별칭 붙은 항목 {tagged}건 (이름 {len(aliases)}개 등록)")


if __name__ == "__main__":
    main()
