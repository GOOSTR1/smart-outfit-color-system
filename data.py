# -*- coding: utf-8 -*-
"""
data.py — 数据层
默认示例衣橱 / 个人档案，以及 JSON 文件持久化（对应论文「数据层」）。
"""
import json
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DATA_DIR, 'user_data.json')

CATEGORIES = ['上衣', '下装', '裙装', '外套', '鞋', '配饰']

# 首启示例衣橱（便于开箱即可生成推荐；名称内置中泰双语）
def _nm(zh, th):
    return {'zh': zh, 'th': th}


DEFAULT_WARDROBE = [
    {'id': 'w01', 'name': _nm('白色衬衫', 'เสื้อเชิ้ตสีขาว'), 'category': '上衣', 'hex': '#FFFFFF'},
    {'id': 'w02', 'name': _nm('黑色高领针织', 'เสื้อคอเต่าสีดำ'), 'category': '上衣', 'hex': '#202020'},
    {'id': 'w03', 'name': _nm('雾霾蓝衬衫', 'เสื้อเชิ้ตสีฟ้าอมเทา'), 'category': '上衣', 'hex': '#9FB4C7'},
    {'id': 'w04', 'name': _nm('浅灰卫衣', 'ฮู้ดดี้สีเทาอ่อน'), 'category': '上衣', 'hex': '#C9CDD1'},
    {'id': 'w05', 'name': _nm('米白针织衫', 'เสื้อถักสีครีม'), 'category': '上衣', 'hex': '#EFE6D8'},
    {'id': 'w06', 'name': _nm('卡其休闲裤', 'กางเกงผ้าสีกากี'), 'category': '下装', 'hex': '#C3A87C'},
    {'id': 'w07', 'name': _nm('黑色直筒裤', 'กางเกงขายาวสีดำ'), 'category': '下装', 'hex': '#242424'},
    {'id': 'w08', 'name': _nm('深蓝牛仔裤', 'กางเกงยีนส์สีน้ำเงินเข้ม'), 'category': '下装', 'hex': '#2E4A66'},
    {'id': 'w09', 'name': _nm('白色半身裙', 'กระโปรงสีขาว'), 'category': '裙装', 'hex': '#F4F2EC'},
    {'id': 'w10', 'name': _nm('酒红半身裙', 'กระโปรงสีไวน์'), 'category': '裙装', 'hex': '#6E2B3C'},
    {'id': 'w11', 'name': _nm('驼色大衣', 'โค้ทสีคาเมล'), 'category': '外套', 'hex': '#B68A5E'},
    {'id': 'w12', 'name': _nm('藏蓝西装外套', 'เสื้อเบลเซอร์กรมท่า'), 'category': '外套', 'hex': '#28364A'},
    {'id': 'w13', 'name': _nm('白色运动鞋', 'รองเท้าผ้าใบสีขาว'), 'category': '鞋', 'hex': '#F2F2F0'},
    {'id': 'w14', 'name': _nm('棕色皮鞋', 'รองเท้าหนังสีน้ำตาล'), 'category': '鞋', 'hex': '#5C4033'},
    {'id': 'w15', 'name': _nm('红色丝巾', 'ผ้าพันคอสีแดง'), 'category': '配饰', 'hex': '#B23A48'},
    {'id': 'w16', 'name': _nm('金色项链', 'สร้อยคอสีทอง'), 'category': '配饰', 'hex': '#C9A227'},
]

DEFAULT_PROFILE = {
    'skin': '冷',
    'hair': '深',
    'style': '极简',
    'disliked': [],
}


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            # 补齐缺失字段
            if 'wardrobe' not in d:
                d['wardrobe'] = DEFAULT_WARDROBE
            if 'profile' not in d:
                d['profile'] = DEFAULT_PROFILE
            return d
        except Exception:
            pass
    return {'wardrobe': list(DEFAULT_WARDROBE), 'profile': dict(DEFAULT_PROFILE)}


def save_data(data: dict) -> None:
    # 云端/只读环境写入失败时静默降级为内存态，避免应用崩溃
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
