# -*- coding: utf-8 -*-
"""
recommender.py — 推荐引擎（对应论文「智能核心层」）
将色彩和谐度、肤色适配、天气/场合/季节/风格适配与配色避坑规则
融合为一个可解释的评分，生成 2~3 套穿搭方案并附带推荐理由。
"""
from __future__ import annotations

from color_engine import classify_color, harmony, skin_fit
from i18n import FAMILY
from body_engine import calc_bmi, bmi_category


# ---------------------------------------------------------------------------
# 条件配置：偏好饱和度/明度/色相段 + 双语说明
# hue 为 (lo, hi) 色相段列表；空列表表示「无特定色相偏好」（中性色最安全）
# ---------------------------------------------------------------------------

WEATHER = {
    '晴天': {'sat': '中', 'light': '中', 'hue': [],
             'note': {'zh': '晴天明亮，配色饱和度适中、清爽明快',
                      'th': 'แดดออก สีอิ่มตัวปานกลาง ดูสดใส'}},
    '阴天': {'sat': '中', 'light': '浅', 'hue': [],
             'note': {'zh': '阴天提亮浅色系，点亮心情',
                      'th': 'วันครึ้ม เลือกสีอ่อนช่วยเพิ่มความสดใส'}},
    '雨天': {'sat': '低', 'light': '深', 'hue': [],
             'note': {'zh': '雨天沉稳配色，耐脏实用',
                      'th': 'วันฝนตก โทนสีเข้มทนทานต่อการใช้งาน'}},
    '高温': {'sat': '低', 'light': '浅', 'hue': [],
             'note': {'zh': '高温选浅色系反光降温，清凉舒适',
                      'th': 'อากาศร้อน สีอ่อนสะท้อนแสงช่วยให้เย็นสบาย'}},
    '低温': {'sat': '中', 'light': '深', 'hue': [],
             'note': {'zh': '低温以深色系为主，保暖又稳重',
                      'th': 'อากาศหนาว โทนสีเข้มให้ความอบอุ่นและน่าเชื่อถือ'}},
}

OCCASION = {
    '通勤上班': {'sat': '低', 'light': '中', 'hue': [],
                 'note': {'zh': '通勤低饱和沉稳配色，专业得体',
                          'th': 'ทำงาน โทนสีอิ่มตัวต่ำ สุภาพเป็นมืออาชีพ'}},
    '商务会议': {'sat': '低', 'light': '深', 'hue': [],
                 'note': {'zh': '商务低饱和 + 深色系，彰显专业与信赖',
                          'th': 'ประชุมธุรกิจ สีอิ่มตัวต่ำและเข้ม ดูน่าเชื่อถือ'}},
    '约会': {'sat': '中', 'light': '中', 'hue': [(300, 360), (0, 40)],
             'note': {'zh': '约会适度提升饱和度，增添活力与亲和',
                      'th': 'เดท เพิ่มความสดใสให้ดูมีชีวิตชีวา'}},
    '聚会派对': {'sat': '高', 'light': '中', 'hue': [],
                 'note': {'zh': '聚会高饱和亮色，尽情释放活力',
                          'th': 'ปาร์ตี้ สีสดใส ปลดปล่อยความสนุก'}},
    '宴会正式': {'sat': '低', 'light': '深', 'hue': [(210, 250), (0, 20), (330, 360)],
                 'note': {'zh': '宴会经典深色系（黑/藏蓝/酒红），得体出众',
                          'th': 'งานทางการ โทนคลาสสิก (ดำ/กรมท่า/ไวน์) ดูสง่างาม'}},
    '休闲日常': {'sat': '中', 'light': '中', 'hue': [],
                 'note': {'zh': '休闲舒适自然，配色自由灵活',
                          'th': 'ลำลอง ใส่สบาย เลือกสีได้อิสระ'}},
}

SEASON = {
    '春': {'sat': '低', 'light': '浅', 'hue': [(330, 360), (0, 60), (150, 210)],
           'note': {'zh': '春日浅柔马卡龙色系，温柔清新',
                    'th': 'ฤดูใบไม้ผลิ โทนพาสเทลนุ่มนวลสดชื่น'}},
    '夏': {'sat': '高', 'light': '浅', 'hue': [(180, 230), (45, 75), (0, 30), (120, 165)],
           'note': {'zh': '夏季鲜亮活力色调，明快清爽',
                    'th': 'ฤดูร้อน สีสดใสมีชีวิตชีวา'}},
    '秋': {'sat': '中', 'light': '中', 'hue': [(15, 50), (340, 360), (40, 80), (90, 120)],
           'note': {'zh': '秋季暖棕与大地色系，温暖稳重',
                    'th': 'ฤดูใบไม้ร่วง โทนน้ำตาลอุ่นและสีเอิร์ธโทน'}},
    '冬': {'sat': '低', 'light': '深', 'hue': [(210, 250), (0, 15), (330, 360), (120, 150)],
           'note': {'zh': '冬季厚重沉稳的深色，高级耐看',
                    'th': 'ฤดูหนาว โทนสีเข้มให้ความรู้สึกมั่นคง'}},
}

