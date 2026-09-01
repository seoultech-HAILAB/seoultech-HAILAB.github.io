#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""members/history.html 을 tools/people_data.json 으로 다시 찍는다.

    python tools/build_history.py

여태 History 는 매니저 세 자리(Lab·Social·Publicity)의 인수인계 기록이었다.
연구실을 거쳐 간 스물여섯 명 중 일곱 명만 이름이 올라 있었고, 누가 학부연구원으로
들어와 석사를 하고 박사로 남았는지, 졸업하고 어디로 갔는지는 어디에도 없었다.

바꾼 뒤로는 사람이 축이다.

  1. 사람 연표 — 한 사람 한 줄, 가로는 2021년부터 지금까지.
     신분(학부·석사·박사·방문교수)이 바뀌면 막대 색이 바뀌므로, 학부로 들어와
     석사를 거쳐 박사로 남은 사람은 줄 하나에 색이 세 번 바뀐다.
     매니저 임기는 그 줄 아래 빨간 실선으로 겹쳐 둔다 — 자리를 뺏지 않으면서
     '이 사람이 이때 운영을 맡았다' 가 같은 줄에서 읽힌다.
  2. 운영 이력 — 옛 페이지의 세 자리. 지우지 않고 맨 아래로 내렸다.

한때 '해마다의 인원' 을 막대로 함께 두었는데, 열한 줄이 늘어서니 위 연표가 이미
하고 있는 이야기를 두 번째로 하면서 시끄럽기만 했다 — 걷어냈다.

