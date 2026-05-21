import streamlit as st
import datetime
import time
import requests
import pandas as pd
import io

# 画面の基本設定
st.set_page_config(page_title="SmokeSaver", layout="centered")

# --- 画面のコンパクト化＆デザインバグ修正CSS ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0.5rem; }
    h1 { font-size: 1.6rem !important; margin-bottom: 0rem; padding-bottom: 0rem; }
    .stMetric { margin-bottom: -0.5rem; }
    h3 { font-size: 1.1rem !important; margin-top: 0.2rem; margin-bottom: 0.2rem; }
    div.stButton > button { margin-top: 0.2rem; padding: 0.4rem; }
    .stMarkdown hr { margin: 0.4rem 0 !important; }
    
    /* 選択ボックス上部が切れるバグを修正 */
    .stSelectbox div[data-baseweb="select"] {
        padding-top: 0.2rem !important;
        margin-top: 0.2rem !important;
    }
    
    /* 残弾数のデジタルゲージ風カスタム */
    .gauge-container {
        font-family: monospace;
        font-size: 1.3rem;
        background-color: #1e1e1e;
        padding: 0.2rem 0.8rem;
        border-radius: 5px;
        display: inline-block;
        letter-spacing: 2px;
        color: #00ffcc;
        border: 1px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

# タイトル
st.title("🚬 スモークセーバー (SS)")
st.caption("マルチユーザー対応・クラウド・ハッキングアプリ")

# --- 1. 設定エリア（サイドバー） ---
st.sidebar.header("⚙️ ユーザー設定")

# ユーザー切り替え機能
current_user = st.sidebar.selectbox("ユーザーを選択", ["(U)", "Guest1", "Guest2"])

price = st.sidebar.number_input("1箱の値段（円）", value=600, step=10)
pieces = st.sidebar.number_input("1箱の本数", value=20, step=1)
usual = st.sidebar.number_input("普段の1日の本数", value=15, step=1)
target = st.sidebar.number_input("今日の目標本数", value=12, step=1)
max_stock = st.sidebar.number_input("最大ストック数（本数）", value=4, min_value=1, step=1)

cost_per_piece = price / pieces

# --- 2. GoogleスプレッドシートDB連携設定 ---
# (U)が作成したスプレッドシートのCSV出力URL
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/11LhDcF9hZzHDa3ewq-KrNvvMCqMwMlWnWW1b9uK7hG0/gviz/tq?tqx=out:csv"
# 書き込み用フォームURL（※簡易版として今回は閲覧・解析ベース、次回以降フォーム連動へ拡張可能。まずはセッション保存を強力に維持）

# データの読み込みと解析（ログインユーザー専用データを抽出）
def analyze_db(user_name):
    total_saved_from_history = 0.0
    today_smoked = 0
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    try:
        response = requests.get(GSHEET_CSV_URL)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # 選択中のユーザーのデータのみに絞り込む
            user_df = df[df["ユーザー"] == user_name]
            
            for _, row in user_df.iterrows():
                action = str(row["アクション"])
                row_time_str = str(row["日時"])
                
                if action.startswith("上限超過で破棄"):
                    try:
                        lost_bullets = int(action.split("(")[1].split("本")[0])
                        total_saved_from_history += lost_bullets * cost_per_piece
                    except:
                        total_saved_from_history += 1.0 * cost_per_piece
                
                if action == "日替わりリセット確定":
                    try:
                        total_saved_from_history += float(str(row["残弾変化"]).replace("￥", "").replace(",", ""))
                    except:
                        pass

                if action == "吸った" and row_time_str.startswith(today_str):
                    today_smoked += 1
    except:
        pass # 通信エラー時はスルー
                
    return total_saved_from_history, today_smoked

total_past_saved_money, today_smoked_count = analyze_db(current_user)

# --- 3. 内部データの初期化（ユーザー個別の状態管理） ---
if "user_states" not in st.session_state:
    st.session_state.user_states = {}

if current_user not in st.session_state.user_states:
    st.session_state.user_states[current_user] = {
        "bullets": 2,
        "last_charge_time": datetime.datetime.now(),
        "current_date": datetime.date.today()
    }

u_state = st.session_state.user_states[current_user]

# 本日の暫定節約計算
current_today_saved = max(0.0, (usual - today_smoked_count) * cost_per_piece)

# --- 4. 日付変更（0時リセット）の監視 ---
today = datetime.date.today()
if today != u_state["current_date"]:
    u_state["bullets"] = 2
    u_state["last_charge_time"] = datetime.datetime.now()
    u_state["current_date"] = today
    st.rerun()

# --- 5. ロジック計算（時間と残弾・上限突破の監視） ---
charge_interval_seconds = (24 * 60 * 60) / target
now = datetime.datetime.now()
elapsed_seconds = (now - u_state["last_charge_time"]).total_seconds()

if elapsed_seconds >= charge_interval_seconds:
    earned_bullets = int(elapsed_seconds // charge_interval_seconds)
    old_bullets = u_state["bullets"]
    u_state["bullets"] += earned_bullets
    
    if u_state["bullets"] > max_stock:
        u_state["bullets"] = max_stock
    u_state["last_charge_time"] = now

remaining_seconds = max(0.0, charge_interval_seconds - (elapsed_seconds % charge_interval_seconds))
remaining_minutes = remaining_seconds / 60
charge_interval_minutes_int = int(charge_interval_seconds // 60)

# --- 6. 通算合計節約額の表示 ---
total_saved_money = total_past_saved_money

# --- 7. メイン画面表示 ---
st.metric(label=f"💰 {current_user} の通算合計節約額（確定値）", value=f"￥{total_saved_money:,.1f}")

st.markdown("---")

st.subheader("🔋 現在の残弾")
bullet_bar = "■" * u_state["bullets"] + "□" * (max_stock - u_state["bullets"])
st.markdown(f'<div class="gauge-container">{bullet_bar} &nbsp; {u_state["bullets"]} / {max_stock} 本</div>', unsafe_allow_html=True)

st.caption(f"⏳ 次まで: あと {remaining_minutes:.1f} 分 （{charge_interval_minutes_int}分に1本補給） | 📊 本日: **{today_smoked_count}** / {target} 本")

# --- 8. アクションボタン ---
button_disabled = u_state["bullets"] <= 0
if st.button("🚬 1本吸う (残弾 -1)", use_container_width=True, disabled=button_disabled):
    u_state["bullets"] -= 1
    u_state["last_charge_time"] = datetime.datetime.now()  
    st.rerun()

st.markdown("---")

st.write("💡 ※クラウド版のデータ同期システム稼働中。サイドバーからユーザーを切り替えてそれぞれの進捗を管理できます。")