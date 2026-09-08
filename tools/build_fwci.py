#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""논문 목록의 FWCI(Field-Weighted Citation Impact)를 OpenAlex 에서 받아 하이라이트에 넣는다.

    python tools/build_fwci.py            # OpenAlex 조회 → tools/fwci_data.json → publications/index.html
    python tools/build_fwci.py --offline  # 조회 없이 저장된 fwci_data.json 으로 하이라이트만 다시 찍는다

FWCI 는 '같은 해·같은 분야·같은 종류의 논문이 받는 평균 인용' 대비 인용 비율이다. 1.0 이
세계 평균. Scopus(SciVal) 의 정의를 OpenAlex 가 자체 데이터로 계산해 공개한다 — 값은
SciVal 과 조금 다를 수 있다. 논문은 링크의 DOI 로 찾고, DOI 가 없으면 제목으로 찾아 제목이
충분히 같을 때만 쓴다. 아직 인용이 쌓이지 않은 최신 논문은 0 으로 잡히며 평균에 그대로 든다
(SciVal 도 같다). 돌린 뒤에는 build_list_pages.py → tidy_pages.py.
"""
import difflib
import html
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tools", "fwci_data.json")
MAILTO = "kwseo@seoultech.ac.kr"      # OpenAlex 의 polite pool — 연구실 대표 주소

def rd(rel): return io.open(os.path.join(ROOT, rel), encoding="utf-8", newline="").read()
def wr(rel, s): io.open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="").write(s)
def plain(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "hai-lab-site (mailto:%s)" % MAILTO})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def doi_of(link):
    m = re.search(r"10\.\d{4,9}/[^\s?#]+", link or "")
    return m.group(0).rstrip(".)") if m else ""

def pubs():
    s = rd("publications/index.html"); out = []
    for li in re.findall(r'<li class="pub".*?</li>', s, re.S):
        out.append(dict(
            title=plain(re.search(r"<h4>(.*?)</h4>", li, re.S).group(1)),
            year=re.search(r'data-year="(\d+)"', li).group(1),
            cat=re.search(r'data-cat="([^"]+)"', li).group(1),
            link=(re.search(r'class="pub_go" href="([^"]+)"', li) or [None, ""])[1]))
    return out

def lookup(p):
    """OpenAlex 에서 한 편 찾기. (fwci, cited_by, openalex_id, how) — 못 찾으면 None"""
    doi = doi_of(p["link"])
    if doi:
        try:
            w = get("https://api.openalex.org/works/https://doi.org/%s?mailto=%s" % (urllib.parse.quote(doi, safe="/"), MAILTO))
            return dict(fwci=w.get("fwci"), cited=w.get("cited_by_count", 0), id=w.get("id"), how="doi", matched=w.get("display_name"))
        except Exception:
            pass
    q = urllib.parse.quote(p["title"][:200])
    try:
        d = get("https://api.openalex.org/works?search=%s&per-page=3&mailto=%s" % (q, MAILTO))
    except Exception:
        return None
    for w in d.get("results", []):
        sim = difflib.SequenceMatcher(None, (w.get("display_name") or "").lower(), p["title"].lower()).ratio()
        if sim >= 0.85 and abs(int(w.get("publication_year") or 0) - int(p["year"])) <= 1:
            return dict(fwci=w.get("fwci"), cited=w.get("cited_by_count", 0), id=w.get("id"), how="title", matched=w.get("display_name"))
    return None

def fetch():
    rows = []
    for p in pubs():
        r = lookup(p); time.sleep(0.2)
        rows.append(dict(title=p["title"], year=p["year"], cat=p["cat"], doi=doi_of(p["link"]),
                         **(r or dict(fwci=None, cited=None, id=None, how="none", matched=None))))
        print("%-5s %-6s %s | %s" % (r["how"] if r else "none", ("%.2f" % r["fwci"]) if r and r["fwci"] is not None else "-", p["title"][:60], (r or {}).get("cited")))
    io.open(DATA, "w", encoding="utf-8", newline="\n").write(json.dumps(
        dict(source="OpenAlex (api.openalex.org)", fetched=time.strftime("%Y-%m-%d"), works=rows), ensure_ascii=False, indent=1) + "\n")
    return rows

def summarize(rows):
    vals = sorted(r["fwci"] for r in rows if r.get("fwci") is not None)
    mean = sum(vals) / len(vals) if vals else 0.0
    med = (vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2) if vals else 0.0
    return dict(n=len(rows), matched=len(vals), mean=mean, median=med, cited=sum(r.get("cited") or 0 for r in rows))

def render(summary, fetched):
    # 대표값은 평균이다 — FWCI 는 인용 비율의 평균이라는 뜻이라 이름과 숫자가 맞아야 한다.
    # 100 이 넘는 세 편이 평균을 끌어올리므로 중앙값을 작게 같이 적어 읽는 사람이 판단하게 한다.
    mean, med = summary["mean"], summary["median"]
    if mean >= 2: rel = "%.0f× the global average" % mean
    elif mean >= 1: rel = "%d%% above the global average" % round((mean - 1) * 100)
    else: rel = "%d%% below the global average" % round((1 - mean) * 100)
    tile = ('<div class="pubhi_item pubhi_item--fwci"><div class="pubhi_top"><span class="pubhi_ico"><i class="fa-solid fa-arrow-trend-up" aria-hidden="true"></i></span>'
            '<span class="pubhi_num">%.1f</span></div><p class="pubhi_lab">FWCI</p>'
            '<p class="pubhi_sub">Field-Weighted Citation Impact &mdash; mean of %d OpenAlex-indexed papers, %s (median %.1f)</p></div>'
            % (mean, summary["matched"], rel, med))
    s = rd("publications/index.html")
    # 타일만 걷어낸다 (타일은 </p></div> 로 끝난다 — 그 뒤의 </div> 는 판(grid) 을 닫는 것이라 건드리면 안 된다)
    s = re.sub(r'<div class="pubhi_item pubhi_item--fwci">.*?</p></div>', "", s, count=1, flags=re.S)
    if '<div class="pubhi_grid">' in s:
        i = s.find('<div class="pubhi_grid">'); j = s.find("</section>", i)
        grid = s[i:j]
        if grid.count("<div") - grid.count("</div>") == 1:      # 예전 실행이 판 닫는 </div> 를 삼켰으면 되살린다
            grid += "</div>"
        assert grid.endswith("</div>") and grid.count("<div") == grid.count("</div>"), "pubhi_grid 가 어긋남"
        s = s[:i] + grid[:-len("</div>")] + tile + "</div>" + s[j:]
    wr("publications/index.html", s)

def main():
    if "--offline" in sys.argv and os.path.exists(DATA):
        d = json.loads(io.open(DATA, encoding="utf-8").read()); rows, fetched = d["works"], d["fetched"]
    else:
        rows = fetch(); fetched = time.strftime("%Y-%m-%d")
    sm = summarize(rows)
    render(sm, fetched)
    print("FWCI 평균 %.2f (%d/%d 편, 인용 합계 %d) → publications/index.html" % (sm["mean"], sm["matched"], sm["n"], sm["cited"]))

if __name__ == "__main__":
    main()
