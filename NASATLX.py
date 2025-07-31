import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ページ状態を管理
if "page" not in st.session_state:
    st.session_state["page"] = "nasa_tlx"

# 初期化（NASA-TLXスライダー用の状態保存）
if "nasa_answers" not in st.session_state:
    st.session_state["nasa_answers"] = {}

# 共通変数
nasa_questions = {
    "精神的負荷": ("知覚・思考・記憶などの要求", "どの程度の精神的・知覚的活動 (考える、決める、計算する...) を求められましたか。", "小さい", "大きい"),
    "身体的負荷": ("身体の使用・動きの要求", "どの程度の身体的活動を必要としましたか。", "小さい", "大きい"),
    "時間的切迫感": ("時間的プレッシャー", "時間的な余裕はありましたか？", "弱い", "強い"),
    "作業成績": ("目標達成度と満足度", "どの程度目標を達成できたと思いますか？", "良い", "悪い"),
    "努力": ("成績を維持するための努力", "どの程度努力が必要でしたか？", "少ない", "多い"),
    "フラストレーション": ("ストレス、不安、いらいら", "どの程度ストレスやいらいらを感じましたか？", "低い", "高い")
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
    condition_options = ["1", "2", "3", "4", "5", "6", "7"]
    experiment_condition = st.selectbox("実験条件", condition_options)

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

            # CSVの読み込みと上書き
            file_path = "responses_nasa.csv"
            # 回答データ作成
            response_data = {
                "タイムスタンプ": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ID": respondent_id,
                "条件ID": experiment_condition
            }
            response_data.update(slider_results)
            df_new = pd.DataFrame([response_data])

            # 「タイムスタンプを除いた行」をセッションに保存（次回削除の比較に使う）
            st.session_state["last_nasa_row_no_ts"] = {k: v for k, v in response_data.items() if k != "タイムスタンプ"}

            # 保存処理
            if os.path.exists(file_path):
                df_existing = pd.read_csv(file_path)
                # 🔻 削除処理を削除：そのまま既存データに新しい1行を追加
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new

            # 保存
            df_combined.to_csv(file_path, index=False)

            st.session_state["page"] = "nasa_done"
            st.rerun()

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

    sus_id = st.text_input("参加者ID", value=st.session_state.get("respondent_id", ""))
    st.divider()

    sus_results = {}
    st.markdown("各質問に対して、1（全くそう思わない）〜5（非常にそう思う）の5段階で回答してください。")

    for i, q in enumerate(sus_questions):
        sus_results[f"Q{i+1}"] = st.radio(q, [1, 2, 3, 4, 5], horizontal=True, key=f"sus_{i}")
        st.write("")

    if st.button("送信", key="sus_submit"):
        if sus_id == "":
            st.error("参加者IDを入力してください。")
        else:
            sus_data = {
                "タイムスタンプ": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ID": sus_id
            }
            sus_data.update(sus_results)

            file_path = "responses_sus.csv"
            df_new = pd.DataFrame([sus_data])
            if os.path.exists(file_path):
                df_existing = pd.read_csv(file_path)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new
            df_combined.to_csv(file_path, index=False)

            # ✅ SUS送信後の完了画面へ遷移
            st.session_state["page"] = "sus_done"
            st.rerun()

# --- SUS回答完了ページ ---
elif st.session_state["page"] == "sus_done":
    st.success("回答を保存しました。ありがとうございました！")
    st.markdown("これで全てのアンケートは完了です。ウィンドウを閉じてください。")