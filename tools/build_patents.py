#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""about/patents.html 의 특허 목록을 tools/patents_data.json 으로 다시 찍는다.

    python tools/build_patents.py

원본 사이트에서 옮겨 온 뒤 손대지 않아, 그 사이 등록으로 바뀐 건과 잘못 붙은 번호가
섞여 있었다. KIPRIS 원부로 대조한 값을 json 한 곳에 두고 여기서 페이지를 만든다.
번호가 또 바뀌면 json 만 고치고 이 스크립트를 돌리면 된다.

연도는 '그 건의 가장 최근 사건' 기준이다 — 등록됐으면 등록연도, 아니면 출원연도.
(예전에는 어떤 건은 등록연도로, 어떤 건은 출원연도로 섞여 있었다.)
"""
import html
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LABEL = {
    "registered": "등록특허",
    "pending": "출원·공개",
    "filed": "출원",
}


def e(t):
    return html.escape(str(t or ""), quote=True)


def numbers(p):
    """그 건을 가리키는 번호 하나만 적는다.

    등록된 특허는 등록번호가 최종 번호다. 출원번호·공개번호까지 나란히 붙이면
    한 건에 번호가 셋이라 무엇을 보아야 하는지 흐려진다 (원부는 json 에 남겨 둔다).
    예전에는 '출원번호 + 등록일' 처럼 짝이 어긋난 줄도 있었다."""
    if p["status"] == "registered" and p.get("reg_no"):
        return ["등록번호 %s (등록일 %s)" % (e(p["reg_no"]), e(p["reg_on"]))]
    if p.get("filed_no"):
        return ["출원번호 %s (출원일 %s)" % (e(p["filed_no"]), e(p["filed_on"]))]
    return []


def item(p, no):
    """News 목록과 같은 짜임 — [번호][특허명][연도].
    번호는 가장 오래된 것이 1번이라 새 특허가 늘어도 아래가 밀리지 않는다."""
    nums = "".join('<span class="pnum">%s</span>' % x for x in numbers(p))
    note = '<p class="pnote">%s</p>' % e(p["note"]) if p.get("note") else ""
    cls = "tag on" if p["status"] == "registered" else "tag"
    return (
        '<li class="pat" data-year="%s"><span class="pno">%d</span><div>'
        "<h4>%s</h4>"
        '<p class="inv">%s</p>'
        '<p class="meta"><span class="%s">%s</span>%s</p>'
        '<p class="assignee">%s</p>%s'
        '</div><span class="pat_y">%s</span></li>'
        % (e(p["year"]), no, e(p["title"]), e(p["inventors"]),
           cls, LABEL[p["status"]], nums, e(p["assignee"]), note, e(p["year"]))
    )


def main():
    data = json.loads(io.open(os.path.join(ROOT, "tools", "patents_data.json"),
                              encoding="utf-8").read())
    pats = data["patents"]
    # 최신 사건부터. 같은 해면 등록 > 출원·공개 > 출원 순으로.
    rank = {"registered": 0, "pending": 1, "filed": 2}
    pats.sort(key=lambda p: (p["year"], -rank[p["status"]],
                             p.get("reg_on") or p.get("filed_on") or ""), reverse=True)

    p = os.path.join(ROOT, "about", "patents.html")
    s = io.open(p, encoding="utf-8").read()

    body = "".join(item(x, len(pats) - i) for i, x in enumerate(pats))
    s = re.sub(r'(<ol class="patlist"[^>]*>).*?(</ol>)',
               lambda m: m.group(1) + body + m.group(2), s, flags=re.S)

    # 연도 버튼을 실제 목록에 맞춘다
    years = sorted({x["year"] for x in pats}, reverse=True)
    btns = ('<button class="fbtn is-on" data-val="all">전체</button>'
            + "".join('<button class="fbtn" data-val="%s">%s</button>' % (y, y) for y in years))
    s = re.sub(r'(<div class="filterbar" data-axis="year"[^>]*><span class="fcap">연도</span>)'
               r'.*?(<span class="fcount"[^>]*></span></div>)',
               lambda m: m.group(1) + btns + m.group(2), s, flags=re.S)

    n_reg = sum(1 for x in pats if x["status"] == "registered")
    # 검색 결과에 그대로 뜨는 문장이다. '특허 14건' 만으로는 무엇에 대한 특허인지
    # 알 수 없어 아무도 누르지 않는다. 최근 세 건의 주제를 앞에 세운다.
    def gist(t):
        """제목을 낱말 경계에서 끊는다 — 글자 수로 자르면 '시선 추적 데이' 처럼 남는다."""
        t = t.split("(")[0].strip()
        if len(t) <= 24:
            return t
        cut = t[:24].rsplit(" ", 1)[0]
        return cut if len(cut) >= 10 else t[:24]

    topics = " · ".join(gist(x["title"]) for x in pats[:3])
    desc = ("%s 등 서울과학기술대학교 인간중심 인공지능 연구실(HAI Lab)의 "
            "특허 %d건(등록 %d건) 목록." % (topics, len(pats), n_reg))
    s = re.sub(r'<meta name="description" content="[^"]*">',
               '<meta name="description" content="%s">' % desc, s)

    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("특허 %d건 (등록 %d · 출원 %d) -> about/patents.html"
          % (len(pats), n_reg, len(pats) - n_reg))
    for x in pats:
        print("  %s  %-10s %s" % (x["year"], LABEL[x["status"]], x["title"][:44]))


if __name__ == "__main__":
    main()
