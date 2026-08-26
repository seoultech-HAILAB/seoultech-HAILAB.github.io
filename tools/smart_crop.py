#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사진을 한 가지 비율로 맞추되, 사람을 잘라먹지 않는 자리를 골라 자른다.

게시글 사진이 세로 3:4 부터 초광각 2.4:1 까지 섞여 있어 격자에 넣으면 제각각이다.
가운데를 기계적으로 자르면 세로 사진은 얼굴이 날아간다. 그래서 자를 위치를
그림에서 찾는다:

  살빛      사람이 있을 법한 자리. 얼굴과 손이 여기 걸린다.
  결(edge)  인물·글자가 있는 곳은 밝기 변화가 크고, 하늘·벽·바닥은 밋밋하다.

두 지도를 더해 세로/가로 방향의 관심도를 만들고, 목표 비율의 창을 훑어
관심도 합이 가장 큰 자리를 고른다. 세로 사진은 얼굴이 위쪽에 몰리므로
위쪽에 약간 가산점을 준다.
"""
import numpy as np
from PIL import Image, ImageOps


def _interest(im):
    """세로(행)·가로(열) 방향 관심도. 값이 클수록 '여기에 볼 것이 있다'."""
    small = im.convert("RGB").resize((160, 160), Image.BILINEAR)
    a = np.asarray(small).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    # 살빛: 붉은 기가 초록보다 뚜렷하고 너무 어둡지 않은 화소
    mx, mn = a.max(2), a.min(2)
    skin = ((r > 95) & (g > 40) & (b > 20) & (mx - mn > 15) &
            (np.abs(r - g) > 15) & (r > g) & (r > b)).astype(np.float32)

    # 결: 이웃 화소와의 밝기 차이
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    edge = np.zeros_like(lum)
    edge[1:-1, 1:-1] = (np.abs(lum[1:-1, 1:-1] - lum[:-2, 1:-1]) +
                        np.abs(lum[1:-1, 1:-1] - lum[2:, 1:-1]) +
                        np.abs(lum[1:-1, 1:-1] - lum[1:-1, :-2]) +
                        np.abs(lum[1:-1, 1:-1] - lum[1:-1, 2:]))
    edge /= (edge.max() or 1)

    m = edge + skin * 2.2          # 사람 쪽에 무게를 더 준다
    return m.sum(1), m.sum(0)      # 행별, 열별


def _window(weight, span, length, top_bias=0.0):
    """길이 span 짜리 창을 훑어 관심도 합이 가장 큰 시작점을 고른다."""
    n = len(weight)
    w = int(round(span / length * n))
    if w >= n:
        return 0.0
    cs = np.concatenate([[0.0], np.cumsum(weight)])
    sums = cs[w:] - cs[:-w]
    if top_bias:
        # 얼굴은 위쪽에 있기 마련이라 위쪽 창에 가산점
        pos = np.linspace(0, 1, len(sums))
        sums = sums * (1.0 + top_bias * (1.0 - pos))
    return float(np.argmax(sums)) / n


def smart_crop(im, ratio):
    """ratio (가로/세로) 로 잘라낸 이미지를 돌려준다."""
    im = ImageOps.exif_transpose(im)
    w, h = im.size
    cur = w / h
    if abs(cur - ratio) < 0.02:
        return im

    rows, cols = _interest(im)
    if cur > ratio:                       # 너무 넓다 -> 가로를 줄인다
        nw, nh = int(round(h * ratio)), h
        x = int(_window(cols, nw, w) * w)
        x = max(0, min(x, w - nw))
        return im.crop((x, 0, x + nw, nh))

    nw, nh = w, int(round(w / ratio))     # 너무 높다 -> 세로를 줄인다
    y = int(_window(rows, nh, h, top_bias=0.35) * h)
    y = max(0, min(y, h - nh))
    return im.crop((0, y, nw, y + nh))


def focal_point(im, ratio=4 / 3):
    """object-fit: cover 로 ratio 에 맞출 때 초점을 어디에 둘지 (x%, y%).

    원본을 잘라 없애지 않고 CSS 에 위치만 넘기기 위한 것이다. 되돌릴 수 있고,
    나중에 격자 비율을 바꿔도 파일은 그대로다."""
    im = ImageOps.exif_transpose(im)
    w, h = im.size
    cur = w / h
    if abs(cur - ratio) < 0.02:
        return 50, 50

    rows, cols = _interest(im)
    if cur > ratio:                       # 좌우가 잘린다 -> 가로 초점
        keep = h * ratio
        start = _window(cols, keep, w) * w
        slack = w - keep
        return (int(round(start / slack * 100)) if slack > 1 else 50), 50

    keep = w / ratio                      # 위아래가 잘린다 -> 세로 초점
    start = _window(rows, keep, h, top_bias=0.35) * h
    slack = h - keep
    return 50, (int(round(start / slack * 100)) if slack > 1 else 50)
