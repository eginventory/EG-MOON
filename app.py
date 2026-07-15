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

if 'inventory' not in st.session_state: st.session_state.inventory = load_json(DATA_FILE, {})
if 'categories' not in st.session_state: st.session_state.categories = load_json(CAT_FILE, {"미분류": ["기본"]})
if 'history' not in st.session_state: st.session_state.history = load_json(HISTORY_FILE, [])
if 'status_msg' not in st.session_state: st.session_state.status_msg = "대기 중..."

# ================= 팝업창(Toplevel) 완벽 구현 =================
@st.dialog("➕ 신규 상품 등록")
def add_item_dialog(pre_filled=""):
    st.warning("등록되지 않은 바코드입니다. 새로 등록하시겠습니까?" if pre_filled else "새로운 상품을 등록합니다.")
    brand = st.selectbox("1. 브랜드명", list(st.session_state.categories.keys()))
    sub_list = st.session_state.categories.get(brand, ["기본"])
    sub = st.selectbox("2. 품목(카테고리)", sub_list if sub_list else ["기본"])
    flex = st.text_input("3. 강성 (Flex)")
    loc = st.text_input("4. 보관 위치/칸")
    sku = st.text_input("5. 바코드 (SKU) *필수", value=pre_filled)
    
    if st.button("✅ 저장 및 등록", use_container_width=True):
        if not sku.strip(): st.error("바코드는 필수입니다.")
        elif sku.strip() in st.session_state.inventory: st.error("이미 등록된 바코드입니다.")
        else:
            st.session_state.inventory[sku.strip()] = {"brand": brand, "sub_category": sub, "flex": flex.strip(), "location": loc.strip(), "quantity": 0, "memo": ""}
            st.session_state.status_msg = f"✨ '{sku}' 등록 완료!"
            save_all()
            st.rerun()

