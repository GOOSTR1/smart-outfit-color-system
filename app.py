# -*- coding: utf-8 -*-
"""
app.py — 智能穿搭色彩系统（Streamlit 前端）
表现层 + 应用/工作流层：衣橱管理、个人档案、穿搭推荐、色彩知识。
"""
import uuid

import streamlit as st

from i18n import t, FAMILY, TEMP, LIGHT, SAT, CATEGORY
from data import load_data, save_data, CATEGORIES
from recommender import (
    recommend, option_label, item_name, WEATHER_OPTIONS, OCCASION_OPTIONS,
    SEASON_OPTIONS, STYLE_OPTIONS,
)
from body_engine import body_advice, body_summary, BODY_SHAPES, SHAPE_NAME
from avatar import render_avatar

st.set_page_config(page_title='智能穿搭色彩系统', page_icon='🎨', layout='wide')


# ---------------------------------------------------------------------------
# 状态初始化
# ---------------------------------------------------------------------------
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'lang' not in st.session_state:
    st.session_state.lang = 'zh'

LANG = st.session_state.lang


def _t(key):
    return t(LANG, key)


# ---------------------------------------------------------------------------
# 渲染辅助
# ---------------------------------------------------------------------------
def swatch(hexc, size='30px', radius='8px'):
    return (f'<span style="display:inline-block;width:{size};height:{size};'
            f'border-radius:{radius};background:{hexc};'
            f'border:1px solid rgba(0,0,0,.15);vertical-align:middle"></span>')


def color_bar(hexes):
    segs = ''.join(
        f'<div style="flex:1;height:34px;background:{h};min-width:10px"></div>'
        for h in hexes)
    return (f'<div style="display:flex;border-radius:10px;overflow:hidden;'
            f'border:1px solid rgba(0,0,0,.12);margin:6px 0">{segs}</div>')


def item_card(it):
    cat = CATEGORY[it['category']][LANG]
    fam = FAMILY[it['family']][LANG]
    meta = f'{cat} · {fam} · {TEMP[it["temp"]][LANG]} · {SAT[it["saturation"]][LANG]}'
    return (
        f'<div style="display:inline-block;text-align:center;margin:4px 14px 4px 0;width:110px">'
        f'<div style="width:64px;height:64px;border-radius:12px;background:{it["hex"]};'
        f'border:1px solid rgba(0,0,0,.15);margin:0 auto 6px"></div>'
        f'<div style="font-weight:600;font-size:13px">{it["name"]}</div>'
        f'<div style="font-size:11px;color:#888">{meta}</div>'
        f'</div>')


def score_badge(score):
    if score >= 85:
        color = '#1f9d55'
    elif score >= 70:
        color = '#b7791f'
    else:
        color = '#c53030'
    return (f'<span style="background:{color};color:#fff;font-weight:700;'
            f'padding:4px 12px;border-radius:20px">{score}</span>')


# ---------------------------------------------------------------------------
# 侧边栏：语言 + 导航
# ---------------------------------------------------------------------------
with st.sidebar:
    lang_choice = st.selectbox(
        _t('lang_label'), ['中文', 'ไทย'],
        index=0 if st.session_state.lang == 'zh' else 1)
    st.session_state.lang = 'zh' if lang_choice == '中文' else 'th'
    LANG = st.session_state.lang

    st.markdown('## 🎨 ' + _t('app_title'))
    nav = st.radio(_t('nav_label'), [
        _t('nav_home'), _t('nav_wardrobe'), _t('nav_profile'),
        _t('nav_recommend'), _t('nav_knowledge'),
    ])
    st.caption(_t('footer'))

# 语言切换后重新绑定
LANG = st.session_state.lang


