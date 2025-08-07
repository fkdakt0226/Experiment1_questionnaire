import streamlit as st
import pandas as pd
import gspread
import random
from datetime import datetime, timedelta, timezone
from itertools import combinations
from google.oauth2 import service_account

# --- 認証 ---
scope = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_file("auto-reserve-367912-50ccc9b37e8f.json", scopes=scope)
#credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
gc = gspread.authorize(credentials)

SPREADSHEET_KEY = "16IwSCosz6aRv5IDU-0IQPqV9hVpgbMFh_Lz-dFxSQjI"
workbook = gc.open_by_key(SPREADSHEET_KEY)
ws = workbook.worksheet("NASA_W_EX1")

JST = timezone(timedelta(hours=9))

# --- 定義 ---
scales = ["精神的負荷", "身体的負荷", "時間的切迫感", "作業成績", "努力", "フラストレーション"]
if "question_order" not in st.session_state:
    st.session_state.question_order = random.sample(list(combinations(scales, 2)), k=15)
    st.session_state.current = 0
    st.session_state.responses = []
    st.session_state.user_id = ""
    st.session_state.timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

# --- UI ---
st.title("NASA-TLX：2択比較")
if st.session_state.current == 0:
    st.session_state.user_id = st.text_input("参加者IDを入力してください", value=st.session_state.user_id)
    if st.session_state.user_id == "":
        st.stop()

# --- 質問表示 ---
if st.session_state.current < len(st.session_state.question_order):
    original_pair = st.session_state.question_order[st.session_state.current]
    options = list(original_pair)
    random.shuffle(options)  # ← 並びをランダムに

    a, b = options
    st.write(f"Q{st.session_state.current + 1}：次のうち、より負荷が大きかったのはどちらですか？")
    col1, col2 = st.columns(2)
    if col1.button(a):
        st.session_state.responses.append(a)
        st.session_state.current += 1
        st.rerun()
    if col2.button(b):
        st.session_state.responses.append(b)
        st.session_state.current += 1
        st.rerun()
else:
    # 回答完了
    st.success("全ての質問に回答しました。ありがとうございました！")
    result = {
        "タイムスタンプ": st.session_state.timestamp,
        "ID": st.session_state.user_id
    }

    # すべてのスケール組み合わせ（順序に依存しない）
    combination_to_index = {
        frozenset(["精神的負荷", "身体的負荷"]): 1,
        frozenset(["精神的負荷", "時間的切迫感"]): 2,
        frozenset(["精神的負荷", "作業成績"]): 3,
        frozenset(["精神的負荷", "努力"]): 4,
        frozenset(["精神的負荷", "フラストレーション"]): 5,
        frozenset(["身体的負荷", "時間的切迫感"]): 6,
        frozenset(["身体的負荷", "作業成績"]): 7,
        frozenset(["身体的負荷", "努力"]): 8,
        frozenset(["身体的負荷", "フラストレーション"]): 9,
        frozenset(["時間的切迫感", "作業成績"]): 10,
        frozenset(["時間的切迫感", "努力"]): 11,
        frozenset(["時間的切迫感", "フラストレーション"]): 12,
        frozenset(["作業成績", "努力"]): 13,
        frozenset(["作業成績", "フラストレーション"]): 14,
        frozenset(["努力", "フラストレーション"]): 15
    }

    # 回答に基づいて列に配置
    answers_dict = {}
    for i, (a, b) in enumerate(st.session_state.question_order):
        chosen = st.session_state.responses[i]
        key = frozenset([a, b])
        col_index = combination_to_index.get(key)
        if col_index:
            answers_dict[str(col_index)] = chosen

    # ヘッダーに合わせて新しい行を作成
    headers = ws.row_values(1)
    new_row = [result.get(h, answers_dict.get(h, "")) for h in headers]

    # Google Sheets に保存
    ws.append_row(new_row, value_input_option="USER_ENTERED")
    st.write("回答結果が保存されました。")