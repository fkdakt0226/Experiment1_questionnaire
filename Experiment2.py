import streamlit as st
import pandas as pd
import os
import gspread
from datetime import datetime
from google.oauth2 import service_account

scope = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
#credentials = service_account.Credentials.from_service_account_file("auto-reserve-367912-50ccc9b37e8f.json", scopes=scope)
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
gc = gspread.authorize(credentials)

SPREADSHEET_KEY = "16IwSCosz6aRv5IDU-0IQPqV9hVpgbMFh_Lz-dFxSQjI"
workbook = gc.open_by_key(SPREADSHEET_KEY)
ws_nasa = workbook.worksheet("NASA_EX2")
ws_sus = workbook.worksheet("SUS_EX2")

# ページ状態を管理
if "page" not in st.session_state:
    st.session_state["page"] = "nasa_tlx"

# 初期化（NASA-TLXスライダー用の状態保存）
if "nasa_answers" not in st.session_state:
    st.session_state["nasa_answers"] = {}

# 共通変数
nasa_questions = {
    "精神的負荷": ("知覚・思考・記憶などの要求", "どの程度の精神的・知覚的活動 (考える、決める、計算する、記憶する、見るなど)を求められましたか。この課題は簡単でしたか、それとも難しかったですか。単純でしたか複雑でしたか。", "小さい", "大きい"),
    "身体的負荷": ("身体の使用・動きの要求", "どの程度の身体的活動(押す，引く，回す，制御する，動き回るなど)を必要としましたか．作業は楽でしたか、それとも大変でしたか。ゆっくりできましたかキビキビやらなければなりませんでしたか，休み休みできましたか働きづめでしたか", "小さい", "大きい"),
    "時間的切迫感": ("タイムプレッシャー", "仕事のペースや課題が発生する頻度のために感じる時間的切迫感はどの程度でしたか．ペースはゆっくりとして余裕があるものでしたか，それとも速くて余裕のないものでしたか", "弱い", "強い"),
    "作業成績": ("目標達成度と満足度", "作業指示者(またはあなた自身)によって設定された課題の目標をどの程度達成できたと思いますか．目標の達成に関して自分の作業成績にどの程度満足していますか", "良い", "悪い"),
    "努力": ("成績の維持に必要だった努力の程度", "作業成績のレベルを達成・維持するために，精神的・身体的にどの程度いっしょうけんめいに作業しなければなりませんでしたか", "少ない", "多い"),
    "フラストレーション": ("不安・いら立ち・ストレスの程度", "作業中に，不安感，落胆，いらいら，ストレス，悩みをどの程度感じましたか．あるいは逆に，安心感，満足感，充足感，楽しさ，リラックスをどの程度感じましたか", "低い", "高い")
}

sus_questions = [
    "このシステムを頻繁に使用したい。",
    "このシステムは必要以上に複雑だと思う。",
    "このシステムはシンプルで使いやすい。",
    "このシステムを使うにはテクニカルサポートが必要。",
    "このシステムはスムーズに機能し、連携がとれていると思う。",
    "システムには不規則な点が多いと思う。",
    "ほとんどの人がこのシステムをすぐに習得できると思う。",
    "このシステムは時間がかかると思う。",
    "このシステムを使っていると、自信が持てる。",
    "このシステムを使い始める前に学ぶべきことはたくさんあると思う。"
]

