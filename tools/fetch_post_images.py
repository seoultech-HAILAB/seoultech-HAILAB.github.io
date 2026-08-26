#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""원본 사이트 게시글에 붙어 있던 이미지를 assets/img/posts/ 로 내려받는다.

    python tools/fetch_post_images.py <크롤json디렉터리>

파일 이름은 원본 URL 의 해시로 짓는다 (원본 이름이 전부 타임스탬프+UUID 라 읽을 수가 없다).
이미 받은 파일은 건너뛴다.
"""
import concurrent.futures as cf
import hashlib
import io
import json
import os
import sys
import urllib.request

BASE = "https://hai.seoultech.ac.kr"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "img", "posts")


def local_name(url):
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    ext = os.path.splitext(url.split("?")[0])[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".jpg"
    return f"p{h}{ext}"


def grab(url):
    dst = os.path.join(OUT, local_name(url))
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return ("skip", url, 0)
    full = url if url.startswith("http") else BASE + url
    try:
        req = urllib.request.Request(full, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": BASE + "/",
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        if len(data) < 200:
            return ("tiny", url, len(data))
        with open(dst, "wb") as f:
            f.write(data)
        return ("ok", url, len(data))
    except Exception as e:
        return ("fail:" + type(e).__name__, url, 0)


def main():
    src = sys.argv[1]
    urls = []
    for name in ("news", "projects", "gallery"):
        p = os.path.join(src, name + ".json")
        if not os.path.exists(p):
            continue
        for rec in json.load(io.open(p, encoding="utf-8")):
            urls += [u for u in rec.get("imgs", []) if u and not u.startswith("data:")]
    urls = list(dict.fromkeys(urls))
    os.makedirs(OUT, exist_ok=True)
    print(f"내려받을 이미지 {len(urls)}장")

    tally = {}
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for i, (st, url, n) in enumerate(ex.map(grab, urls), 1):
            key = st.split(":")[0]
            tally[key] = tally.get(key, 0) + 1
            if i % 40 == 0:
                print(f"  {i}/{len(urls)}", flush=True)
    print("결과:", tally)
    got = len([f for f in os.listdir(OUT) if not f.startswith(".")])
    print(f"assets/img/posts 안에 {got}개")


if __name__ == "__main__":
    main()
