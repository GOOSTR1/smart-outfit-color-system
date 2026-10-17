# -*- coding: utf-8 -*-
"""
color_engine.py — 色彩引擎
智能穿搭色彩系统的底层：颜色解析、色彩分类（色相家族 / 冷暖 / 明暗 / 饱和度），
以及基于色彩理论的和谐度与肤色适配评估规则。

所有函数返回「机器可读」的标签（tag），由上层负责翻译成中/泰文，
保持本模块语言无关、便于测试。
"""
from __future__ import annotations
import colorsys


# ---------------------------------------------------------------------------
# 基础颜色转换
# ---------------------------------------------------------------------------

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return '#%02X%02X%02X' % (int(r), int(g), int(b))


def hex_to_hsl(h: str) -> tuple:
    """返回 (hue 0-360, saturation 0-1, lightness 0-1)。"""
    r, g, b = hex_to_rgb(h)
    hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return hh * 360, ss, ll


def hsl_to_hex(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l, s)
    return rgb_to_hex(round(r * 255), round(g * 255), round(b * 255))


# 色相分段（度）：用于确定颜色家族
FAMILY_HUE = [
    ('红',   (0, 15)),
    ('橙',   (15, 45)),
    ('黄',   (45, 70)),
    ('黄绿', (70, 100)),
    ('绿',   (100, 150)),
    ('青',   (150, 185)),
    ('蓝',   (185, 250)),
    ('紫',   (250, 300)),
    ('粉',   (300, 345)),
    ('红',   (345, 360)),
]


def classify_color(hex_color: str) -> dict:
    """把颜色解析为结构化信息。

    返回: {hex, family, temp, lightness, saturation, h, s, l}
      family     色相家族（红/橙/黄/黄绿/绿/青/蓝/紫/粉/棕/米白/灰/黑/白）
      temp       冷暖（暖/冷/中性）
      lightness  明暗（深/中/浅）
      saturation 饱和度档（低/中/高）
    """
    h, s, l = hex_to_hsl(hex_color)

    # 中性色：极低饱和度
    if s < 0.10:
        if l < 0.16:
            family = '黑'
        elif l > 0.92:
            family = '白'
        elif l > 0.78:
            family = '米白'
        else:
            family = '灰'
        temp = '中性'
    else:
        # 棕色：橙黄段 + 中低明度 + 一定饱和度
        if 15 <= h < 45 and l < 0.45 and s > 0.25:
            family = '棕'
        else:
            family = '红'
            for fam, (lo, hi) in FAMILY_HUE:
                if lo <= h < hi:
                    family = fam
                    break

        # 深玫红/酒红归入红（粉色应偏浅）
        if family == '粉' and l < 0.55:
            family = '红'

        # 冷暖按色相家族判定
        if family in ('红', '橙', '黄', '黄绿', '棕'):
            temp = '暖'
        elif family in ('绿', '青', '蓝', '紫', '粉'):
            temp = '冷'
        else:
            temp = '中性'

    lightness = '深' if l < 0.35 else ('浅' if l > 0.70 else '中')
    saturation = '低' if s < 0.30 else ('高' if s > 0.65 else '中')

    return {
        'hex': rgb_to_hex(*hex_to_rgb(hex_color)),
        'family': family,
        'temp': temp,
        'lightness': lightness,
        'saturation': saturation,
        'h': h, 's': s, 'l': l,
    }


def hue_diff(h1: float, h2: float) -> float:
    """两色相之间的最小夹角（0-180）。"""
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


# ---------------------------------------------------------------------------
# 和谐度评估（两两比较）
# tag 取值: neutral / neutral_base / analogous / near / complementary /
#           clash / high_sat / mid
# ---------------------------------------------------------------------------

def harmony(hex1: str, hex2: str) -> dict:
    c1, c2 = classify_color(hex1), classify_color(hex2)
    t1, t2 = c1['temp'], c2['temp']

    if t1 == '中性' and t2 == '中性':
        return {'score': 90, 'tag': 'neutral'}
    if t1 == '中性' or t2 == '中性':
        return {'score': 85, 'tag': 'neutral_base'}

    d = hue_diff(c1['h'], c2['h'])
    s_hi = c1['s'] > 0.6 and c2['s'] > 0.6

    # 经典红绿撞色（传统色轮中的冲突组合，PPT 明确要求规避）
    fams = {c1['family'], c2['family']}
    if '红' in fams and (fams & {'绿', '青', '黄绿'}):
        if c1['s'] > 0.35 and c2['s'] > 0.35:
            return {'score': 22, 'tag': 'clash'}

    if d >= 140 and s_hi:
        return {'score': 25, 'tag': 'clash'}
    if d < 30:
        return {'score': 88, 'tag': 'analogous'}
    if d < 60:
        return {'score': 80, 'tag': 'near'}
    if d >= 140:
        return {'score': 60, 'tag': 'complementary'}
    if s_hi:
        return {'score': 55, 'tag': 'high_sat'}
    return {'score': 72, 'tag': 'mid'}


# ---------------------------------------------------------------------------
# 肤色适配评估
# tag 取值: neutral / good / bad
# ---------------------------------------------------------------------------

def skin_fit(hex_color: str, skin_tone: str) -> dict:
    c = classify_color(hex_color)
    t = c['temp']
    if t == '中性':
        return {'score': 80, 'tag': 'neutral'}
    if skin_tone == '冷':
        if t == '冷':
            return {'score': 92, 'tag': 'good'}
        return {'score': 45, 'tag': 'bad'}   # 暖色易让冷皮显黄
    # 暖皮
    if t == '暖':
        return {'score': 92, 'tag': 'good'}
    return {'score': 55, 'tag': 'bad'}       # 冷色可能让暖皮显苍白