STYLE = {
    '极简': {'sat': '低', 'light': '中', 'hue': [],
             'note': {'zh': '极简偏好低饱和莫兰迪 + 中性色',
                      'th': 'มินิมอล โทนสีอิ่มตัวต่ำและสีกลาง'}},
    '复古': {'sat': '中', 'light': '中', 'hue': [(15, 50), (340, 360), (40, 80), (90, 120)],
             'note': {'zh': '复古适配浓郁大地色与酒红',
                      'th': 'วินเทจ โทนเอิร์ธเข้มและสีไวน์'}},
    '韩系': {'sat': '低', 'light': '浅', 'hue': [(300, 360), (0, 60), (150, 210)],
             'note': {'zh': '韩系柔和低饱和浅色系，温柔减龄',
                      'th': 'สไตล์เกาหลี โทนอ่อนนุ่มนวล'}},
    '休闲': {'sat': '中', 'light': '中', 'hue': [(180, 240), (0, 60), (90, 120)],
             'note': {'zh': '休闲明亮舒适，随性自然',
                      'th': 'ลำลอง สดใส ใส่สบาย'}},
    '优雅': {'sat': '低', 'light': '中', 'hue': [(210, 250), (0, 20), (330, 360)],
             'note': {'zh': '优雅经典低饱和，高级有质感',
                      'th': 'หรู โทนคลาสสิกอิ่มตัวต่ำ'}},
    '通勤': {'sat': '低', 'light': '中', 'hue': [(210, 250)],
             'note': {'zh': '通勤干练中性色，利落大方',
                      'th': 'ทำงาน โทนสีกลาง กระฉับกระเฉง'}},
}

WEATHER_OPTIONS = list(WEATHER.keys())
OCCASION_OPTIONS = list(OCCASION.keys())
SEASON_OPTIONS = list(SEASON.keys())
STYLE_OPTIONS = list(STYLE.keys())

_OPTION_LABEL = {
    'weather': {
        '晴天': {'zh': '晴天', 'th': 'แดดออก'}, '阴天': {'zh': '阴天', 'th': 'ครึ้ม'},
        '雨天': {'zh': '雨天', 'th': 'ฝนตก'}, '高温': {'zh': '高温', 'th': 'ร้อน'},
        '低温': {'zh': '低温', 'th': 'หนาว'},
    },
    'occasion': {
        '通勤上班': {'zh': '通勤上班', 'th': 'ไปทำงาน'},
        '商务会议': {'zh': '商务会议', 'th': 'ประชุมธุรกิจ'},
        '约会': {'zh': '约会', 'th': 'นัดเดท'},
        '聚会派对': {'zh': '聚会派对', 'th': 'งานสังสรรค์'},
        '宴会正式': {'zh': '宴会正式', 'th': 'งานทางการ'},
        '休闲日常': {'zh': '休闲日常', 'th': 'ลำลองทุกวัน'},
    },
    'season': {
        '春': {'zh': '春', 'th': 'ใบไม้ผลิ'}, '夏': {'zh': '夏', 'th': 'ฤดูร้อน'},
        '秋': {'zh': '秋', 'th': 'ใบไม้ร่วง'}, '冬': {'zh': '冬', 'th': 'ฤดูหนาว'},
    },
    'style': {
        '极简': {'zh': '极简', 'th': 'มินิมอล'}, '复古': {'zh': '复古', 'th': 'วินเทจ'},
        '韩系': {'zh': '韩系', 'th': 'สไตล์เกาหลี'}, '休闲': {'zh': '休闲', 'th': 'ลำลอง'},
        '优雅': {'zh': '优雅', 'th': 'หรู'}, '通勤': {'zh': '通勤', 'th': 'ทำงาน'},
    },
}


def option_label(kind, key, lang):
    return _OPTION_LABEL[kind].get(key, {}).get(lang, key)


