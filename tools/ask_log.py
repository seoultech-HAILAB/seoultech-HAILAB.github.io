#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""도우미가 받은 질문을 꺼내 본다.

    python tools/ask_log.py            # 최근 30건
    python tools/ask_log.py --punt     # 못 답한 것만 (이메일로 넘긴 답)
    python tools/ask_log.py --top      # 무엇을 자주 묻는지
    python tools/ask_log.py -n 100     # 개수 지정

못 답한 질문(--punt)이 곧 할 일 목록이다. 그 질문의 답을 사이트에 채우거나,
사이트에 둘 수 없는 정책이면 워커의 '정책 문답' 블록에 적으면 된다.
"""
import argparse
import json
import subprocess
import sys

DB = "hai-ask-log"


def q(sql):
    r = subprocess.run(
        ["npx", "--yes", "wrangler@4", "d1", "execute", DB, "--remote", "--json", "--command", sql],
        capture_output=True, text=True, encoding="utf-8", shell=(sys.platform == "win32"))
    out = "\n".join(l for l in r.stdout.splitlines() if not l.startswith("npm notice"))
    try:
        return json.loads(out)[0]["results"]
    except Exception:
        print(r.stdout[-800:], r.stderr[-400:], sep="\n")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=30)
    ap.add_argument("--punt", action="store_true", help="못 답한 질문만")
    ap.add_argument("--top", action="store_true", help="자주 묻는 순")
    a = ap.parse_args()

    if a.top:
        rows = q("SELECT question, COUNT(*) n, SUM(punt) punts FROM ask "
                 "GROUP BY question ORDER BY n DESC LIMIT %d" % a.n)
        print("자주 묻는 질문")
        for r in rows:
            mark = "  ← 못 답함" if r["punts"] else ""
            print("  %3d회  %s%s" % (r["n"], r["question"], mark))
        return

    where = "WHERE punt = 1" if a.punt else ""
    rows = q("SELECT id, substr(at,1,16) t, question, answer, ms, punt "
             "FROM ask %s ORDER BY id DESC LIMIT %d" % (where, a.n))
    tot = q("SELECT COUNT(*) c, SUM(punt) p FROM ask")[0]
    print("전체 %s건 · 못 답한 것 %s건" % (tot["c"], tot["p"] or 0))
    print()
    for r in rows:
        print("#%-4s %s  %sms%s" % (r["id"], r["t"], r["ms"], "  [못 답함]" if r["punt"] else ""))
        print("   Q %s" % r["question"])
        print("   A %s" % (r["answer"] or "")[:160].replace("\n", " "))
        print()


if __name__ == "__main__":
    main()