# ---------------------------------------------------------------------------
# 首页
# ---------------------------------------------------------------------------
def page_home():
    st.title(_t('app_title'))
    st.subheader(_t('app_subtitle'))
    st.info(_t('home_howto'))

    st.markdown('#### ' + _t('home_feat_title'))
    feats = {
        'zh': [
            ('🎨 色彩基础判断', '基于色相环与色彩理论，自动排除冲突配色，提供和谐配色备选。'),
            ('🧑‍🎨 个人属性适配', '结合肤色冷暖、发色深浅，筛选最适合你的专属色系。'),
            ('🌦️ 外部条件动态推荐', '结合天气、场合、季节与流行趋势，生成场景化方案。'),
            ('👗 现有衣柜资产利用', '盘活衣橱存量单品，挖掘旧衣新穿法，避免重复购买。'),
            ('⚡ 日常决策提效', '输入条件即可快速生成 2~3 套方案，告别选择困难。'),
            ('🧭 风格统一保障', '锚定核心风格、统一配色基调，塑造个人时尚标签。'),
            ('🛡️ 配色避坑提示', '遵循「主色 ≤3 种」等法则，避开高饱和撞色雷区。'),
        ],
        'th': [
            ('🎨 การตัดสินสีพื้นฐาน', 'อิงวงล้อสีและทฤษฎีสี คัดกรองสีที่ขัดกัน เสนอสีที่กลมกลืน'),
            ('🧑‍🎨 ปรับตามคุณสมบัติบุคคล', 'คัดสีที่เหมาะกับโทนผิวและสีผมของคุณ'),
            ('🌦️ แนะนำตามเงื่อนไขภายนอก', 'รวมอากาศ/โอกาส/ฤดูกาล สร้างชุดตามสถานการณ์'),
            ('👗 ใช้ตู้เสื้อผ้าที่มีอยู่', 'ใช้เสื้อผ้าที่มีให้คุ้มค่า ลดการซื้อซ้ำ'),
            ('⚡ ตัดสินใจเร็วขึ้น', 'สร้างชุดได้ 2–3 ชุดในพริบตา หมดปัญหาลังเล'),
            ('🧭 รักษาสไตล์ให้สม่ำเสมอ', 'ยึดสไตล์หลักและโทนสีเดียวกัน สร้างเอกลักษณ์'),
            ('🛡️ หลีกเลี่ยงกับดักสี', 'ใช้กฎ «สีหลักไม่เกิน 3 สี» หลีกเลี่ยงสีตัดกันแรง'),
        ],
    }
    for icon_title, desc in feats[LANG]:
        st.markdown(f'**{icon_title}** — {desc}')

    st.markdown('#### ' + _t('home_value_title'))
    values = {
        'zh': ['个性化', '智能化', '高效化', '实用化', '时尚化'],
        'th': ['เฉพาะบุคคล', 'อัจฉริยะ', 'มีประสิทธิภาพ', 'ใช้ได้จริง', 'ทันสมัย'],
    }
    st.markdown(' · '.join(f'`{v}`' for v in values[LANG]))


