import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# ================= 파일 경로 설정 =================
DATA_FILE = 'inventory_data.json'
CAT_FILE = 'category_data.json'
HISTORY_FILE = 'history_data.json'

# ================= 데이터 로드 및 저장 함수 =================
def load_json(filepath, default_type):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default_type
    return default_type

def save_all():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.inventory, f, ensure_ascii=False, indent=4)
    with open(CAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.categories, f, ensure_ascii=False, indent=4)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.history, f, ensure_ascii=False, indent=4)

# ================= 세션 상태(Session State) 초기화 =================
if 'inventory' not in st.session_state:
    st.session_state.inventory = load_json(DATA_FILE, {})
if 'categories' not in st.session_state:
    cats = load_json(CAT_FILE, {"미분류": ["기본"]})
    if not cats: cats = {"미분류": ["기본"]}
    st.session_state.categories = cats
if 'history' not in st.session_state:
    st.session_state.history = load_json(HISTORY_FILE, [])
if 'status_msg' not in st.session_state:
    st.session_state.status_msg = "대기 중..."

# ================= 메인 로직 함수 =================
def log_history(action_type, sku, item_info, qty_change, timestamp):
    record = {
        "time": timestamp, "type": action_type, "sku": sku,
        "brand": item_info.get('brand', ''), "sub_category": item_info.get('sub_category', ''),
        "flex": item_info.get('flex', ''), "change": qty_change, "current_qty": item_info['quantity']
    }
    st.session_state.history.append(record)
    if len(st.session_state.history) > 1000:
        st.session_state.history.pop(0)

def process_scan(barcode, mode):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if barcode in st.session_state.inventory:
        item = st.session_state.inventory[barcode]
        if mode == "IN":
            item['quantity'] += 1
            log_history("IN", barcode, item, "+1", current_time)
            st.session_state.status_msg = f"✅ [{current_time}] [입고] '{barcode}' (+1)"
        elif mode == "OUT":
            if item['quantity'] > 0:
                item['quantity'] -= 1
                log_history("OUT", barcode, item, "-1", current_time)
                st.session_state.status_msg = f"🚀 [{current_time}] [출고] '{barcode}' (-1)"
            else:
                st.session_state.status_msg = f"❌ [{current_time}] [오류] '{barcode}' 재고 0개!"
                st.error("재고가 부족합니다!")
                return
        save_all()
    else:
        st.session_state.status_msg = f"⚠️ [{current_time}] 미등록 바코드: {barcode}"
        st.warning("등록되지 않은 상품입니다. '신규 상품 등록' 탭에서 먼저 등록해주세요.")

def undo_last_scan():
    if not st.session_state.history:
        st.warning("취소할 스캔 내역이 없습니다.")
        return
    last_record = st.session_state.history.pop()
    sku = last_record['sku']
    action_type = last_record['type']
    cancel_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if sku in st.session_state.inventory:
        if action_type == 'IN': st.session_state.inventory[sku]['quantity'] -= 1
        elif action_type == 'OUT': st.session_state.inventory[sku]['quantity'] += 1
    
    save_all()
    st.session_state.status_msg = f"↩️ [{cancel_time}] [{action_type}] '{sku}' 스캔 취소완료"

# ================= 웹 UI 구성 시작 =================
st.set_page_config(page_title="스마트 재고 관리 시스템 v8.0", layout="wide")
st.title("📦 스마트 재고 관리 시스템 v8.0 (Web 완벽판)")

