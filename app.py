import streamlit as st
import json
import os
import pandas as pd

# 데이터 파일
DATA_FILE = 'inventory_data.json'
CAT_FILE = 'category_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def load_cats():
    if os.path.exists(CAT_FILE):
        with open(CAT_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {"미분류": ["기본"]}

def save_all(data, cats):
    with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
    with open(CAT_FILE, 'w', encoding='utf-8') as f: json.dump(cats, f, ensure_ascii=False, indent=4)

if 'inventory' not in st.session_state: st.session_state.inventory = load_data()
if 'cats' not in st.session_state: st.session_state.cats = load_cats()

st.title("📂 카테고리 관리 시스템")

# 1. 사이드바: 브랜드 및 품목 관리
st.sidebar.subheader("브랜드/품목 설정")
selected_brand = st.sidebar.selectbox("브랜드 선택", list(st.session_state.cats.keys()))

# 브랜드 이름 변경 및 삭제
b_name = st.sidebar.text_input("브랜드 이름 변경", selected_brand)
if st.sidebar.button("브랜드 수정"):
    st.session_state.cats[b_name] = st.session_state.cats.pop(selected_brand)
    save_all(st.session_state.inventory, st.session_state.cats)
    st.rerun()

if st.sidebar.button("브랜드 삭제"):
    del st.session_state.cats[selected_brand]
    save_all(st.session_state.inventory, st.session_state.cats)
    st.rerun()

# 2. 품목 관리
st.sidebar.divider()
sub_list = st.session_state.cats[selected_brand]
selected_sub = st.sidebar.selectbox("품목 선택", sub_list)

s_name = st.sidebar.text_input("품목 이름 변경", selected_sub)
if st.sidebar.button("품목 수정"):
    idx = sub_list.index(selected_sub)
    sub_list[idx] = s_name
    save_all(st.session_state.inventory, st.session_state.cats)
    st.rerun()

# 품목 순서 이동 (올리기/내리기)
col1, col2 = st.sidebar.columns(2)
if col1.button("▲ 올리기"):
    idx = sub_list.index(selected_sub)
    if idx > 0:
        sub_list[idx], sub_list[idx-1] = sub_list[idx-1], sub_list[idx]
        save_all(st.session_state.inventory, st.session_state.cats)
        st.rerun()

if col2.button("▼ 내리기"):
    idx = sub_list.index(selected_sub)
    if idx < len(sub_list)-1:
        sub_list[idx], sub_list[idx+1] = sub_list[idx+1], sub_list[idx]
        save_all(st.session_state.inventory, st.session_state.cats)
        st.rerun()

if st.sidebar.button("품목 삭제"):
    sub_list.remove(selected_sub)
    save_all(st.session_state.inventory, st.session_state.cats)
    st.rerun()

# 3. 데이터 표시
st.dataframe(pd.DataFrame.from_dict(st.session_state.inventory, orient='index'))
