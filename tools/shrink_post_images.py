#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/img/posts 를 웹에서 쓸 크기로 줄인다.

    python tools/shrink_post_images.py

원본이 3000~3400px 짜리 10MB 파일이라 그대로 두면 저장소가 600MB 를 넘고
페이지도 못 쓴다. 긴 변 1600px, JPEG 품질 82 로 맞춘다. 투명이 필요 없는
PNG 는 JPEG 으로 바꾼다 (사진이 대부분이라 용량 차이가 크다).
바뀐 파일 이름은 rename_map.json 에 남겨 페이지 생성기가 참조한다.
"""
import io, json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "assets", "img", "posts")
MAX = 1600
Q = 82


def has_alpha(im):
    if im.mode in ("RGBA", "LA"):
        a = im.getchannel("A")
        return a.getextrema()[0] < 250
    return im.mode == "P" and "transparency" in im.info


def main():
    files = sorted(f for f in os.listdir(D) if not f.startswith("."))
    before = sum(os.path.getsize(os.path.join(D, f)) for f in files)
    renames = {}

    for f in files:
        p = os.path.join(D, f)
        try:
            im = Image.open(p)
        except Exception:
            continue
        im.load()
        w, h = im.size
        if max(w, h) > MAX:
            s = MAX / max(w, h)
            im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)

        keep_png = f.lower().endswith(".png") and has_alpha(im)
        if keep_png:
            im.save(p, "PNG", optimize=True)
        else:
            if im.mode != "RGB":
                im = im.convert("RGB")
            dst = os.path.splitext(p)[0] + ".jpg"
            im.save(dst, "JPEG", quality=Q, optimize=True, progressive=True)
            if dst != p:
                os.remove(p)
                renames[f] = os.path.basename(dst)

    files = sorted(f for f in os.listdir(D) if not f.startswith("."))
    after = sum(os.path.getsize(os.path.join(D, f)) for f in files)
    io.open(os.path.join(ROOT, "tools", "rename_map.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(renames, ensure_ascii=False, indent=1))
    print(f"{len(files)}장  {before//1024//1024}MB -> {after//1024//1024}MB "
          f"(평균 {after//len(files)//1024}KB)  png->jpg {len(renames)}건")


if __name__ == "__main__":
    main()