# --- [좌측] 카테고리 트리 사이드바 ---
with st.sidebar:
    st.header("📂 분류 폴더 관리")
    
    # 1. 브랜드 관리
    st.subheader("1. 브랜드")
    brand_list = list(st.session_state.categories.keys())
    selected_brand = st.selectbox("선택된 브랜드", brand_list)
    
    new_brand = st.text_input("새 브랜드 추가")
    if st.button("➕ 브랜드 추가"):
        if new_brand and new_brand not in st.session_state.categories:
            st.session_state.categories[new_brand] = ["기본"]
            save_all()
            st.rerun()
            
    col1, col2 = st.columns(2)
    rename_brand = col1.text_input("이름 변경", value=selected_brand, key="ren_b")
    if col1.button("✏️ 변경", key="btn_ren_b"):
        if rename_brand and rename_brand != selected_brand:
            st.session_state.categories[rename_brand] = st.session_state.categories.pop(selected_brand)
            for sku, info in st.session_state.inventory.items():
                if info.get('brand') == selected_brand: info['brand'] = rename_brand
            save_all(); st.rerun()
            
    if col2.button("🗑️ 삭제", key="btn_del_b"):
        if selected_brand != "미분류":
            # 연관 상품 삭제
            skus_to_delete = [sku for sku, info in st.session_state.inventory.items() if info.get('brand') == selected_brand]
            for sku in skus_to_delete: del st.session_state.inventory[sku]
            del st.session_state.categories[selected_brand]
            save_all(); st.rerun()

    st.divider()

    # 2. 품목(서브 카테고리) 관리
    st.subheader("2. 품목 (카테고리)")
    sub_list = st.session_state.categories.get(selected_brand, [])
    selected_sub = st.selectbox(f"[{selected_brand}]의 품목", sub_list if sub_list else [""])
    
    new_sub = st.text_input("새 품목 추가")
    if st.button("➕ 품목 추가"):
        if new_sub and new_sub not in sub_list:
            st.session_state.categories[selected_brand].append(new_sub)
            save_all(); st.rerun()

    col3, col4 = st.columns(2)
    rename_sub = col3.text_input("이름 변경", value=selected_sub, key="ren_s")
    if col3.button("✏️ 변경", key="btn_ren_s"):
        if rename_sub and rename_sub != selected_sub:
            idx = sub_list.index(selected_sub)
            st.session_state.categories[selected_brand][idx] = rename_sub
            for sku, info in st.session_state.inventory.items():
                if info.get('brand') == selected_brand and info.get('sub_category') == selected_sub:
                    info['sub_category'] = rename_sub
            save_all(); st.rerun()
            
    if col4.button("🗑️ 삭제", key="btn_del_s"):
        skus_to_delete = [sku for sku, info in st.session_state.inventory.items() if info.get('brand') == selected_brand and info.get('sub_category') == selected_sub]
        for sku in skus_to_delete: del st.session_state.inventory[sku]
        st.session_state.categories[selected_brand].remove(selected_sub)
        save_all(); st.rerun()

    # 순서 이동 (드래그 대체 기능)
    st.markdown("**(순서 변경)**")
    col5, col6 = st.columns(2)
    if col5.button("▲ 위로"):
        if selected_sub in sub_list:
            idx = sub_list.index(selected_sub)
            if idx > 0:
                sub_list[idx], sub_list[idx-1] = sub_list[idx-1], sub_list[idx]
                save_all(); st.rerun()
    if col6.button("▼ 아래로"):
        if selected_sub in sub_list:
            idx = sub_list.index(selected_sub)
            if idx < len(sub_list)-1:
                sub_list[idx], sub_list[idx+1] = sub_list[idx+1], sub_list[idx]
                save_all(); st.rerun()

# --- [상단] 스캔 및 컨트롤 영역 ---
with st.container():
    st.info(st.session_state.status_msg)
    col_scan1, col_scan2, col_scan3 = st.columns([2, 4, 1])
    
    with col_scan1:
        mode = st.radio("작업 모드", ["IN", "OUT"], horizontal=True, index=0)
    with col_scan2:
        with st.form("scan_form", clear_on_submit=True):
            cols_form = st.columns([4, 1])
            barcode_input = cols_form[0].text_input("바코드 스캔 (입력 후 Enter)", key="barcode")
            submitted = cols_form[1].form_submit_button("스캔")
            if submitted and barcode_input:
                process_scan(barcode_input.strip(), mode)
                st.rerun()
    with col_scan3:
        if st.button("↩️ 방금 스캔 취소", use_container_width=True):
            undo_last_scan()
            st.rerun()

st.divider()

# --- [메인] 탭 영역 (재고, 히스토리, 신규등록, 통계) ---
tab_inv, tab_hist, tab_add, tab_stat = st.tabs(["📦 재고 현황", "🕒 입출고 내역", "➕ 신규 상품 등록", "📈 통계 대시보드"])

# 1. 재고 현황 탭
with tab_inv:
    col_s1, col_s2, col_s3 = st.columns([1, 1, 3])
    search_type = col_s1.selectbox("검색 기준", ["SKU", "강성", "메모"])
    search_keyword = col_s2.text_input("검색어 입력")
    
    # 데이터프레임 생성
    inv_data = []
    for sku, info in st.session_state.inventory.items():
        inv_data.append({
            "SKU": sku, "Brand": info.get('brand', ''), "SubCat": info.get('sub_category', ''),
            "Flex": info.get('flex', ''), "Location": info.get('location', ''), 
            "Qty": info['quantity'], "Memo": info.get('memo', '')
        })
    df_inv = pd.DataFrame(inv_data)
    
    if not df_inv.empty:
        # 검색 필터 적용
        if search_keyword:
            if search_type == "SKU": df_inv = df_inv[df_inv['SKU'].str.contains(search_keyword, na=False, case=False)]
            elif search_type == "강성": df_inv = df_inv[df_inv['Flex'].str.contains(search_keyword, na=False, case=False)]
            elif search_type == "메모": df_inv = df_inv[df_inv['Memo'].str.contains(search_keyword, na=False, case=False)]
        
        # 사이드바 필터 연동 (전체보기가 아니면 해당 브랜드만)
        if selected_brand:
            df_inv = df_inv[df_inv['Brand'] == selected_brand]
        
        # 편집 가능한 테이블 (메모 더블클릭 수정 기능 완벽 대체)
        st.markdown("**💡 팁: 'Memo' 열을 더블클릭하면 엑셀처럼 바로 메모를 수정할 수 있습니다.**")
        edited_df = st.data_editor(df_inv, use_container_width=True, disabled=["SKU", "Brand", "SubCat", "Flex", "Location", "Qty"])
        
        # 메모 변경사항 자동 저장
        for index, row in edited_df.iterrows():
            sku = row['SKU']
            if sku in st.session_state.inventory and st.session_state.inventory[sku].get('memo') != row['Memo']:
                st.session_state.inventory[sku]['memo'] = row['Memo']
                save_all()
                
        # 엑셀(CSV) 저장 버튼
        csv = edited_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(label="💾 전체 재고 현황 CSV 다운로드", data=csv, file_name="재고현황.csv", mime="text/csv")
    else:
        st.info("등록된 재고가 없습니다.")

