import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# 데이터 로드/저장 설정
DATA_FILE = 'inventory_data.json'
HISTORY_FILE = 'history_data.json'

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f: return json.load(f)
    return {} if file == DATA_FILE else []

# 상태 초기화
if 'inventory' not in st.session_state: st.session_state.inventory = load_json(DATA_FILE)
if 'history' not in st.session_state: st.session_state.history = load_json(HISTORY_FILE)

st.set_page_config(layout="wide")
st.title("📦 스마트 재고 관리 시스템 v8.0")

# 탭 구성
tab1, tab2 = st.tabs(["📦 재고 현황", "🕒 입출고 내역"])

with tab1:
    col_left, col_right = st.columns([1, 3])
    with col_left:
        st.subheader("분류 관리")
        # 원래의 트리뷰 대신 선택형 리스트 사용
        brands = list(set([item.get('brand', '미분류') for item in st.session_state.inventory.values()]))
        sel_brand = st.selectbox("브랜드", ["전체"] + brands)
    
    with col_right:
        st.subheader("재고 리스트")
        df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index')
        if sel_brand != "전체": df = df[df['brand'] == sel_brand]
        st.dataframe(df, use_container_width=True)

    st.subheader("스캔 및 등록")
    mode = st.radio("작업 모드", ["입고", "출고"], horizontal=True)
    barcode = st.text_input("바코드(SKU) 스캔")
    
    if st.button("확인(Enter)"):
        if barcode in st.session_state.inventory:
            change = 1 if mode == "입고" else -1
            st.session_state.inventory[barcode]['quantity'] += change
            # 히스토리 기록
            st.session_state.history.append({"time": str(datetime.now()), "sku": barcode, "type": mode, "change": change})
            with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(st.session_state.inventory, f, ensure_ascii=False)
            st.success(f"{barcode} {mode} 처리 완료!")
            st.rerun()
        else:
            st.warning("미등록 바코드입니다. 등록 절차가 필요합니다.")

with tab2:
    st.subheader("입출고 내역")
    hist_df = pd.DataFrame(st.session_state.history)
    st.dataframe(hist_df, use_container_width=True)
