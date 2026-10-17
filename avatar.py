# -*- coding: utf-8 -*-
"""
avatar.py — 人体模型与穿衣可视化
根据身材（体型/BMI/身高）生成参数化的人体 SVG，并把一套穿搭的颜色
绘制到对应部位（上装=躯干+袖子，外套=开襟，裙/裤=下半身，鞋=脚，配饰=项链）。
"""
from body_engine import calc_bmi, bmi_category, height_category

SKIN = '#F0C8A0'
HAIR = {'深': '#2E2620', '浅': '#9A7B4F'}

# 各体型在肩/胸/腰/臀的横向半宽（px，正常 BMI 下）
SHAPE_W = {
    'H型':     {'shoulder': 42, 'bust': 40, 'waist': 38, 'hip': 41},
    '苹果型':  {'shoulder': 40, 'bust': 41, 'waist': 45, 'hip': 39},
    '梨型':    {'shoulder': 38, 'bust': 37, 'waist': 33, 'hip': 46},
    '沙漏型':  {'shoulder': 43, 'bust': 41, 'waist': 30, 'hip': 43},
    '倒三角型': {'shoulder': 49, 'bust': 42, 'waist': 36, 'hip': 37},
}

# BMI 档位 → 整体宽度缩放
BMI_SCALE = {'偏瘦': 0.86, '正常': 1.00, '偏胖': 1.16, '肥胖': 1.32}

# 身高档位 → 脚踝高度（越高腿越长）
ANKLE = {'娇小': 348, '中等': 378, '高挑': 406}


def _widths(profile):
    shape = profile.get('body_shape', 'H型')
    bcat = bmi_category(calc_bmi(profile.get('height', 165), profile.get('weight', 55)))
    s = BMI_SCALE.get(bcat, 1.0)
    sh = SHAPE_W.get(shape, SHAPE_W['H型'])
    return {
        'shoulder': sh['shoulder'] * s,
        'bust': sh['bust'] * s,
        'waist': sh['waist'] * s,
        'hip': sh['hip'] * s,
        'ankle': ANKLE[height_category(profile.get('height', 165))],
    }


def _torso_path(w):
    sl, bst, wst, hp = w['shoulder'], w['bust'], w['waist'], w['hip']
    return (f'M {100-sl} 84 '
            f'L {100-bst} 124 '
            f'Q {100-wst-3} 150 {100-wst} 172 '
            f'L {100-hp} 234 '
            f'L {100+hp} 234 '
            f'Q {100+wst+3} 150 {100+wst} 172 '
            f'L {100+bst} 124 '
            f'L {100+sl} 84 Z')


def _jacket_paths(w, color):
    sl, bst, wst, hp = w['shoulder'], w['bust'], w['waist'], w['hip']
    left = (f'M {100-sl} 84 L {100-bst} 124 Q {100-wst-3} 150 {100-wst} 172 '
            f'L {100-hp} 234 L {100-7} 234 L {100-7} 84 Z')
    right = (f'M {100+sl} 84 L {100+bst} 124 Q {100+wst+3} 150 {100+wst} 172 '
             f'L {100+hp} 234 L {100+7} 234 L {100+7} 84 Z')
    return (f'<path d="{left}" fill="{color}"/>'
            f'<path d="{right}" fill="{color}"/>')


def render_avatar(profile, items, width=180, height=387):
    """生成一张穿衣人体模型 SVG。items 为含 category/hex 的单品列表。"""
    hair = HAIR.get(profile.get('hair', '深'), HAIR['深'])
    wd = _widths(profile)
    sl, bst, wst, hp = wd['shoulder'], wd['bust'], wd['waist'], wd['hip']
    ankle = wd['ankle']

    # 解析服装颜色（未指定时用中性默认）
    cols = {'上衣': '#C9CDD1', '裙装': None, '下装': '#5A6B7A',
            '外套': None, '鞋': '#3A3A3A', '配饰': None}
    for it in items:
        cat = it.get('category')
        if cat in cols and cols[cat] is None:
            cols[cat] = it.get('hex')

    top = cols['上衣']
    outer = cols['外套']
    shoes = cols['鞋']
    accent = cols['配饰']
    sleeve = outer if outer else top
    is_skirt = cols['裙装'] is not None
    bottom = cols['裙装'] if is_skirt else cols['下装']

    p = []
    # 脖子、头、头发
    p.append(f'<rect x="92" y="58" width="16" height="30" fill="{SKIN}"/>')
    p.append(f'<circle cx="100" cy="42" r="27" fill="{SKIN}"/>')
    p.append(f'<path d="M 71 42 A 29 29 0 0 1 129 42 Z" fill="{hair}"/>')

    # 手臂（袖子）+ 手
    p.append(f'<rect x="{100-sl-12}" y="88" width="15" height="117" rx="7" fill="{sleeve}"/>')
    p.append(f'<rect x="{100+sl-3}" y="88" width="15" height="117" rx="7" fill="{sleeve}"/>')
    p.append(f'<circle cx="{100-sl-4.5}" cy="209" r="6" fill="{SKIN}"/>')
    p.append(f'<circle cx="{100+sl+4.5}" cy="209" r="6" fill="{SKIN}"/>')

    # 躯干（上装）
    p.append(f'<path d="{_torso_path(wd)}" fill="{top}"/>')

    # 外套（开襟）
    if outer:
        p.append(_jacket_paths(wd, outer))

    # 下半身：裙装 / 裤装
    if is_skirt:
        hem = max(hp, wst) * 1.55
        hem_y = min(ankle - 92, 288)
        p.append(f'<path d="M {100-wst} 170 L {100-hem} {hem_y} L {100+hem} {hem_y} '
                 f'L {100+wst} 170 Z" fill="{bottom}"/>')
        leg_w = hp * 0.5 - 6
        p.append(f'<rect x="{100-hp*0.5}" y="{hem_y}" width="{leg_w}" height="{ankle-hem_y-8}" rx="9" fill="{SKIN}"/>')
        p.append(f'<rect x="{100+6}" y="{hem_y}" width="{leg_w}" height="{ankle-hem_y-8}" rx="9" fill="{SKIN}"/>')
    else:
        leg_w = hp * 0.52
        p.append(f'<rect x="{100-leg_w-5}" y="232" width="{leg_w}" height="{ankle-240}" rx="11" fill="{bottom}"/>')
        p.append(f'<rect x="{100+5}" y="232" width="{leg_w}" height="{ankle-240}" rx="11" fill="{bottom}"/>')

    # 鞋
    p.append(f'<ellipse cx="{100-hp*0.4}" cy="{ankle+2}" rx="16" ry="7" fill="{shoes}"/>')
    p.append(f'<ellipse cx="{100+hp*0.4}" cy="{ankle+2}" rx="16" ry="7" fill="{shoes}"/>')

    # 配饰（项链）
    if accent:
        p.append(f'<path d="M 88 76 Q 100 90 112 76" fill="none" stroke="{accent}" stroke-width="3"/>')
        p.append(f'<circle cx="100" cy="86" r="3.5" fill="{accent}"/>')

    svg = (f'<svg viewBox="0 0 200 430" width="{width}" height="{height}" '
           f'xmlns="http://www.w3.org/2000/svg">' + ''.join(p) + '</svg>')
    return svg
