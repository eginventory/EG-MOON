import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# ================= 파일 경로 설정 =================
DATA_FILE = 'inventory_data.json'
CAT_FILE = 'category_data.json'
HISTORY_FILE = 'history_data.json'

# ================= 데이터 로드 및 저장 =================
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

# 삭제용 체크박스 상태 관리
if 'delete_mode' not in st.session_state: st.session_state.delete_mode = False

# ================= 메인 UI 구성 시작 =================
st.set_page_config(layout="wide", page_title="스마트 재고 관리 시스템 v8.0")

# 디자인 커스텀 (CSS)
st.markdown("""
<style>
    [data-testid="stExpanderDetails"] { gap: 0rem !important; padding: 0rem !important; }
    [data-testid="stExpanderDetails"] .stButton { margin-top: -0.2rem !important; margin-bottom: -0.2rem !important; }
</style>
""", unsafe_allow_html=True)

# ================= [팝업창 함수들 생략(기존과 동일)] =================
# (코드가 너무 길어져 생략했으나, 이전 코드의 add_item_dialog, add_brand_dialog, add_sub_dialog, manage_category_dialog, stat_dialog 함수를 그대로 아래에 유지하시면 됩니다.)
# [중요] 실제 붙여넣기 하실 때는 위 생략된 팝업 함수들을 이전 코드 그대로 가져와주세요!

# ================= 레이아웃 시작 =================
menu1, menu2, menu3 = st.columns([2, 2, 6])
with menu1:
    csv_data = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').to_csv(encoding='utf-8-sig')
    st.download_button("💾 엑셀(CSV) 전체 재고 저장", data=csv_data, file_name="재고현황.csv", use_container_width=True)
with menu2:
    if st.button("📈 통계 대시보드 열기", use_container_width=True): stat_dialog()
st.divider()

left_pane, right_pane = st.columns([1, 4])

with left_pane:
    st.markdown("### 📂 분류 폴더")
    for b, subs in st.session_state.categories.items():
        is_expanded = (st.session_state.selected_node[1] == b)
        with st.expander(f"📁 {b}", expanded=is_expanded):
            for s in subs:
                s_type = "primary" if st.session_state.selected_node == ("SUB", b, s) else "secondary"
                if st.button(f"└ 📄 {s}", key=f"btn_{b}_{s}", use_container_width=True, type=s_type):
                    st.session_state.selected_node = ("SUB", b, s) if st.session_state.selected_node != ("SUB", b, s) else ("ALL", None, None)
                    st.rerun()
    st.markdown("---")
    btn1, btn2, btn3 = st.columns(3)
    if btn1.button("브랜드+"): add_brand_dialog()
    if btn2.button("품목+"): add_sub_dialog()
    if btn3.button("관리/삭제"): manage_category_dialog()

with right_pane:
    # (스캔 로직 등은 이전 코드와 동일)
    tab_inv, tab_hist = st.tabs(["📦 재고 현황", "🕒 입출고 내역 (히스토리)"])
    
    with tab_inv:
        # 삭제 모드 토글 및 실행
        st.session_state.delete_mode = st.toggle("🗑️ 상품 삭제 모드 활성화")
        
        df_inv = pd.DataFrame([{"SKU": k, "Brand": v.get('brand',''), "SubCat": v.get('sub_category',''), "Flex": v.get('flex',''), "Qty": v['quantity'], "Memo": v.get('memo','')} for k, v in st.session_state.inventory.items()])
        
        # 💡 체크박스 기능 추가된 데이터 테이블
        if not df_inv.empty:
            # 삭제 모드일 때만 체크박스 컬럼 추가
            if st.session_state.delete_mode:
                df_inv.insert(0, "선택", False)
                edited_df = st.data_editor(df_inv, use_container_width=True, hide_index=True, column_config={"선택": st.column_config.CheckboxColumn(required=True)})
                
                if st.button("⚠️ 선택한 항목 영구 삭제", type="primary"):
                    to_delete = edited_df[edited_df['선택'] == True]['SKU'].tolist()
                    for sku in to_delete:
                        del st.session_state.inventory[sku]
                    save_all()
                    st.rerun()
            else:
                # 삭제 모드가 아닐 때는 일반 편집 테이블
                edited_df = st.data_editor(df_inv, use_container_width=True, hide_index=True, disabled=["SKU", "Brand", "SubCat", "Flex", "Qty"])
                for idx, row in edited_df.iterrows():
                    if st.session_state.inventory[row['SKU']].get('memo') != row['Memo']:
                        st.session_state.inventory[row['SKU']]['memo'] = row['Memo']
                        save_all()