날짜의 출처와 추정 규칙은 tools/people_data.json 머리말에 적어 두었다.
추정으로 채운 구간은 점선으로 그린다 — 사람의 이력이라 확인된 것과 계산한 것이
같은 모양이면 안 된다.
"""
import html
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROLE = {                       # 갈래: 이름표, 막대 색 이름
    "faculty":  "Faculty",
    "phd":      "Ph.D.",
    "ms":       "M.S.",
    "ug":       "Undergrad",
}
ROLE_ORDER = ["faculty", "phd", "ms", "ug"]


def e(t):
    return html.escape(str(t or ""), quote=True)


def pct(x):
    return ("%.4f" % x).rstrip("0").rstrip(".")


def yf(v):
    """'2024.07' -> 2024.5 (연을 실수로 본다).

    이미 실수로 계산해 둔 값은 그대로 돌려준다 — 여기서 str() 로 다시 읽으면
    2025.6666… 의 소수 자리를 '달' 로 보아 값이 폭주한다. 그 탓에 x() 가 100 에
    붙어 졸업한 사람의 막대까지 오른쪽 끝까지 늘어나 있었다."""
    if isinstance(v, float):
        return v
    t = str(v)
    if "." in t:
        y, m = t.split(".")
        return int(y) + (int(m) - 1) / 12.0
    return float(t)


class Axis(object):
    """가로축은 달 단위다. 같은 2021년이어도 교수님은 5월, 박보겸은 7월,
    김유원은 9월에 들어왔다 — 연도까지만 그리면 그 차이가 사라진다.
    눈금과 띠만 해 경계에 맞춘다."""

    def __init__(self, span):
        self.a, self.b = yf(span["from"]), yf(span["to"])
        self.y0 = int(span["from"][:4])
        self.now = span["now"]
        # 축은 '지금' 뒤로 조금 더 뻗어 있다 (지금 표시가 오른쪽 끝에 붙지 않게).
        # 해 이름표와 띠는 지금이 든 해까지만 그린다 — 아직 오지 않은 해에
        # 이름표를 달면 그 해도 다 지난 것처럼 보인다.
        self.y1 = int(str(self.now)[:4])
        self.total = self.b - self.a

    def x(self, v):
        return max(0.0, min(100.0, (yf(v) - self.a) / self.total * 100))

    def year_band(self, y):
        """그 해 칸의 [왼쪽, 폭] — 축 밖으로 나가는 부분은 잘라 낸다."""
        x0, x1 = self.x("%d.01" % y), self.x("%d.01" % (y + 1))
        return x0, x1 - x0

    def label_at(self, y):
        """해 이름표 자리. 마지막 해는 '지금' 까지만 그려져 있으므로 그 안의
        한가운데에 둔다 — 칸 한가운데에 두면 아직 오지 않은 달 위에 뜬다."""
        x0, w = self.year_band(y)
        end = min(x0 + w, self.x(yf(self.now) + 1 / 12.0))
        return (x0 + max(end, x0 + 4)) / 2


def bar(ax, sp, join=(False, False), program=None):
    """한 신분 구간의 막대. to 는 '그 신분이었던 마지막 달' 이므로 그 달 끝까지
    (다음 달 1일까지) 채운다 — 2025.02 졸업이면 2월이 다 칠해져야 한다."""
    x0 = ax.x(sp["from"])
    # 지금도 있는 사람은 '지금' 에서 멈춘다 — 축 끝까지 늘이면 앞일까지 아는 것처럼 보인다
    x1 = ax.x(yf(ax.now if sp.get("to") is None else sp["to"]) + 1 / 12.0)

    cls = ["ptl_bar", "is-" + sp["role"]]
    # 앞뒤 구간과 날짜가 맞닿으면 그쪽 모서리를 펴서 한 줄로 이어 붙인다.
    # 석박통합처럼 한 과정인데 막대가 둘로 끊겨 보이던 것이 이어진다.
    if join[0]:
        cls.append("is-joinl")
    if join[1]:
        cls.append("is-joinr")
    if sp.get("est"):
        cls.append("is-est")
    if sp.get("to") is None:
        cls.append("is-now")

    tip = "%s · %s ~ %s%s%s" % (ROLE[sp["role"]], sp["from"], sp.get("to") or "",
                                " · " + program if program else "",
                                " (추정)" if sp.get("est") else "")
    text = ROLE[sp["role"]] if (x1 - x0) >= 9 else ""
    return ('<b class="%s" style="left:%s%%;width:%s%%" title="%s">%s</b>'
            % (" ".join(cls), pct(x0), pct(max(x1 - x0, 1.1)), e(tip), e(text)))


def term(ax, r):
    """매니저 임기 — 막대 아래에 겹쳐 긋는 실선."""
    x0 = ax.x(r["from"])
    x1 = ax.x(yf(r.get("to") or ax.now) + 1 / 12.0)
    tip = "%s · %s ~ %s" % (r["title"], r["from"], r.get("to") or "")
    return ('<em class="ptl_term" style="left:%s%%;width:%s%%" title="%s"></em>'
            % (pct(x0), pct(max(x1 - x0, 1.1)), e(tip)))


def spans_text(p):
    """좁은 화면용 — 같은 내용을 한 줄 글로. 시간축은 여기서 못 읽는다."""
    out = []
    for sp in p["spans"]:
        to = "현재" if sp.get("to") is None else sp["to"]
        out.append("%s %s~%s%s" % (ROLE[sp["role"]], sp["from"], to,
                                   " (추정)" if sp.get("est") else ""))
    if p.get("program"):
        out.append(p["program"])
    if p.get("grad"):
        out.append("석사 졸업 %s" % p["grad"])
    for r in p.get("roles", []):
        out.append("%s %s~%s" % (r["title"], r["from"], r.get("to") or "현재"))
    return " · ".join(out)


def row(ax, p):
    photo = ('<img src="../assets/img/%s" alt="%s" loading="lazy">' % (e(p["photo"]), e(p["name"]))
             if p.get("photo") else '<span class="ptl_noimg" aria-hidden="true"></span>')
    # 한글 이름은 싣지 않는다 — 이름 칸이 두 줄이 되면 스무 줄에서 세로가 그만큼
    # 길어지고, 영문 이름이 잘리지 않을 만큼 칸을 넓히면 시간축이 좁아진다.
    # (한글 이름은 people_data.json 에 그대로 두어 검색·대조에 쓴다.)
    who = '<span class="ptl_nm"><b>%s</b></span>' % e(p["name"])
    # 앞 구간이 바로 지난 달에 끝났으면 붙은 것으로 본다
    sp_all = p["spans"]

    def touches(a, b):
        return a.get("to") and yf(b["from"]) - yf(a["to"]) < 1.5 / 12

    bars = "".join(
        bar(ax, sp,
            (i > 0 and touches(sp_all[i - 1], sp),
             i + 1 < len(sp_all) and touches(sp, sp_all[i + 1])),
            p.get("program"))
        for i, sp in enumerate(sp_all))
    terms = "".join(term(ax, r) for r in p.get("roles", []))
    here = p["spans"][-1].get("to") is None
    # 이 칸이 답하는 질문은 '그래서 지금 어디에' 다. 나간 사람은 간 곳을 적고,
    # 있는 사람은 여기 있다고 적는다 — '재직 중' 은 학생에게 쓰는 말이 아니다.
    if not here:
        nxt = e(p.get("exit") or "기록 없음")
    elif p["spans"][-1]["role"] == "faculty":
        nxt = '<span class="is-here">Lab Director</span>'
    else:
        nxt = '<span class="is-here">현재 구성원</span>'
    lead = " is-lead" if p["spans"][0]["role"] == "faculty" else ""
    return ('<li class="ptl_row%s%s">'
            '<div class="ptl_who">%s%s</div>'
            '<div class="ptl_track">%s%s</div>'
            '<p class="ptl_txt">%s</p>'
            '<p class="ptl_next">%s</p>'
            "</li>"
            % (" is-here" if here else "", lead, photo, who,
               bars, terms, e(spans_text(p)), nxt))


def legend(people):
    """실제로 쓰인 갈래만 — 아무도 없는 색을 범례에 두면 무엇을 찾으라는 말이 된다."""
    used = set(sp["role"] for p in people for sp in p["spans"])
    keys = "".join('<span class="lg"><i class="is-%s"></i>%s</span>' % (k, ROLE[k])
                   for k in ROLE_ORDER if k in used)
    # 추정 칸은 실제로 추정이 남아 있을 때만 낸다 — 지금은 스물아홉 구간이 모두
    # 확인되어 점선이 한 줄도 없다. 없는 것을 범례에 두면 무엇을 찾으라는 말이 된다.
    if any(sp.get("est") for p in people for sp in p["spans"]):
        keys += '<span class="lg"><i class="is-est"></i>추정 구간</span>'
    return ('<p class="ptl_legend">%s'
            '<span class="lg"><i class="is-term"></i>Manager</span></p>' % keys)


def managers(people):
    """옛 페이지의 세 자리. 사람 연표 아래에 요약으로 남긴다."""
    seats = {}
    for p in people:
        for r in p.get("roles", []):
            seats.setdefault(r["title"], []).append((r, p))
    out = []
    for title in ("Lab Manager", "Social Manager", "Publicity Manager"):
        if title not in seats:
            continue
        items = sorted(seats[title], key=lambda x: x[0]["from"], reverse=True)
        li = "".join(
            '<li class="mgr%s"><b>%s</b><time>%s ~ %s</time></li>'
            % (" is-now" if r.get("to") is None else "", e(p["name"]),
               e(r["from"]), e(r.get("to") or "Present"))
            for r, p in items)
        out.append('<div class="mgr_seat"><h4>%s</h4><ul>%s</ul></div>' % (e(title), li))
    return '<div class="mgr_seats">%s</div>' % "".join(out)


def main():
    data = json.loads(io.open(os.path.join(ROOT, "tools", "people_data.json"),
                              encoding="utf-8").read())
    people = data["people"]
    # 교수님은 언제 시작했든 맨 위다 — 학생 이력과 나란히 시간순으로 섞이면
    # 연구실의 축이 누구인지가 흐려진다. 나머지는 들어온 순서.
    # 같은 달에 시작한 사람끼리는 신분이 위인 쪽을 먼저 (이동엽 석사 · 유다나 학부가
    # 둘 다 2023.03 이라 이름순으로 갈렸었다) — 이름순은 마지막 갈림길로만 둔다.
    rank = dict((k, i) for i, k in enumerate(ROLE_ORDER))
    people.sort(key=lambda p: (0 if p["spans"][0]["role"] == "faculty" else 1,
                               yf(p["spans"][0]["from"]),
                               rank[p["spans"][0]["role"]], p["name"]))
    ax = Axis(data["span"])
    y0, y1 = ax.y0, ax.y1

    # 해 경계선은 막대 '위' 에 긋는다. 뒤에 두었더니 한 해를 통째로 채운 막대가
    # 선을 덮어, 그 막대가 12월에 끝난 것인지 이듬해 1월까지 간 것인지 알 수 없었다.
    # 흰 선과 어두운 선을 나란히 두어 옅은 막대에서도 짙은 막대에서도 보이게 한다.
    # 해 경계선은 막대 '위' 에 긋는다. 뒤에 두었더니 한 해를 통째로 채운 막대가
    # 선을 덮어, 그 막대가 어디서 끝났는지 알 수 없었다.
    # 해 경계선은 막대 '위' 에 긋는다. 뒤에 두었더니 한 해를 통째로 채운 막대가
    # 선을 덮어, 그 막대가 어디서 끝났는지 알 수 없었다.
    ticks = "".join('<i style="left:%s%%"></i>' % pct(ax.x("%d.01" % y))
                    for y in range(y0 + 1, y1 + 1))
    # 해마다 옅은 띠를 번갈아 깔아 '지금 보는 칸이 몇 년인지' 가 눈으로 짚이게 한다
    bands = "".join('<i style="left:%s%%;width:%s%%"></i>'
                    % (pct(ax.year_band(y)[0]), pct(ax.year_band(y)[1]))
                    for y in range(y0, y1 + 1) if (y - y0) % 2 == 1)
    # 이름표는 그 해 칸의 한가운데. 이름표 줄만 오른쪽 여백이 없어 폭이 달랐던 탓에
    # 어떤 해는 칸 가운데, 어떤 해는 선 위에 놓여 들쭉날쭉해 보였다 (CSS 에서 고침).
    years = "".join('<span%s style="left:%s%%">%s</span>'
                    % (' class="is-now"' if y == y1 else "",
                       pct(ax.label_at(y)), ax.now if y == y1 else y)
                    for y in range(y0, y1 + 1))
    # '지금' 자리. 이 연표가 언제까지를 그린 것인지 화면 안에서 읽히게 한다 —
    # 페이지만 보고는 '현재 구성원' 이 언제 기준인지 알 수 없었다.
    nx = pct(ax.x(yf(ax.now) + 1 / 12.0))
    ticks += '<i class="is-now" style="left:%s%%"></i>' % nx

    rows = "".join(row(ax, p) for p in people)
    # 눈금은 줄마다 다시 그리지 않고 판 하나에 깔아 뒤에 둔다
    body = (
        '<section class="sec"><h3 class="sec_tit">'
        '<i class="subBullet" aria-hidden="true">›</i>Lab Timeline '
        '<span class="n">%d</span></h3>'
        '%s'
        '<div class="ptl"><div class="ptl_years">%s</div>'
        '<div class="ptl_bands" aria-hidden="true">%s</div>'
        '<ul class="ptl_rows">%s</ul>'
        '<div class="ptl_lines" aria-hidden="true">%s</div></div></section>'
        '<section class="sec"><h3 class="sec_tit">'
        '<i class="subBullet" aria-hidden="true">›</i>Operations</h3>'
        '%s</section>'
        % (len(people), legend(people), years, bands, rows, ticks,
           managers(people)))

    p = os.path.join(ROOT, "members", "history.html")
    s = io.open(p, encoding="utf-8").read()
    s, n = re.subn(r'(<div class="sub_body">).*?(\n      </div>)',
                   lambda m: m.group(1) + body + m.group(2), s, flags=re.S)
    assert n == 1, "sub_body 를 찾지 못했다"

    now = sum(1 for x in people if x["spans"][-1].get("to") is None)
    desc = ("2021년 개설 이후 연구실을 거쳐 간 %d명(재직 %d명)의 학부연구원·석사·박사 "
            "재직 이력과 졸업 후 진로. 서울과학기술대학교 인간중심 인공지능 연구실"
            "(HAI Lab) History." % (len(people), now))
    s = re.sub(r'<meta name="description" content="[^"]*">',
               '<meta name="description" content="%s">' % desc, s)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)

    # 석사는 2년보다 짧을 수 없다. 학적 입학보다 먼저 연구실에 들어왔으면 길게
    # 나오는데 그건 맞는 값이다 — 짧게 나오면 합류일이 잘못 적힌 것이다.
    def mon(t):
        y, m = str(t).split(".")
        return int(y) * 12 + int(m)
    odd = [(x["name"], sp) for x in people for sp in x["spans"]
           if sp["role"] == "ms" and sp.get("to")
           and mon(sp["to"]) - mon(sp["from"]) + 1 < 24]

    print("사람 %d명 (재직 %d) -> members/history.html" % (len(people), now))
    if odd:
        print("  석사가 2년이 안 된다 — 합류일을 확인할 것:")
        for nm, sp in odd:
            print("    %-16s %s ~ %s (%d개월)"
                  % (nm, sp["from"], sp["to"], mon(sp["to"]) - mon(sp["from"]) + 1))
    est = sum(1 for x in people for sp in x["spans"] if sp.get("est"))
    print("  구간 %d개 중 추정 %d개" % (sum(len(x["spans"]) for x in people), est))


if __name__ == "__main__":
    main()
