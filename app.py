import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# 데이터 파일
DATA_FILE = 'inventory_data.json'
CAT_FILE = 'category_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_categories():
    if os.path.exists(CAT_FILE):
        with open(CAT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"미분류": ["기본"]}

def save_all(data, cats):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    with open(CAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=4)

st.set_page_config(layout="wide")
st.title("📦 스마트 재고 관리 시스템 v8.0")

# 데이터 로드
if 'inventory' not in st.session_state: st.session_state.inventory = load_data()
if 'categories' not in st.session_state: st.session_state.categories = load_categories()

# 1. 카테고리 관리 (버튼 방식)
st.sidebar.subheader("📂 카테고리 관리")
brand_list = list(st.session_state.categories.keys())
selected_brand = st.sidebar.selectbox("브랜드 선택", brand_list)
sub_list = st.session_state.categories.get(selected_brand, [])

col1, col2 = st.sidebar.columns(2)
if col1.button("브랜드 추가"):
    new_b = st.sidebar.text_input("새 브랜드명")
    if new_b: st.session_state.categories[new_b] = ["기본"]
if col2.button("품목 추가"):
    new_s = st.sidebar.text_input("새 품목명")
    if new_s and new_s not in sub_list: st.session_state.categories[selected_brand].append(new_s)

# 2. 재고 현황 및 검색
st.subheader("📦 재고 현황")
search = st.text_input("🔍 SKU 검색")
df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index')

if search:
    df = df[df.index.str.contains(search, na=False)]
st.dataframe(df, use_container_width=True)

# 3. 입출고 및 등록
st.divider()
with st.expander("➕ 상품 입출고 / 신규 등록"):
    sku = st.text_input("바코드(SKU)")
    col_a, col_b = st.columns(2)
    
    if col_a.button("입고 (+1)"):
        if sku in st.session_state.inventory:
            st.session_state.inventory[sku]['quantity'] += 1
        else:
            st.session_state.inventory[sku] = {"brand": selected_brand, "sub_category": sub_list[0] if sub_list else "기본", "quantity": 1, "memo": ""}
        save_all(st.session_state.inventory, st.session_state.categories)
        st.rerun()
        
    if col_b.button("출고 (-1)"):
        if sku in st.session_state.inventory and st.session_state.inventory[sku]['quantity'] > 0:
            st.session_state.inventory[sku]['quantity'] -= 1
            save_all(st.session_state.inventory, st.session_state.categories)
            st.rerun()
        else:
            st.error("재고 부족 또는 미등록 상품")

# 변경사항 저장 알림
if st.button("모든 설정 저장"):
    save_all(st.session_state.inventory, st.session_state.categories)
    st.success("저장 완료!")
