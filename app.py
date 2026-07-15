import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# ================= 1. 파일 경로 및 초기화 =================
DATA_FILE = 'inventory_data.json'
CAT_FILE = 'category_data.json'
HISTORY_FILE = 'history_data.json'

def load_json(filepath, default_type):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
        except: return default_type
    return default_type

def save_all():
    with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(st.session_state.inventory, f, ensure_ascii=False, indent=4)
    with open(CAT_FILE, 'w', encoding='utf-8') as f: json.dump(st.session_state.categories, f, ensure_ascii=False, indent=4)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f: json.dump(st.session_state.history, f, ensure_ascii=False, indent=4)

# 초기 세션 상태 로드
if 'inventory' not in st.session_state: st.session_state.inventory = load_json(DATA_FILE, {})
if 'categories' not in st.session_state: st.session_state.categories = load_json(CAT_FILE, {})
if 'history' not in st.session_state: st.session_state.history = load_json(HISTORY_FILE, [])
if 'status_msg' not in st.session_state: st.session_state.status_msg = "대기 중..."
if 'selected_node' not in st.session_state: st.session_state.selected_node = ("ALL", None, None)

# ================= 2. 팝업창(Dialog) 함수 정의 =================
@st.dialog("➕ 신규 상품 등록")
def add_item_dialog(pre_filled=""):
    brand_opts = list(st.session_state.categories.keys())
    brand = st.selectbox("1. 브랜드명", brand_opts if brand_opts else ["(등록된 브랜드 없음)"])
    sub_list = st.session_state.categories.get(brand, [])
    sub = st.selectbox("2. 품목(카테고리)", sub_list if sub_list else ["(등록된 품목 없음)"])
    flex = st.text_input("3. 강성 (Flex)")
    loc = st.text_input("4. 보관 위치/칸")
    sku = st.text_input("5. 바코드 (SKU) *필수", value=pre_filled)
    if st.button("✅ 저장 및 등록", use_container_width=True):
        if not sku.strip(): st.error("바코드는 필수입니다.")
        elif sku.strip() in st.session_state.inventory: st.error("이미 등록된 바코드입니다.")
        else:
            st.session_state.inventory[sku.strip()] = {"brand": brand if brand != "(등록된 브랜드 없음)" else "", "sub_category": sub if sub != "(등록된 품목 없음)" else "", "flex": flex.strip(), "location": loc.strip(), "quantity": 0, "memo": ""}
            st.session_state.status_msg = f"✨ '{sku}' 등록 완료!"
            save_all(); st.rerun()

@st.dialog("📁 새 브랜드 추가")
def add_brand_dialog():
    nb = st.text_input("새로운 브랜드명 입력")
    if st.button("추가 완료", use_container_width=True) and nb:
        if nb not in st.session_state.categories:
            st.session_state.categories[nb] = [] 
            save_all(); st.rerun()
        else: st.error("이미 존재하는 브랜드입니다.")

@st.dialog("📄 새 품목 추가")
def add_sub_dialog():
    if not st.session_state.categories: st.warning("브랜드를 먼저 추가하세요!"); return
    tb = st.selectbox("어느 브랜드에 추가할까요?", list(st.session_state.categories.keys()))
    ns = st.text_input("새로운 품목명 입력")
    if st.button("추가 완료", use_container_width=True) and ns:
        if ns not in st.session_state.categories[tb]:
            st.session_state.categories[tb].append(ns)
            st.session_state.selected_node = ("BRAND", tb, None)
            save_all(); st.rerun()
        else: st.error("이미 존재하는 품목입니다.")

@st.dialog("📈 통계 및 분석 대시보드", width="large")
def stat_dialog():
    t1, t2, t3, t4 = st.tabs(["🏆 많이 팔린 제품", "⚠️ 재고 부족", "🏢 브랜드별 판매량", "📅 월별 판매량"])
    out_hist = [r for r in st.session_state.history if r['type'] == 'OUT']
    sku_sales = {}
    for r in out_hist: sku_sales[r['sku']] = sku_sales.get(r['sku'], 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
    with t1:
        df1 = pd.DataFrame([{"SKU": k, "브랜드": st.session_state.inventory.get(k, {}).get('brand', ''), "품목": st.session_state.inventory.get(k, {}).get('sub_category', ''), "강성": st.session_state.inventory.get(k, {}).get('flex', ''), "수량": v} for k, v in sku_sales.items()])
        if not df1.empty: df1 = df1.sort_values("수량", ascending=False)
        st.dataframe(df1, use_container_width=True, hide_index=True)
    with t2:
        df2 = pd.DataFrame([{"SKU": s, "브랜드": i.get('brand',''), "품목": i.get('sub_category',''), "강성": i.get('flex',''), "현재수량": i['quantity'], "판매수량": sku_sales.get(s, 0)} for s, i in st.session_state.inventory.items() if i['quantity'] <= 2])
        if not df2.empty: df2 = df2.sort_values("현재수량", ascending=True)
        st.dataframe(df2, use_container_width=True, hide_index=True)
    with t3:
        b_sales = {}
        for r in out_hist: b_sales[r['brand'] if r['brand'] else "미분류"] = b_sales.get(r['brand'] if r['brand'] else "미분류", 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
        st.dataframe(pd.DataFrame(list(b_sales.items()), columns=["브랜드", "판매량"]).sort_values("판매량", ascending=False), use_container_width=True)
    with t4:
        m_sales = {}
        for r in out_hist: 
            m = r['time'][:7]
            key = (m, r['sku'])
            m_sales[key] = m_sales.get(key, 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
        df4 = pd.DataFrame([{"해당 월": m, "SKU": s, "브랜드": st.session_state.inventory.get(s, {}).get('brand', ''), "품목": st.session_state.inventory.get(s, {}).get('sub_category', ''), "강성": st.session_state.inventory.get(s, {}).get('flex', ''), "수량": v} for (m, s), v in m_sales.items()])
        if not df4.empty: df4 = df4.sort_values(["해당 월", "수량"], ascending=[False, False])
        st.dataframe(df4, use_container_width=True, hide_index=True)

# ================= 3. 메인 레이아웃 및 기능 =================
st.set_page_config(layout="wide", page_title="스마트 재고 관리 시스템 v8.0")
menu1, menu2 = st.columns([1, 8])
with menu1:
    csv_data = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').to_csv(encoding='utf-8-sig')
    st.download_button("💾 엑셀 저장", data=csv_data, file_name="재고현황.csv", use_container_width=True)
with menu2:
    if st.button("📈 통계 대시보드"): stat_dialog()
st.divider()

# 좌측 사이드바 및 우측 메인 영역 등 나머지 로직은 이전과 동일...
# (하단에 나머지 기능들을 그대로 붙여넣으시면 됩니다)