# 内置推荐色板（衣橱不足时的兜底「配色方案」）
PALETTE_ITEMS = [
    {'name': {'zh': '白', 'th': 'ขาว'}, 'category': '上衣', 'hex': '#FFFFFF'},
    {'name': {'zh': '黑', 'th': 'ดำ'}, 'category': '上衣', 'hex': '#202020'},
    {'name': {'zh': '雾霾蓝', 'th': 'ฟ้าอมเทา'}, 'category': '上衣', 'hex': '#9FB4C7'},
    {'name': {'zh': '浅灰', 'th': 'เทาอ่อน'}, 'category': '上衣', 'hex': '#C9CDD1'},
    {'name': {'zh': '米白', 'th': 'ครีม'}, 'category': '上衣', 'hex': '#EFE6D8'},
    {'name': {'zh': '浅粉', 'th': 'ชมพูอ่อน'}, 'category': '上衣', 'hex': '#F2C6CF'},
    {'name': {'zh': '藏蓝', 'th': 'กรมท่า'}, 'category': '上衣', 'hex': '#28364A'},
    {'name': {'zh': '酒红', 'th': 'ไวน์แดง'}, 'category': '上衣', 'hex': '#6E2B3C'},

    {'name': {'zh': '黑', 'th': 'ดำ'}, 'category': '下装', 'hex': '#242424'},
    {'name': {'zh': '卡其', 'th': 'สีกากี'}, 'category': '下装', 'hex': '#C3A87C'},
    {'name': {'zh': '深蓝', 'th': 'น้ำเงินเข้ม'}, 'category': '下装', 'hex': '#2E4A66'},
    {'name': {'zh': '白', 'th': 'ขาว'}, 'category': '下装', 'hex': '#F4F2EC'},
    {'name': {'zh': '深灰', 'th': 'เทาเข้ม'}, 'category': '下装', 'hex': '#4A4A4A'},
    {'name': {'zh': '橄榄绿', 'th': 'เขียวมะกอก'}, 'category': '下装', 'hex': '#6B7056'},

    {'name': {'zh': '红', 'th': 'แดง'}, 'category': '配饰', 'hex': '#B23A48'},
    {'name': {'zh': '金', 'th': 'ทอง'}, 'category': '配饰', 'hex': '#C9A227'},
    {'name': {'zh': '银灰', 'th': 'เทาเงิน'}, 'category': '配饰', 'hex': '#B9BEC4'},
    {'name': {'zh': '酒红', 'th': 'ไวน์แดง'}, 'category': '配饰', 'hex': '#6E2B3C'},
]


def item_name(item, lang):
    nm = item.get('name')
    if isinstance(nm, dict):
        return nm.get(lang, nm.get('zh', ''))
    return nm


# ---------------------------------------------------------------------------
# 条件适配打分
# ---------------------------------------------------------------------------

_SAT_IDEAL = {'低': (0.15, 0.32), '中': (0.45, 0.36), '高': (0.82, 0.36)}
_LIGHT_IDEAL = {'深': (0.22, 0.30), '中': (0.50, 0.36), '浅': (0.80, 0.30)}


def fit_score(hex_color, cfg):
    c = classify_color(hex_color)
    ideal, tol = _SAT_IDEAL[cfg['sat']]
    sat_fit = max(0.0, 100 - abs(c['s'] - ideal) / tol * 100)
    ideal, tol = _LIGHT_IDEAL[cfg['light']]
    light_fit = max(0.0, 100 - abs(c['l'] - ideal) / tol * 100)

    bands = cfg.get('hue', [])
    if not bands:
        hue_fit = 75.0
    elif c['temp'] == '中性':
        hue_fit = 72.0
    else:
        hue_fit = 100.0 if any(lo <= c['h'] < hi for lo, hi in bands) else 42.0
    return 0.30 * sat_fit + 0.30 * light_fit + 0.40 * hue_fit


# ---------------------------------------------------------------------------
# 推荐理由（双语）
# ---------------------------------------------------------------------------