# --- NASA-TLX ページ ---
if st.session_state["page"] == "nasa_tlx":
    st.title("NASA-TLX")

    # IDを保持していれば再利用
    respondent_id = st.text_input("参加者ID", value=st.session_state.get("respondent_id", ""))
    condition_options_nasa = ["1", "2", "3", "4", "5", "6", "7"]
    experiment_condition_nasa = st.selectbox("実験条件", condition_options_nasa)

    st.divider()
    st.header("主観的負荷評価")

    slider_results = {}
    for label, desc in nasa_questions.items():
        st.subheader(f"{label}：{desc[0]}")
        st.markdown(desc[1])
        # 保存済みがあればその値を初期値に
        default_val = st.session_state["nasa_answers"].get(label, 50)
        slider_results[label] = st.slider(
            f"{label}（0 = {desc[2]}, 100 = {desc[3]}）", 0, 100, default_val, key=f"slider_{label}"
        )
        st.write("")

    st.divider()
    if st.button("送信", key="nasa_submit"):
        if respondent_id == "":
            st.error("参加者IDを入力してください。")
        else:
            # セッションに保持
            st.session_state["respondent_id"] = respondent_id
            st.session_state["nasa_answers"] = slider_results
            st.session_state["experiment_condition"] = experiment_condition_nasa

            # 回答データ作成
            response_data = {
                "タイムスタンプ": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ID": respondent_id,
                "条件": experiment_condition_nasa
            }
            response_data.update(slider_results)

            sheet_headers_nasa = ws_nasa.row_values(1)
            new_row_nasa = [response_data.get(h, "") for h in sheet_headers_nasa]

            try:
                ws_nasa.append_row(new_row_nasa, value_input_option="USER_ENTERED")
                st.session_state["page"] = "nasa_done"
                st.rerun()
            except Exception as e:
                st.error(f"Google Sheetsへの保存中にエラーが発生しました: {e}")

# --- NASA回答完了ページ ---
elif st.session_state["page"] == "nasa_done":
    st.success("回答を保存しました。ありがとうございました！")
    st.markdown("以下のボタンで次のアンケートに進むか、回答を修正してください。")

    if st.button("👉 次のアンケートへ（SUS）"):
        st.session_state["page"] = "sus"
        st.rerun()

    # 🔁 回答修正ボタン
    if st.button("📝 回答を修正する（NASA-TLXに戻る）"):
        st.session_state["page"] = "nasa_tlx"
        st.rerun()


# --- SUSアンケートページ ---
elif st.session_state["page"] == "sus":
    st.title("System Usability Scale")

    # 直前の回答が session_state["sus_results"] にあるなら復元
    if "sus_results" in st.session_state:
        for i in range(10):
            key = f"sus_{i}"
            if key not in st.session_state:
                st.session_state[key] = st.session_state["sus_results"].get(f"Q{i+1}", 3)  # デフォルト3

    sus_id = st.text_input("参加者ID", value=st.session_state.get("respondent_id", ""))
    condition_options_sus = ["1", "2", "3", "4", "5", "6", "7"]
    experiment_condition_sus = st.selectbox(
        "実験条件",
        condition_options_sus,
        index=condition_options_sus.index(
            st.session_state.get("experiment_condition", "1")
        )
    )

    st.divider()

    sus_results = {}
    st.markdown("各質問に対して、1（全くそう思わない）〜5（非常にそう思う）の5段階で回答してください。")

    for i, q in enumerate(sus_questions):
        key = f"sus_{i}"
        sus_results[f"Q{i+1}"] = st.radio(
            q,
            [1, 2, 3, 4, 5],
            horizontal=True,
            key=key
        )
        st.write("")

    if st.button("送信", key="sus_submit"):
        if sus_id == "":
            st.error("参加者IDを入力してください。")
        else:
            sus_data = {
                "タイムスタンプ": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ID": sus_id,
                "条件": experiment_condition_sus
            }

            for i in range(10):
                sus_data[f"Q{i+1}"] = st.session_state.get(f"sus_{i}", 3)  # ← 回答値
            st.session_state["sus_results"] = {f"Q{i+1}": sus_data[f"Q{i+1}"] for i in range(10)}  # ✅ 保存
            sus_data.update(sus_results)

            sheet_headers_sus = ws_sus.row_values(1)
            new_row_sus = [sus_data.get(h, "") for h in sheet_headers_sus]

            try:
                ws_sus.append_row(new_row_sus, value_input_option="USER_ENTERED")
                st.session_state["page"] = "sus_done"
                st.rerun()
            except Exception as e:
                st.error(f"Google Sheetsへの保存中にエラーが発生しました: {e}")

# --- SUS回答完了ページ ---
elif st.session_state["page"] == "sus_done":
    st.success("回答を保存しました。ありがとうございました！")
    st.markdown("これで全てのアンケートは完了です。ウィンドウを閉じてください。")

    # 🔁 SUS回答修正ボタン
    if st.button("📝 回答を修正する（SUSに戻る）"):
        st.session_state["page"] = "sus"
        st.rerun()