@st.dialog("📈 통계 및 분석 대시보드", width="large")
def stat_dialog():
    t1, t2, t3, t4 = st.tabs(["🏆 많이 팔린 제품", "⚠️ 재고 부족", "🏢 브랜드별 판매량", "📅 월별 판매량"])
    out_hist = [r for r in st.session_state.history if r['type'] == 'OUT']
    
    with t1:
        sku_sales = {}
        for r in out_hist: sku_sales[r['sku']] = sku_sales.get(r['sku'], 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
        df1 = pd.DataFrame([{"SKU": k, "판매량": v, "브랜드": st.session_state.inventory.get(k, {}).get('brand', '')} for k, v in sorted(sku_sales.items(), key=lambda x: x[1], reverse=True)])
        st.dataframe(df1, use_container_width=True)
    with t2:
        low = [{"SKU": s, "브랜드": i.get('brand',''), "품목": i.get('sub_category',''), "재고": i['quantity']} for s, i in st.session_state.inventory.items() if i['quantity'] <= 2]
        st.dataframe(pd.DataFrame(low), use_container_width=True)
    with t3:
        b_sales = {}
        for r in out_hist: 
            b = r['brand'] if r['brand'] else "미분류"
            b_sales[b] = b_sales.get(b, 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
        st.dataframe(pd.DataFrame(list(b_sales.items()), columns=["브랜드", "판매량"]).sort_values("판매량", ascending=False), use_container_width=True)
    with t4:
        m_sales = {}
        for r in out_hist: 
            m = r['time'][:7]
            m_sales[m] = m_sales.get(m, 0) + abs(int(str(r['change']).replace('+','').replace('-','')))
        st.dataframe(pd.DataFrame(list(m_sales.items()), columns=["월(YYYY-MM)", "판매량"]).sort_values("월(YYYY-MM)", ascending=False), use_container_width=True)

@st.dialog("✏️ 폴더(카테고리) 수정 및 삭제")
def manage_category_dialog():
    st.info("이름 변경, 순서 이동, 삭제를 진행할 수 있습니다.")
    sel_b = st.selectbox("브랜드 선택", list(st.session_state.categories.keys()))
    sel_s = st.selectbox("품목 선택 (브랜드만 관리하려면 '전체' 선택)", ["전체"] + st.session_state.categories[sel_b])
    
    st.divider()
    new_name = st.text_input("새 이름", value=sel_s if sel_s != "전체" else sel_b)
    if st.button("이름 변경"):
        if sel_s == "전체" and new_name != sel_b:
            st.session_state.categories[new_name] = st.session_state.categories.pop(sel_b)
            for s, i in st.session_state.inventory.items():
                if i.get('brand') == sel_b: i['brand'] = new_name
        elif sel_s != "전체" and new_name != sel_s:
            idx = st.session_state.categories[sel_b].index(sel_s)
            st.session_state.categories[sel_b][idx] = new_name
            for s, i in st.session_state.inventory.items():
                if i.get('brand') == sel_b and i.get('sub_category') == sel_s: i['sub_category'] = new_name
        save_all(); st.rerun()

    if sel_s != "전체":
        c1, c2 = st.columns(2)
        lst = st.session_state.categories[sel_b]
        idx = lst.index(sel_s)
        if c1.button("▲ 순서 위로") and idx > 0:
            lst[idx], lst[idx-1] = lst[idx-1], lst[idx]
            save_all(); st.rerun()
        if c2.button("▼ 순서 아래로") and idx < len(lst)-1:
            lst[idx], lst[idx+1] = lst[idx+1], lst[idx]
            save_all(); st.rerun()

    st.divider()
    if st.button("🗑️ 선택 항목 삭제 (주의: 소속된 상품도 삭제됨)", type="primary"):
        to_del = [s for s, i in st.session_state.inventory.items() if i.get('brand') == sel_b and (sel_s == "전체" or i.get('sub_category') == sel_s)]
        for s in to_del: del st.session_state.inventory[s]
        if sel_s == "전체": del st.session_state.categories[sel_b]
        else: st.session_state.categories[sel_b].remove(sel_s)
        save_all(); st.rerun()

@st.dialog("📁 새 브랜드 추가")
def add_brand_dialog():
    nb = st.text_input("브랜드명")
    if st.button("추가") and nb:
        st.session_state.categories[nb] = ["기본"]
        save_all(); st.rerun()

@st.dialog("📄 새 품목 추가")
def add_sub_dialog():
    tb = st.selectbox("어느 브랜드에 추가할까요?", list(st.session_state.categories.keys()))
    ns = st.text_input("품목명")
    if st.button("추가") and ns:
        st.session_state.categories[tb].append(ns)
        save_all(); st.rerun()

# ================= 메인 UI 구성 시작 =================
st.set_page_config(layout="wide", page_title="스마트 재고 관리 시스템 v8.0")

# 1. 상단 메뉴바 (Tkinter 메뉴바 완벽 대체)
menu1, menu2, menu3 = st.columns([2, 2, 6])
with menu1:
    csv_data = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').to_csv(encoding='utf-8-sig')
    st.download_button("💾 엑셀(CSV) 전체 재고 저장", data=csv_data, file_name="재고현황.csv", use_container_width=True)
with menu2:
    if st.button("📈 통계 대시보드 열기", use_container_width=True): stat_dialog()
st.divider()

# 2. 좌/우 PanedWindow 분할 (Tkinter 화면 배치 완벽 복구)
left_pane, right_pane = st.columns([1, 4])

# [좌측] 카테고리 트리 사이드바
with left_pane:
    st.markdown("### 📂 분류 폴더")
    
    # Treeview 시각적 복구
    tree_opts = ["🌟 전체보기"]
    node_map = {"🌟 전체보기": ("ALL", None, None)}
    for b in st.session_state.categories.keys():
        b_node = f"📁 {b}"
        tree_opts.append(b_node)
        node_map[b_node] = ("BRAND", b, None)
        for s in st.session_state.categories[b]:
            s_node = f" └ 📄 {s} [{b}]"
            tree_opts.append(s_node)
            node_map[s_node] = ("SUB", b, s)
            
    selected_node = st.radio("트리 선택", tree_opts, label_visibility="collapsed")
    
    st.markdown("---")
    btn1, btn2, btn3 = st.columns(3)
    if btn1.button("브랜드+", help="브랜드 추가"): add_brand_dialog()
    if btn2.button("품목+", help="품목 추가"): add_sub_dialog()
    if btn3.button("관리/삭제", help="이름 변경, 순서 이동, 삭제"): manage_category_dialog()

# [우측] 메인 영역
with right_pane:
    # 상단 컨트롤 프레임 (입출고 및 바코드 스캔)
    c1, c2, c3 = st.columns([2, 4, 2])
    mode = c1.radio("작업 모드:", ["입고 (+)", "출고 (-)"], horizontal=True)
    
    with c2.form("scan_form", clear_on_submit=True):
        sc1, sc2 = st.columns([3, 1])
        barcode_input = sc1.text_input("바코드 스캔", label_visibility="collapsed", placeholder="[바코드 스캔 후 Enter]")
        submit_scan = sc2.form_submit_button("확인")
        
    if c3.button("➕ 신규 상품 등록", use_container_width=True): add_item_dialog()

    # 바코드 스캔 로직 처리
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
            add_item_dialog(pre_filled=code) # 미등록 바코드 스캔 시 팝업창 띄움

    # 스캔 결과 및 취소 버튼
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

    # Notebook 탭 영역
    tab_inv, tab_hist = st.tabs(["📦 재고 현황", "🕒 입출고 내역 (히스토리)"])
    
    with tab_inv:
        s1, s2 = st.columns([1, 4])
        s_type = s1.selectbox("검색 기준", ["SKU", "강성", "메모"], label_visibility="collapsed")
        s_kw = s2.text_input("검색어", label_visibility="collapsed", placeholder="🔍 검색어 입력")
        
        # 데이터 정리 및 필터링
        df_inv = pd.DataFrame([{"SKU": k, "Brand": v.get('brand',''), "SubCat": v.get('sub_category',''), "Flex": v.get('flex',''), "Qty": v['quantity'], "Memo": v.get('memo','')} for k, v in st.session_state.inventory.items()])
        if not df_inv.empty:
            ntype, nbrand, nsub = node_map[selected_node]
            if ntype == "BRAND": df_inv = df_inv[df_inv['Brand'] == nbrand]
            elif ntype == "SUB": df_inv = df_inv[(df_inv['Brand'] == nbrand) & (df_inv['SubCat'] == nsub)]
            if s_kw: df_inv = df_inv[df_inv[s_type].str.contains(s_kw, case=False, na=False)]
            
            # 메모 더블클릭 팝업 대신, 엑셀처럼 표에서 바로 더블클릭해서 수정하는 기능!
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
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