_HARMONY_PHR = {
    'neutral': {'zh': '中性色搭配，低调高级，几乎不会出错',
                'th': 'โทนสีกลาง เรียบหรู แทบไม่พลาด'},
    'neutral_base': {'zh': '中性色打底 + 彩色点缀，稳妥又出彩',
                     'th': 'สีกลางเป็นพื้น + สีสดเป็นจุด เสริมให้โดดเด่น'},
    'analogous': {'zh': '同色系/邻近色，过渡自然和谐',
                  'th': 'สีเดียวกัน/ใกล้เคียง กลมกลืนเป็นธรรมชาติ'},
    'near': {'zh': '邻近色系，柔和协调', 'th': 'สีใกล้เคียง นุ่มนวลเข้ากัน'},
    'complementary': {'zh': '互补色，建议一主一次、小面积点缀',
                      'th': 'สีตรงข้าม แนะนำสีหลัก + สีเสริมเล็กน้อย'},
    'clash': {'zh': '高饱和互补色相撞，视觉冲突过强',
              'th': 'สีตรงข้ามอิ่มตัวสูง ตัดกันแรงเกินไป'},
    'high_sat': {'zh': '两色都高饱和，对比偏强',
                 'th': 'ทั้งสองสีอิ่มตัวสูง ตัดกันค่อนข้างแรง'},
    'mid': {'zh': '对比适中，整体协调', 'th': 'ตัดกันพอดี ภาพรวมเข้ากัน'},
}


def _avg(vals):
    return sum(vals) / len(vals) if vals else 75.0


# ---------------------------------------------------------------------------
# 身材适配打分（深色显瘦 / 浅色增体积）
# ---------------------------------------------------------------------------

def body_fit_score(hex_color, bmi_cat):
    if bmi_cat in ('偏胖', '肥胖'):
        ideal = 0.22          # 偏好深色
    elif bmi_cat == '偏瘦':
        ideal = 0.78          # 偏好浅色
    else:
        return 80.0           # 正常：无特殊偏好
    l = classify_color(hex_color)['l']
    return max(0.0, 100 - abs(l - ideal) / 0.35 * 100)


def _main_color_reason(cls, lang):
    colored = [c for c in cls if c['temp'] != '中性']
    if len(colored) < 2:
        return ('以中性色为主，高级耐看' if lang == 'zh'
                else 'เน้นโทนสีกลาง ดูมีระดับ')
    a, b = colored[0], colored[1]
    r = harmony(a['hex'], b['hex'])
    fa, fb = FAMILY[a['family']][lang], FAMILY[b['family']][lang]
    ph = _HARMONY_PHR[r['tag']][lang]
    return (f'主配色 {fa} + {fb}：{ph}' if lang == 'zh'
            else f'สีหลัก {fa} + {fb}: {ph}')


def _skin_reason(skin, lang, has_bad, neutral_only):
    if neutral_only:
        return ('以中性色为主，不挑肤色、安全百搭' if lang == 'zh'
                else 'เน้นโทนสีกลาง ใช้ได้ทุกสีผิว ปลอดภัย')
    if has_bad:
        if lang == 'zh':
            return '部分颜色与你的肤色不合：' + ('暖色易显黄' if skin == '冷' else '冷色易显苍白')
        return 'บางสีไม่เข้ากับผิวของคุณ: ' + ('สีโทนอุ่นทำให้ผิวดูเหลือง' if skin == '冷' else 'สีโทนเย็นทำให้ผิวดูซีด')
    if lang == 'zh':
        return '整体呼应你的' + ('冷调' if skin == '冷' else '暖调') + '肤色，衬托气质'
    return 'เข้ากับผิวโทน' + ('เย็น' if skin == '冷' else 'อุ่น') + 'ของคุณ ช่วยขับผิวให้สดใส'


# ---------------------------------------------------------------------------
# 单品组合评分
# ---------------------------------------------------------------------------

