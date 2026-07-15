import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# 데이터 파일 설정
DATA_FILE = 'inventory_data.json'

# 데이터 로드 함수
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 데이터 저장 함수
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

st.set_page_config(page_title="재고 관리 시스템", layout="wide")
st.title("📦 스마트 재고 관리 시스템")

inventory = load_data()

# 탭 구성
tab1, tab2 = st.tabs(["재고 현황", "입출고 처리"])

with tab1:
    st.subheader("현재 재고 목록")
    if inventory:
        df = pd.DataFrame.from_dict(inventory, orient='index')
        st.dataframe(df, use_container_width=True)
    else:
        st.write("데이터가 없습니다.")

with tab2:
    st.subheader("스캔 및 입출고")
    barcode = st.text_input("바코드(SKU) 입력 후 엔터")
    mode = st.radio("작업 선택", ["입고", "출고"])

    if barcode:
        if barcode in inventory:
            if st.button("확인"):
                if mode == "입고":
                    inventory[barcode]['quantity'] += 1
                else:
                    inventory[barcode]['quantity'] -= 1
                save_data(inventory)
                st.success(f"{barcode} 처리 완료!")
                st.rerun()
        else:
            st.error("등록되지 않은 상품입니다.")