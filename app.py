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
if 'inventory' not in st.session_state: 
    st.session_state.inventory = load_json(DATA_FILE, {})
if 'categories' not in st.session_state: 
    st.session_state.categories = load_json(CAT_FILE, {})
if 'history' not in st.session_state: 
    st.session_state.history = load_json(HISTORY_FILE, [])
if 'status_msg' not in st.session_state: 
    st.session_state.status_msg = "대기 중..."
if 'selected_node' not in st.session_state: 
    st.session_state.selected_node = ("ALL", None, None)

# '기본' 데이터 자동 청소 로직
cleaned = False
for b in list(st.session_state.categories.keys()):
    if "기본" in st.session_state.categories[b]:
        st.session_state.categories[b].remove("기본")
        cleaned = True
for sku, info in st.session_state.inventory.items():
    if info.get('sub_category') == '기본':
        info['sub_category'] = ''
        cleaned = True
if cleaned:
    save_all()

# ================= 메인 UI 구성 시작 =================
st.set_page_config(layout="wide", page_title="스마트 재고 관리 시스템 v8.0")

# 디자인 커스텀 (CSS) - 폴더와 품목 사이의 간격을 확 줄여줍니다
st.markdown("""
<style>
    [data-testid="stExpanderDetails"] {
        gap: 0rem !important;
        padding-top: 0rem !important;
        padding-bottom: 0.5rem !important;
    }
    [data-testid="stExpanderDetails"] .stButton {
        margin-top: -0.2rem !important;
        margin-bottom: -0.2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= 팝업창(Toplevel) 완벽 구현 =================
@st.dialog("➕ 신규 상품 등록")
def add_item_dialog(pre_filled=""):
    st.warning("등록되지 않은 바코드입니다. 새로 등록하시겠습니까?" if pre_filled else "새로운 상품을 등록합니다.")
    
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
            st.session_state.inventory[sku.strip()] = {
                "brand": brand if brand != "(등록된 브랜드 없음)" else "", 
                "sub_category": sub if sub != "(등록된 품목 없음)" else "", 
                "flex": flex.strip(), 
                "location": loc.strip(), 
                "quantity": 0, "memo": ""
            }
            st.session_state.status_msg = f"✨ '{sku}' 등록 완료!"
            save_all()
            st.rerun()

@st.dialog("📁 새 브랜드 추가")
def add_brand_dialog():
    nb = st.text_input("새로운 브랜드명 입력")
    if st.button("추가 완료", use_container_width=True) and nb:
        if nb not in st.session_state.categories:
            st.session_state.categories[nb] = [] 
            save_all()
            st.rerun()
        else:
            st.error("이미 존재하는 브랜드입니다.")

@st.dialog("📄 새 품목 추가")
def add_sub_dialog():
    if not st.session_state.categories:
        st.warning("먼저 브랜드를 추가해주세요!")
        return
        
    tb = st.selectbox("어느 브랜드에 추가할까요?", list(st.session_state.categories.keys()))
    ns = st.text_input("새로운 품목명 입력")
    if st.button("추가 완료", use_container_width=True) and ns:
        if ns not in st.session_state.categories[tb]:
            st.session_state.categories[tb].append(ns)
            st.session_state.selected_node = ("BRAND", tb, None)
            save_all()
            st.rerun()
        else:
            st.error("이미 존재하는 품목입니다.")

@st.dialog("⚙️ 카테고리 관리 및 순서 설정", width="large")
def manage_category_dialog():
    st.markdown("### 전시 방식 및 상세 카테고리 관리")
    if not st.session_state.categories:
        st.info("등록된 브랜드가 없습니다.")
        return
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📁 브랜드 관리")
        sel_b = st.selectbox("수정/삭제할 브랜드 선택", list(st.session_state.categories.keys()))
        if sel_b:
            new_b = st.text_input("이름 변경 (브랜드)", value=sel_b)
            c1, c2 = st.columns(2)
            if c1.button("✏️ 브랜드 수정", use_container_width=True):
                if new_b and new_b != sel_b and new_b not in st.session_state.categories:
                    st.session_state.categories[new_b] = st.session_state.categories.pop(sel_b)
                    for s, i in st.session_state.inventory.items():
                        if i.get('brand') == sel_b: i['brand'] = new_b
                    save_all(); st.rerun()
            if c2.button("🗑️ 브랜드 삭제", type="primary", use_container_width=True):
                to_del = [s for s, i in st.session_state.inventory.items() if i.get('brand') == sel_b]
                for s in to_del: del st.session_state.inventory[s]
                del st.session_state.categories[sel_b]
                st.session_state.selected_node = ("ALL", None, None)
                save_all(); st.rerun()
                
    with col2:
        st.markdown("#### 📄 품목 관리 및 순서 이동")
        if sel_b and st.session_state.categories[sel_b]:
            subs = st.session_state.categories[sel_b]
            sel_s = st.selectbox("수정/이동할 품목 선택", subs)
            if sel_s:
                new_s = st.text_input("이름 변경 (품목)", value=sel_s)
                c3, c4 = st.columns(2)
                if c3.button("✏️ 품목 수정", use_container_width=True):
                    if new_s and new_s != sel_s and new_s not in subs:
                        idx = subs.index(sel_s)
                        st.session_state.categories[sel_b][idx] = new_s
                        for s, i in st.session_state.inventory.items():
                            if i.get('brand') == sel_b and i.get('sub_category') == sel_s: i['sub_category'] = new_s
                        save_all(); st.rerun()
                if c4.button("🗑️ 품목 삭제", type="primary", use_container_width=True):
                    to_del = [s for s, i in st.session_state.inventory.items() if i.get('brand') == sel_b and i.get('sub_category') == sel_s]
                    for s in to_del: del st.session_state.inventory[s]
                    st.session_state.categories[sel_b].remove(sel_s)
                    st.session_state.selected_node = ("ALL", None, None)
                    save_all(); st.rerun()
                
                st.markdown("##### ↕️ 전시 순서 이동")
                arr1, arr2 = st.columns(2)
                idx = subs.index(sel_s)
                if arr1.button("🔼 위로 올리기", use_container_width=True) and idx > 0:
                    subs[idx], subs[idx-1] = subs[idx-1], subs[idx]
                    save_all(); st.rerun()
                if arr2.button("🔽 아래로 내리기", use_container_width=True) and idx < len(subs)-1:
                    subs[idx], subs[idx+1] = subs[idx+1], subs[idx]
                    save_all(); st.rerun()
        else:
            st.info("이 브랜드에는 등록된 품목이 없습니다.")

@st.dialog("📈 통계 및 분석 대시보드", width="large")
def stat_dialog():
    t1, t2, t3, t4 = st.tabs(["🏆 많이 팔린 제품", "⚠️ 재고 부족", "🏢 브랜드별 판매량", "📅 월별 판매량"])
    
    # 출고 데이터 미리 집계 (공통 사용)
    out_hist = [r for r in st.session_state.history if r['type'] == 'OUT']
    sku_sales = {}
    for r in out_hist: 
        sku_sales[r['sku']] = sku_sales.get(r['sku'], 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
        
    with t1:
        st.caption("💡 표의 컬럼 이름(예: 수량, 강성)을 클릭하시면 해당 기준으로 자동 정렬됩니다.")
        df1_data = []
        for k, v in sku_sales.items():
            info = st.session_state.inventory.get(k, {})
            df1_data.append({
                "SKU": k, "브랜드": info.get('brand', ''), "품목": info.get('sub_category', ''),
                "강성": info.get('flex', ''), "수량": v
            })
        df1 = pd.DataFrame(df1_data)
        if not df1.empty: 
            df1 = df1.sort_values(by="수량", ascending=False)
        st.dataframe(df1, use_container_width=True, hide_index=True)
        
    with t2:
        st.caption("💡 표의 컬럼 이름을 클릭하여 원하는 기준으로 정렬해보세요.")
        df2_data = []
        for sku, info in st.session_state.inventory.items():
            if info['quantity'] <= 2:
                df2_data.append({
                    "SKU": sku, "브랜드": info.get('brand', ''), "품목": info.get('sub_category', ''),
                    "강성": info.get('flex', ''), "현재수량": info['quantity'], "판매수량": sku_sales.get(sku, 0)
                })
        df2 = pd.DataFrame(df2_data)
        if not df2.empty: 
            df2 = df2.sort_values(by="현재수량", ascending=True)
        st.dataframe(df2, use_container_width=True, hide_index=True)
        
    with t3:
        b_sales = {}
        for r in out_hist: 
            b = r['brand'] if r['brand'] else "미분류"
            b_sales[b] = b_sales.get(b, 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
        df3 = pd.DataFrame(list(b_sales.items()), columns=["브랜드", "판매량"])
        if not df3.empty: 
            df3 = df3.sort_values(by="판매량", ascending=False)
        st.dataframe(df3, use_container_width=True, hide_index=True)
        
    with t4:
        st.caption("💡 해당 월이나 수량 컬럼을 클릭하여 정렬할 수 있습니다.")
        month_sku_sales = {}
        for r in out_hist: 
            m = r['time'][:7]
            key = (m, r['sku'])
            month_sku_sales[key] = month_sku_sales.get(key, 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
        
        df4_data = []
        for (m, s), v in month_sku_sales.items():
            info = st.session_state.inventory.get(s, {})
            df4_data.append({
                "해당 월": m, "SKU": s, "브랜드": info.get('brand', ''), 
                "품목": info.get('sub_category', ''), "강성": info.get('flex', ''), "수량": v
            })
        df4 = pd.DataFrame(df4_data)
        if not df4.empty: 
            df4 = df4.sort_values(by=["해당 월", "수량"], ascending=[False, False])
        st.dataframe(df4, use_container_width=True, hide_index=True)

# ================= 레이아웃 시작 =================
menu1, menu2, menu3 = st.columns([2, 2, 6])
with menu1:
    csv_data = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').to_csv(encoding='utf-8-sig')
    st.download_button("💾 엑셀(CSV) 전체 재고 저장", data=csv_data, file_name="재고현황.csv", use_container_width=True)
with menu2:
    if st.button("📈 통계 대시보드 열기", use_container_width=True): stat_dialog()
st.divider()

left_pane, right_pane = st.columns([1, 4])

# [좌측] 카테고리 트리 사이드바
with left_pane:
    st.markdown("### 📂 분류 폴더")
    
    for b, subs in st.session_state.categories.items():
        is_expanded = (st.session_state.selected_node[1] == b)
        
        with st.expander(f"📁 {b}", expanded=is_expanded):
            for s in subs:
                s_type = "primary" if st.session_state.selected_node == ("SUB", b, s) else "secondary"
                if st.button(f"└ 📄 {s}", key=f"btn_{b}_{s}", use_container_width=True, type=s_type):
                    if st.session_state.selected_node == ("SUB", b, s):
                        st.session_state.selected_node = ("ALL", None, None)
                    else:
                        st.session_state.selected_node = ("SUB", b, s)
                    st.rerun()
                    
    st.markdown("---")
    btn1, btn2, btn3 = st.columns(3)
    if btn1.button("브랜드+", help="새로운 브랜드를 추가합니다"): add_brand_dialog()
    if btn2.button("품목+", help="선택한 브랜드에 품목을 추가합니다"): add_sub_dialog()
    if btn3.button("관리/삭제", help="카테고리 수정 및 순서 이동"): manage_category_dialog()

# [우측] 메인 영역
with right_pane:
    c1, c2, c3 = st.columns([2, 4, 2])
    mode = c1.radio("작업 모드:", ["입고 (+)", "출고 (-)"], horizontal=True)
    
    with c2.form("scan_form", clear_on_submit=True):
        sc1, sc2 = st.columns([3, 1])
        barcode_input = sc1.text_input("바코드 스캔", label_visibility="collapsed", placeholder="[바코드 스캔 후 Enter]")
        submit_scan = sc2.form_submit_button("확인")
        
    if c3.button("➕ 신규 상품 등록", use_container_width=True): add_item_dialog()

    if submit_scan and barcode_input:
        code = barcode_input.strip()
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if code in st.session_state.inventory:
            item = st.session_state.inventory[code]
            if "입고" in mode:
                item['quantity'] += 1
                st.session_state.status_msg = f"✅ [{time_str}] [입고] '{code}' (+1)"
                st.session_state.history.append({"time": time_str, "type": "IN", "sku": code, "brand": item.get('brand',''), "sub_category": item.get('sub_category',''), "flex": item.get('flex',''), "change": "+1", "current_qty": item['quantity']})
            else:
                if item['quantity'] > 0:
                    item['quantity'] -= 1
                    st.session_state.status_msg = f"🚀 [{time_str}] [출고] '{code}' (-1)"
                    st.session_state.history.append({"time": time_str, "type": "OUT", "sku": code, "brand": item.get('brand',''), "sub_category": item.get('sub_category',''), "flex": item.get('flex',''), "change": "-1", "current_qty": item['quantity']})
                else:
                    st.session_state.status_msg = f"❌ [{time_str}] 재고 부족!"
            save_all()
        else:
            add_item_dialog(pre_filled=code)

    sc_res1, sc_res2 = st.columns([4, 1])
    sc_res1.info(st.session_state.status_msg)
    if sc_res2.button("↩️ 방금 스캔 취소", use_container_width=True):
        if st.session_state.history:
            last = st.session_state.history.pop()
            if last['sku'] in st.session_state.inventory:
                st.session_state.inventory[last['sku']]['quantity'] += (-1 if last['type'] == 'IN' else 1)
            save_all()
            st.session_state.status_msg = f"↩️ '{last['sku']}' 스캔 취소됨"
            st.rerun()

    tab_inv, tab_hist = st.tabs(["📦 재고 현황", "🕒 입출고 내역 (히스토리)"])
    
    with tab_inv:
        s1, s2 = st.columns([1, 4])
        # 💡 수정된 부분: 모델명(품목)과 브랜드를 검색 옵션에 추가
        s_type = s1.selectbox("검색 기준", ["SKU", "모델명(품목)", "브랜드", "강성", "메모"], label_visibility="collapsed")
        s_kw = s2.text_input("검색어", label_visibility="collapsed", placeholder="🔍 검색어 입력")
        
        df_inv = pd.DataFrame([{"SKU": k, "Brand": v.get('brand',''), "SubCat": v.get('sub_category',''), "Flex": v.get('flex',''), "Qty": v['quantity'], "Memo": v.get('memo','')} for k, v in st.session_state.inventory.items()])
        if not df_inv.empty:
            ntype, nbrand, nsub = st.session_state.selected_node
            if ntype == "SUB": df_inv = df_inv[(df_inv['Brand'] == nbrand) & (df_inv['SubCat'] == nsub)]
            
            # 💡 수정된 부분: 선택된 검색어에 따라 매핑하여 정확히 필터링
            if s_kw: 
                search_map = {"SKU": "SKU", "모델명(품목)": "SubCat", "브랜드": "Brand", "강성": "Flex", "메모": "Memo"}
                col_name = search_map[s_type]
                df_inv = df_inv[df_inv[col_name].str.contains(s_kw, case=False, na=False)]
            
            st.caption("💡 표 안의 'Memo' 칸을 더블클릭하면 엑셀처럼 바로 글씨를 수정할 수 있습니다.")
            edited_df = st.data_editor(df_inv, use_container_width=True, hide_index=True, disabled=["SKU", "Brand", "SubCat", "Flex", "Qty"])
            for idx, row in edited_df.iterrows():
                if st.session_state.inventory[row['SKU']].get('memo') != row['Memo']:
                    st.session_state.inventory[row['SKU']]['memo'] = row['Memo']
                    save_all()

    with tab_hist:
        h1, h2 = st.columns([1, 1])
        h_date = h1.date_input("📅 일자 조회")
        h_type = h2.selectbox("구분", ["전체", "IN", "OUT"])
        
        df_hist = pd.DataFrame(reversed(st.session_state.history))
        if not df_hist.empty:
            if h_date: df_hist = df_hist[df_hist['time'].str.startswith(str(h_date))]
            if h_type != "전체": df_hist = df_hist[df_hist['type'] == h_type]
            
            if not df_hist.empty:
                df_hist = df_hist.rename(columns={
                    "time": "날짜 및 시간", "type": "구분", "sku": "바코드 (SKU)",
                    "brand": "브랜드", "sub_category": "품목", "flex": "강성",
                    "change": "변동", "current_qty": "결과 재고"
                })
                df_hist = df_hist[["날짜 및 시간", "구분", "바코드 (SKU)", "브랜드", "품목", "강성", "변동", "결과 재고"]]
                
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("입출고 내역이 없습니다.")