def score_outfit(items, profile, conditions, lang):
    """items: list of dict {name, category, hex}。返回带评分与理由的 dict。"""
    hexes = [it['hex'] for it in items]
    cls = [classify_color(h) for h in hexes]

    # 两两和谐度
    h_scores, clash_found = [], False
    for i in range(len(hexes)):
        for j in range(i + 1, len(hexes)):
            r = harmony(hexes[i], hexes[j])
            h_scores.append(r['score'])
            if r['tag'] == 'clash':
                clash_found = True
    harmony_avg = _avg(h_scores)

    # 肤色适配
    skin_vals = [skin_fit(h, profile['skin']) for h in hexes]
    skin_avg = _avg([v['score'] for v in skin_vals])
    has_bad = any(v['tag'] == 'bad' for v in skin_vals)
    neutral_only = all(v['tag'] == 'neutral' for v in skin_vals)

    # 条件适配
    occ = _avg([fit_score(h, OCCASION[conditions['occasion']]) for h in hexes])
    wea = _avg([fit_score(h, WEATHER[conditions['weather']]) for h in hexes])
    sea = _avg([fit_score(h, SEASON[conditions['season']]) for h in hexes])
    sty = _avg([fit_score(h, STYLE[profile['style']]) for h in hexes])

    # 身材适配（深色显瘦 / 浅色增体积）
    bmi_cat = bmi_category(calc_bmi(profile.get('height', 165), profile.get('weight', 55)))
    body_avg = _avg([body_fit_score(h, bmi_cat) for h in hexes])

    total = (0.28 * harmony_avg + 0.22 * skin_avg + 0.13 * occ
             + 0.09 * wea + 0.09 * sea + 0.10 * sty + 0.09 * body_avg)

    # 主色数量规则
    main_families = {c['family'] for c in cls if c['temp'] != '中性'}
    count_ok = len(main_families) <= 3
    total += 6 if count_ok else -12

    # 避开不喜欢颜色
    disliked = set(profile.get('disliked', []))
    hit = [c['family'] for c in cls if c['family'] in disliked]
    if hit:
        total -= 25

    total = max(0, min(100, round(total)))

    # 组装理由
    reasons = [_main_color_reason(cls, lang), _skin_reason(profile['skin'], lang, has_bad, neutral_only)]
    reasons.append(OCCASION[conditions['occasion']]['note'][lang])
    reasons.append(SEASON[conditions['season']]['note'][lang] + ' · '
                   + WEATHER[conditions['weather']]['note'][lang])
    reasons.append(STYLE[profile['style']]['note'][lang])
    if count_ok:
        reasons.append('全身主色 ≤3 种，符合搭配法则' if lang == 'zh'
                       else 'สีหลักทั้งตัวไม่เกิน 3 สี ตามหลักการจับคู่')
    else:
        reasons.append('主色超过 3 种，容易显乱，建议精简' if lang == 'zh'
                       else 'สีหลักเกิน 3 สี ดูรก แนะนำให้ลดจำนวนสี')
    if clash_found:
        reasons.append('检测到高饱和撞色，建议调整' if lang == 'zh'
                       else 'พบสีตัดกันแรงเกินไป แนะนำให้ปรับ')

    items_out = []
    for it, c in zip(items, cls):
        d = dict(it)
        d.update({'family': c['family'], 'temp': c['temp'],
                  'lightness': c['lightness'], 'saturation': c['saturation'],
                  'name': item_name(it, lang)})
        items_out.append(d)

    return {
        'score': total,
        'items': items_out,
        'palette': [c['hex'] for c in cls],
        'reasons': reasons,
    }


def _enumerate(tops, bottoms, outers, accents, profile, conditions, lang, top_n):
    disliked = set(profile.get('disliked', []))

    def ok(it):
        return classify_color(it['hex'])['family'] not in disliked

    tops = [it for it in tops if ok(it)]
    bottoms = [it for it in bottoms if ok(it)]
    outers = [it for it in outers if ok(it)]
    accents = [it for it in accents if ok(it)]

    best = {}
    for t in tops:
        for b in bottoms:
            base_ids = {t['id'], b['id']}
            for o in [None] + outers:
                if o and o['id'] in base_ids:
                    continue
                for a in [None] + accents:
                    if a and (a['id'] in base_ids or (o and a['id'] == o['id'])):
                        continue
                    pieces = [t, b] + ([o] if o else []) + ([a] if a else [])
                    r = score_outfit(pieces, profile, conditions, lang)
                    key = (t['id'], b['id'])
                    if key not in best or r['score'] > best[key]['score']:
                        best[key] = r
    return sorted(best.values(), key=lambda x: -x['score'])[:top_n]


def recommend(wardrobe, profile, conditions, lang, top_n=3):
    tops = [it for it in wardrobe if it['category'] == '上衣']
    bottoms = [it for it in wardrobe if it['category'] in ('下装', '裙装')]
    outers = [it for it in wardrobe if it['category'] == '外套']
    accents = [it for it in wardrobe if it['category'] in ('配饰', '鞋')]

    if not tops or not bottoms:
        return recommend_palette(profile, conditions, lang, top_n)

    results = _enumerate(tops, bottoms, outers, accents, profile, conditions, lang, top_n)
    for r in results:
        r['is_palette'] = False
    return results


def recommend_palette(profile, conditions, lang, top_n=3):
    tops = [it for it in PALETTE_ITEMS if it['category'] == '上衣']
    bottoms = [it for it in PALETTE_ITEMS if it['category'] == '下装']
    accents = [it for it in PALETTE_ITEMS if it['category'] == '配饰']
    # 为色板条目生成临时 id
    for i, it in enumerate(PALETTE_ITEMS):
        it['id'] = 'p%02d' % i
    results = _enumerate(tops, bottoms, [], accents, profile, conditions, lang, top_n)
    for r in results:
        r['is_palette'] = True
    return results