# 2. 히스토리 탭
with tab_hist:
    col_h1, col_h2 = st.columns([1, 1])
    filter_date = col_h1.date_input("일자 조회")
    filter_type = col_h2.selectbox("구분", ["전체", "IN", "OUT"])
    
    df_hist = pd.DataFrame(reversed(st.session_state.history))
    if not df_hist.empty:
        if filter_date:
            df_hist = df_hist[df_hist['time'].str.startswith(str(filter_date))]
        if filter_type != "전체":
            df_hist = df_hist[df_hist['type'] == filter_type]
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("히스토리 내역이 없습니다.")

# 3. 신규 상품 등록 탭 (기존 팝업창 대체)
with tab_add:
    st.subheader("새로운 상품 등록")
    with st.form("add_form", clear_on_submit=True):
        col_a1, col_a2 = st.columns(2)
        add_brand = col_a1.selectbox("1. 브랜드명", list(st.session_state.categories.keys()))
        add_sub = col_a2.selectbox("2. 품목(카테고리)", st.session_state.categories.get(add_brand, ["기본"]) if st.session_state.categories.get(add_brand) else ["기본"])
        
        add_flex = col_a1.text_input("3. 강성 (Flex)")
        add_loc = col_a2.text_input("4. 보관 위치/칸")
        add_sku = st.text_input("5. 바코드 (SKU) *필수")
        
        submitted_add = st.form_submit_button("✅ 저장 및 등록")
        if submitted_add:
            if not add_sku.strip():
                st.error("바코드는 필수 입력 사항입니다.")
            elif add_sku.strip() in st.session_state.inventory:
                st.error("이미 등록된 바코드입니다.")
            else:
                st.session_state.inventory[add_sku.strip()] = {
                    "brand": add_brand, "sub_category": add_sub, "flex": add_flex.strip(),
                    "location": add_loc.strip(), "quantity": 0, "memo": ""
                }
                save_all()
                st.success(f"'{add_sku}' 등록이 완료되었습니다! 재고 탭에서 확인하세요.")
                st.session_state.status_msg = f"✨ 신규 등록 완료: {add_sku}"

# 4. 통계 대시보드 탭 (기존 팝업창 대체)
with tab_stat:
    st.subheader("📈 통계 및 분석 대시보드")
    out_history = [rec for rec in st.session_state.history if rec['type'] == 'OUT']
    
    col_st1, col_st2 = st.columns(2)
    
    with col_st1:
        st.markdown("#### 🏆 많이 팔린 제품 (출고 기준)")
        sku_sales = {}
        for rec in out_history:
            sku = rec['sku']
            change = abs(int(str(rec['change']).replace('+','').replace('-','')))
            sku_sales[sku] = sku_sales.get(sku, 0) + change
        sorted_skus = sorted(sku_sales.items(), key=lambda x: x[1], reverse=True)
        top_df = pd.DataFrame([{"SKU": k, "판매량": v, "브랜드": st.session_state.inventory.get(k, {}).get('brand', '')} for k, v in sorted_skus])
        st.dataframe(top_df, use_container_width=True)

        st.markdown("#### 🏢 브랜드별 누적 판매량")
        brand_sales = {}
        for rec in out_history:
            b = rec['brand'] if rec['brand'] else "미분류"
            c = abs(int(str(rec['change']).replace('+','').replace('-','')))
            brand_sales[b] = brand_sales.get(b, 0) + c
        b_df = pd.DataFrame(list(brand_sales.items()), columns=["브랜드", "판매량"]).sort_values(by="판매량", ascending=False)
        st.dataframe(b_df, use_container_width=True)

    with col_st2:
        st.markdown("#### ⚠️ 재고 부족 경고 (2개 이하)")
        low_stock = []
        for sku, info in st.session_state.inventory.items():
            if info['quantity'] <= 2:
                low_stock.append({"SKU": sku, "브랜드": info.get('brand',''), "품목": info.get('sub_category',''), "재고": info['quantity']})
        st.dataframe(pd.DataFrame(low_stock), use_container_width=True)

        st.markdown("#### 📅 월별 누적 판매량")
        month_sales = {}
        for rec in out_history:
            m = rec['time'][:7]
            c = abs(int(str(rec['change']).replace('+','').replace('-','')))
            month_sales[m] = month_sales.get(m, 0) + c
        m_df = pd.DataFrame(list(month_sales.items()), columns=["월 (YYYY-MM)", "판매량"]).sort_values(by="월 (YYYY-MM)", ascending=False)
        st.dataframe(m_df, use_container_width=True)
