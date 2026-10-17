# -*- coding: utf-8 -*-
"""
image_gen.py — AI 生图（智谱 CogView）
把一套穿搭用自然语言描述，调用智谱 CogView 生成真人效果图。
"""
import json
import os

import requests

API_URL = 'https://open.bigmodel.cn/api/paas/v4/images/generations'
MODEL = os.environ.get('ZHIPU_MODEL', 'cogview-4')


def _get_key():
    # 1) 环境变量
    k = os.environ.get('ZHIPUAI_API_KEY')
    if k:
        return k
    # 2) Streamlit secrets（.streamlit/secrets.toml）
    try:
        import streamlit as st
        k = st.secrets.get('ZHIPUAI_API_KEY')
        if k:
            return k
    except Exception:
        pass
    # 3) 本地配置文件 api_key.json（已 gitignore）
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_key.json')
    if os.path.exists(cfg):
        try:
            with open(cfg, 'r', encoding='utf-8') as f:
                return json.load(f).get('zhipu_api_key')
        except Exception:
            pass
    return None


def generate_outfit_image(prompt, size='1024x1024'):
    """调用 CogView 生成图片，返回 (bytes, url)。未配置 key 时抛错。"""
    key = _get_key()
    if not key:
        raise RuntimeError('未配置 ZHIPUAI_API_KEY：请在智谱开放平台 bigmodel.cn 创建密钥后提供。')

    r = requests.post(
        API_URL,
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={'model': MODEL, 'prompt': prompt, 'size': size},
        timeout=180,
    )
    if r.status_code != 200:
        raise RuntimeError(f'生图失败（HTTP {r.status_code}）：{r.text[:300]}')

    data = r.json()
    item = (data.get('data') or [{}])[0]
    url = item.get('url')
    if not url:
        raise RuntimeError(f'生图响应异常：{json.dumps(data, ensure_ascii=False)[:300]}')

    img = requests.get(url, timeout=60)
    if img.status_code != 200:
        raise RuntimeError(f'图片下载失败（HTTP {img.status_code}）')
    return img.content, url


def build_prompt(profile, items, conditions, lang='zh'):
    """根据身材 + 整套穿搭 + 场景生成自然语言描述（中文）。"""
    from i18n import FAMILY, CATEGORY
    from color_engine import classify_color
    from body_engine import calc_bmi, bmi_category

    gender = '男性' if profile.get('gender', '女') == '男' else '女性'
    bmi = calc_bmi(profile.get('height', 165), profile.get('weight', 55))
    bcat = bmi_category(bmi)
    bmi_word = {'偏瘦': '身材偏瘦', '正常': '身材匀称',
                '偏胖': '身材微胖', '肥胖': '身材丰满'}.get(bcat, '身材匀称')
    shape_word = {
        'H型': 'H 型身材（肩腰臀匀称）', '苹果型': '苹果型身材（腰腹丰满）',
        '梨型': '梨型身材（下半身丰满）', '沙漏型': '沙漏型身材（凹凸有致）',
        '倒三角型': '倒三角身材（肩宽）',
    }.get(profile.get('body_shape', 'H型'), '匀称身材')

    parts = []
    for it in items:
        fam = classify_color(it.get('hex', '#888888'))['family']
        parts.append(f"{CATEGORY[it['category']]['zh']}为{FAMILY[fam]['zh']}色")
    outfit = '，'.join(parts) if parts else '简约穿搭'

    season = {'春': '春季', '夏': '夏季', '秋': '秋季',
              '冬': '冬季'}.get(conditions.get('season'), '')
    occ = {'通勤上班': '通勤上班', '商务会议': '商务会议', '约会': '约会',
           '聚会派对': '聚会派对', '宴会正式': '正式宴会',
           '休闲日常': '日常休闲'}.get(conditions.get('occasion'), '日常')

    return (f"一位{gender}，{bmi_word}，{shape_word}，"
            f"身穿一套完整穿搭：{outfit}。"
            f"{season}{occ}场景，全身穿搭展示，"
            f"时尚杂志摄影风格，高清写实，自然光线，全身正面照，人物比例自然，背景简洁。")
