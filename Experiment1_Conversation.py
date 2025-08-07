import streamlit as st
import pandas as pd
import gspread
import random
import pytz
from datetime import datetime
from google.oauth2 import service_account

# ページ設定
st.set_page_config(page_title="会話理解度テスト", layout="wide")

# 認証とスプレッドシート取得
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
gc = gspread.authorize(credentials)
SPREADSHEET_KEY = "1f9KsFCKZVXo28Hc-JbcSszrZ2GiKm-NnlidgLTH8Ktg"
workbook = gc.open_by_key(SPREADSHEET_KEY)

# 設問データ読み込み
@st.cache_data
def load_question_data():
    ws_Q = workbook.worksheet("Question")
    data = ws_Q.get_all_records()
    return pd.DataFrame(data)

df = load_question_data()

# 設問取得関数（ランダム）
def get_questions_from_wide_row(df, set_name):
    row = df[df["Set"] == set_name]
    if row.empty:
        return []
    questions = row.iloc[0, 1:].tolist()
    question_dicts = [{"QID": i + 1, "Question": q} for i, q in enumerate(questions)]
    random.shuffle(question_dicts)
    return question_dicts

# Google Sheets への書き込み
def write_answers_to_google_sheets(respondent_id, experiment_condition, set_names, questions_sets, responses, workbook):
    JST = pytz.timezone("Asia/Tokyo")
    timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

    for set_name, questions in zip(set_names, questions_sets):
        try:
            sheet = workbook.worksheet(set_name)
        except:
            st.error(f"シート '{set_name}' が見つかりませんでした。")
            continue

        questions_sorted = sorted(questions, key=lambda x: x["QID"])
        answers = [responses.get(f"{set_name}_{q['QID']}", "") for q in questions_sorted]
        row = [timestamp, respondent_id, experiment_condition] + answers
        sheet.append_row(row, value_input_option="USER_ENTERED")

# --- UI開始 ---
st.title("会話理解度テスト")

respondent_id = st.text_input("参加者ID", value=st.session_state.get("respondent_id", ""))
experiment_condition = st.selectbox("実験条件", ["0", "1", "2", "3", "4", "5", "6"])
st.divider()

# 設問セット選択
col1, col2, col3 = st.columns(3)
with col1:
    set1 = st.selectbox("設問セット①", [""] + ["C1", "C2", "C3", "C4", "C5", "C6"], key="set1")
with col2:
    set2 = st.selectbox("設問セット②", [""] + ["C7", "C8", "C9", "C10", "C11", "C12", "B"], key="set2")
with col3:
    set3 = st.selectbox("設問セット③", [""] + ["C13", "C14", "C15", "C16", "C17", "C18"], key="set3")

# 初回 or セットが変更された場合のみ再取得
if "set1_prev" not in st.session_state or st.session_state.set1 != st.session_state.set1_prev:
    st.session_state.questions1 = get_questions_from_wide_row(df, st.session_state.set1) if st.session_state.set1 else []
    st.session_state.set1_prev = st.session_state.set1

if "set2_prev" not in st.session_state or st.session_state.set2 != st.session_state.set2_prev:
    st.session_state.questions2 = get_questions_from_wide_row(df, st.session_state.set2) if st.session_state.set2 else []
    st.session_state.set2_prev = st.session_state.set2

if "set3_prev" not in st.session_state or st.session_state.set3 != st.session_state.set3_prev:
    st.session_state.questions3 = get_questions_from_wide_row(df, st.session_state.set3) if st.session_state.set3 else []
    st.session_state.set3_prev = st.session_state.set3

questions1 = st.session_state.get("questions1", [])
questions2 = st.session_state.get("questions2", [])
questions3 = st.session_state.get("questions3", [])

# 回答保存用 state 初期化
if "responses" not in st.session_state:
    st.session_state.responses = {}

# 質問表示関数
def show_questions(col, questions, col_name):
    with col:
        for q in questions:
            qid = f"{col_name}_{q['QID']}"
            st.session_state.responses[qid] = st.radio(
                f"{q['Question']}",
                options=["はい", "いいえ", "わからない"],
                key=qid
            )

# 選択されている列のみ表示
c1, c2, c3 = st.columns(3)
if st.session_state.set1:
    show_questions(c1, questions1, st.session_state.set1)
if st.session_state.set2:
    show_questions(c2, questions2, st.session_state.set2)
if st.session_state.set3:
    show_questions(c3, questions3, st.session_state.set3)

# 送信ボタンと処理
st.markdown("---")
if st.button("送信"):
    all_qs = []
    sets_used = []
    questions_used = []

    if st.session_state.set1:
        sets_used.append(st.session_state.set1)
        questions_used.append(questions1)
        all_qs.extend(questions1)
    if st.session_state.set2:
        sets_used.append(st.session_state.set2)
        questions_used.append(questions2)
        all_qs.extend(questions2)
    if st.session_state.set3:
        sets_used.append(st.session_state.set3)
        questions_used.append(questions3)
        all_qs.extend(questions3)

    for q in all_qs:
        q["Set"] = [s for s, qlist in zip(sets_used, questions_used) if q in qlist][0]

    results = []
    for q in all_qs:
        qid = f"{q['Set']}_{q['QID']}"
        results.append({
            "RespondentID": respondent_id,
            "Set": q["Set"],
            "QID": q["QID"],
            "Question": q["Question"],
            "Answer": st.session_state.responses.get(qid, "")
        })

    st.success("送信が完了しました。")

    write_answers_to_google_sheets(
        respondent_id=respondent_id,
        experiment_condition=experiment_condition,
        set_names=sets_used,
        questions_sets=questions_used,
        responses=st.session_state.responses,
        workbook=workbook
    )