# ---------------------------------------------------------------------------
# 我的衣橱
# ---------------------------------------------------------------------------
def page_wardrobe():
    st.title(_t('nav_wardrobe'))
    data = st.session_state.data
    wardrobe = data['wardrobe']

    with st.expander(_t('w_add_title'), expanded=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        name = c1.text_input(_t('w_name'), placeholder=_t('w_name_ph'))
        cat = c2.selectbox(_t('w_category'), CATEGORIES,
                           format_func=lambda c: CATEGORY[c][LANG])
        color = c3.color_picker(_t('w_color'), '#9FB4C7')
        if c4.button(_t('w_add_btn'), use_container_width=True) and name.strip():
            wardrobe.append({
                'id': uuid.uuid4().hex[:8],
                'name': name.strip(),
                'category': cat,
                'hex': color,
            })
            save_data(data)
            st.success(name.strip())

    st.markdown('#### ' + _t('w_list_title').format(n=len(wardrobe)))
    if not wardrobe:
        st.info(_t('w_empty'))
    else:
        for it in wardrobe:
            from color_engine import classify_color
            c = classify_color(it['hex'])
            col1, col2, col3, col4, col5 = st.columns([0.6, 1.6, 1.2, 1.6, 0.6])
            col1.markdown(swatch(it['hex'], '34px'), unsafe_allow_html=True)
            col2.write(f"**{item_name(it, LANG)}**")
            col3.write(CATEGORY[it['category']][LANG])
            col4.write(FAMILY[c['family']][LANG] + ' · ' + TEMP[c['temp']][LANG])
            if col5.button(_t('w_delete'), key='del_' + it['id']):
                data['wardrobe'] = [x for x in wardrobe if x['id'] != it['id']]
                save_data(data)
                st.rerun()

    if wardrobe and st.button(_t('w_clear')):
        data['wardrobe'] = []
        save_data(data)
        st.success(_t('w_clear_confirm'))
        st.rerun()


# ---------------------------------------------------------------------------
# 个人档案
# ---------------------------------------------------------------------------
def page_profile():
    st.title(_t('nav_profile'))
    data = st.session_state.data
    profile = data['profile']

    st.markdown('#### ' + _t('p_skin'))
    skin = st.radio(
        _t('p_skin'), ['冷', '暖'],
        index=0 if profile['skin'] == '冷' else 1,
        format_func=lambda v: (_t('p_skin_cool') if v == '冷' else _t('p_skin_warm')))
    st.caption(_t('p_skin_hint'))

    st.markdown('#### ' + _t('p_hair'))
    hair = st.radio(
        _t('p_hair'), ['深', '浅'],
        index=0 if profile['hair'] == '深' else 1,
        format_func=lambda v: (_t('p_hair_deep') if v == '深' else _t('p_hair_light')))

    st.markdown('#### ' + _t('p_style'))
    style = st.selectbox(
        _t('p_style'), STYLE_OPTIONS,
        index=STYLE_OPTIONS.index(profile['style']),
        format_func=lambda s: option_label('style', s, LANG))

    st.markdown('#### ' + _t('p_disliked'))
    family_keys = ['红', '橙', '黄', '绿', '蓝', '紫', '粉', '棕', '黑', '灰']
    disliked = st.multiselect(
        _t('p_disliked'), family_keys,
        default=profile['disliked'],
        format_func=lambda f: FAMILY[f][LANG])

    st.markdown('#### ' + _t('p_body_title'))
    c1, c2 = st.columns(2)
    height = c1.number_input(_t('p_height'), 120, 220, int(profile.get('height', 165)), step=1)
    weight = c2.number_input(_t('p_weight'), 30, 200, int(profile.get('weight', 55)), step=1)
    body_shape = st.selectbox(
        _t('p_shape'), BODY_SHAPES,
        index=BODY_SHAPES.index(profile.get('body_shape', 'H型')),
        format_func=lambda s: SHAPE_NAME[s][LANG])
    st.caption(_t('p_shape_hint'))

    st.markdown('##### ' + _t('p_measure_title'))
    m1, m2, m3 = st.columns(3)
    bust = m1.number_input(_t('p_bust'), 0, 160, int(profile.get('bust_cm', 0)), step=1)
    waist_cm = m2.number_input(_t('p_waist'), 0, 160, int(profile.get('waist_cm', 0)), step=1)
    hip_cm = m3.number_input(_t('p_hip'), 0, 160, int(profile.get('hip_cm', 0)), step=1)
    st.caption(_t('p_measure_hint'))

    col_av, col_sum = st.columns([1, 2])
    live = {'height': height, 'weight': weight, 'body_shape': body_shape,
            'hair': profile.get('hair', '深'),
            'bust_cm': bust, 'waist_cm': waist_cm, 'hip_cm': hip_cm}
    col_av.markdown(render_avatar(live, [], 160, 344), unsafe_allow_html=True)
    col_sum.info(body_summary(live, LANG))

    if st.button(_t('p_save'), type='primary'):
        profile['skin'] = skin
        profile['hair'] = hair
        profile['style'] = style
        profile['disliked'] = disliked
        profile['height'] = height
        profile['weight'] = weight
        profile['body_shape'] = body_shape
        profile['bust_cm'] = bust
        profile['waist_cm'] = waist_cm
        profile['hip_cm'] = hip_cm
        save_data(data)
        st.success(_t('p_saved'))


# ---------------------------------------------------------------------------
# 穿搭推荐
# ---------------------------------------------------------------------------
def page_recommend():
    st.title(_t('nav_recommend'))
    data = st.session_state.data
    wardrobe = data['wardrobe']
    profile = data['profile']

    st.markdown('#### ' + _t('r_conditions'))
    c1, c2, c3 = st.columns(3)
    weather = c1.selectbox(_t('r_weather'), WEATHER_OPTIONS,
                           format_func=lambda w: option_label('weather', w, LANG))
    occasion = c2.selectbox(_t('r_occasion'), OCCASION_OPTIONS,
                            format_func=lambda o: option_label('occasion', o, LANG))
    season = c3.selectbox(_t('r_season'), SEASON_OPTIONS,
                          format_func=lambda s: option_label('season', s, LANG))

    conditions = {'weather': weather, 'occasion': occasion, 'season': season}

    with st.expander(_t('r_body_tips'), expanded=False):
        st.caption(body_summary(profile, LANG))
        for tip in body_advice(profile, LANG):
            st.markdown(f'- {tip}')

    if st.button(_t('r_generate'), type='primary'):
        st.session_state['gen_conditions'] = conditions
        st.session_state['gen_lang'] = LANG
        st.session_state['results'] = recommend(wardrobe, profile, conditions, LANG)

    # 语言切换后重新本地化
    if 'results' in st.session_state and st.session_state.get('gen_lang') != LANG:
        st.session_state['results'] = recommend(
            wardrobe, profile, st.session_state['gen_conditions'], LANG)
        st.session_state['gen_lang'] = LANG

    if 'results' not in st.session_state:
        st.info(_t('r_hint'))
        return

    results = st.session_state['results']
    if not results:
        st.warning(_t('r_no_items'))
        return

    if results[0].get('is_palette'):
        st.caption(_t('r_no_items'))
        st.markdown('### ' + _t('r_palette_title'))
    else:
        st.markdown('### ' + _t('r_result'))

    for i, r in enumerate(results, 1):
        with st.container(border=True):
            col_av, col_main = st.columns([1, 3.4])
            with col_av:
                st.markdown(render_avatar(profile, r['items'], 150, 322),
                            unsafe_allow_html=True)
                st.markdown(score_badge(r['score']), unsafe_allow_html=True)
                st.caption(_t('r_score'))
            with col_main:
                st.markdown(f'#### {_t("r_item_prefix").format(i=i)}')
                st.markdown(color_bar(r['palette']), unsafe_allow_html=True)
                st.markdown(''.join(item_card(it) for it in r['items']),
                            unsafe_allow_html=True)
            with st.expander(_t('r_reasons')):
                for reason in r['reasons']:
                    st.markdown(f'- {reason}')


# ---------------------------------------------------------------------------
# 色彩知识
# ---------------------------------------------------------------------------
def page_knowledge():
    st.title(_t('nav_knowledge'))

    st.markdown('### ' + _t('k_wheel'))
    st.markdown(
        '<div style="width:230px;height:230px;border-radius:50%;margin:10px auto;'
        'background:conic-gradient(#e53935,#fb8c00,#fdd835,#7cb342,#26a69a,'
        '#1e88e5,#5e35b1,#d81b60,#e53935)"></div>',
        unsafe_allow_html=True)

    st.markdown('### ' + _t('k_harmony'))
    harmony_rules = {
        'zh': [
            ('同色系 / 邻近色', '色相环上相邻的颜色，过渡自然、几乎不踩雷，如米白 + 卡其。'),
            ('中性色打底', '黑白灰米白作为大面积底色，任何彩色都能安全点缀。'),
            ('互补色点缀', '互补色（如蓝 + 橙）适合一主一次、小面积点缀，忌大面积对撞。'),
        ],
        'th': [
            ('สีเดียวกัน / ใกล้เคียง', 'สีที่อยู่ติดกันในวงล้อสี กลมกลืน แทบไม่พลาด เช่น ครีม + สีกากี'),
            ('ใช้สีกลางเป็นพื้น', 'ดำ ขาว เทา ครีมเป็นพื้นหลัก แล้วเสริมด้วยสีอื่นได้อย่างปลอดภัย'),
            ('สีตรงข้ามเป็นจุดเสริม', 'สีตรงข้าม (เช่น น้ำเงิน + ส้ม) ใช้สีหลัก + สีเสริมเล็กน้อย อย่าใช้เท่ากัน'),
        ],
    }
    for title, desc in harmony_rules[LANG]:
        st.markdown(f'**{title}**：{desc}')

    st.markdown('### ' + _t('k_avoid'))
    avoid_tips = {
        'zh': [
            '❌ 避免大面积红配绿、高饱和撞色，视觉冲击过强。',
            '❌ 全身主色调建议不超过 3 种，避免杂乱。',
            '❌ 冷皮慎用暖黄/橘调（易显黄），暖皮慎用冷蓝/紫（易显苍白）。',
            '✅ 浅色系易显脏，优先抗污/垂坠面料；深色可用丝绒、缎面增加层次。',
        ],
        'th': [
            '❌ หลีกเลี่ยงแดง + เขียวพื้นที่กว้าง และสีตัดกันอิ่มตัวสูง',
            '❌ สีหลักทั้งตัวไม่ควรเกิน 3 สี เพื่อไม่ให้ดูรก',
            '❌ ผิวเย็นระวังสีเหลือง/ส้ม (ดูเหลือง) ผิวอุ่นระวังน้ำเงิน/ม่วง (ดูซีด)',
            '✅ สีอ่อนเลอะง่าย เลือกผ้าไม่ยับ/กันเปื้อน สีเข้มเสริมด้วยผ้าเงาเพิ่มมิติ',
        ],
    }
    for tip in avoid_tips[LANG]:
        st.markdown(tip)


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------
PAGES = {
    _t('nav_home'): page_home,
    _t('nav_wardrobe'): page_wardrobe,
    _t('nav_profile'): page_profile,
    _t('nav_recommend'): page_recommend,
    _t('nav_knowledge'): page_knowledge,
}
PAGES[nav]()
