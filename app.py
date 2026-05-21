import streamlit as st
import datetime
import time
import os
import csv
import pandas as pd

# 画面の基本設定
st.set_page_config(page_title="SmokeSaver", layout="centered")

# --- 画面のコンパクト化＆文字化け防止CSS調整 ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0.5rem; }
    h1 { font-size: 1.6rem !important; margin-bottom: 0rem; padding-bottom: 0rem; }
    .stMetric { margin-bottom: -0.5rem; }
    h3 { font-size: 1.1rem !important; margin-top: 0.2rem; margin-bottom: 0.2rem; }
    div.stButton > button { margin-top: 0.2rem; padding: 0.4rem; }
    .stMarkdown hr { margin: 0.4rem 0 !important; }
    
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
st.caption("(U) 専用アイコス・ハッキングアプリ")

# --- 1. 設定エリア（サイドバー） ---
st.sidebar.header("⚙️ 基本設定")
price = st.sidebar.number_input("1箱の値段（円）", value=600, step=10)
pieces = st.sidebar.number_input("1箱の本数", value=20, step=1)
usual = st.sidebar.number_input("普段の1日の本数", value=15, step=1)
target = st.sidebar.number_input("今日の目標本数", value=12, step=1)
max_stock = st.sidebar.number_input("最大ストック数（本数）", value=4, min_value=1, step=1)

cost_per_piece = price / pieces

# --- 2. データ保存（CSV）の準備と解析 ---
CSV_FILE = "history.csv"

def init_csv():
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["日時", "アクション", "残弾変化", "その日の節約額"])
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "アプリ開始", "0", "￥0.0"])

if not os.path.exists(CSV_FILE):
    init_csv()
else:
    with open(CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        if "その日の節約額" not in header:
            init_csv()

# CSVの履歴から「溢れた回数」と「日替わりで確定した過去の節約額」を厳密に集計
def analyze_history_for_savings():
    total_saved_from_history = 0.0
    today_smoked = 0
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    with open(CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  
        for row in reader:
            if not row:
                continue
            row_time_str = row[0]
            action = row[1]
            
            # 1. ストック上限を超えて溢れた弾のカウント
            if action.startswith("上限超過で破棄"):
                try:
                    lost_bullets = int(action.split("(")[1].split("本")[0])
                    total_saved_from_history += lost_bullets * cost_per_piece
                except:
                    total_saved_from_history += 1.0 * cost_per_piece
            
            # 2. 過去の日付変更リセット時に確定した節約額の加算
            if action == "日替わりリセット確定":
                try:
                    # 残弾変化の列に記録された金額を取得
                    saved_val = float(row[2].replace("￥", "").replace(",", ""))
                    total_saved_from_history += saved_val
                except:
                    pass

            if action == "吸った" and row_time_str.startswith(today_str):
                today_smoked += 1
                
    return total_saved_from_history, today_smoked

total_past_saved_money, today_smoked_count = analyze_history_for_savings()

# --- 3. 内部データの初期化（セッション記憶） ---
if "bullets" not in st.session_state:
    st.session_state.bullets = 2  
if "last_charge_time" not in st.session_state:
    st.session_state.last_charge_time = datetime.datetime.now()
if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.date.today()

# 本日の暫定節約計算（普段の本数 - 本日吸った本数）
current_today_saved = max(0.0, (usual - today_smoked_count) * cost_per_piece)

# --- 4. 日付変更（0時リセット）の監視 ---
today = datetime.date.today()
if today != st.session_state.current_date:
    # 日付が変わった瞬間、昨日浮いた分の金額を確定させてログに残す
    log_action("日替わりリセット確定", f"￥{current_today_saved:,.1f}", current_today_saved)
    
    st.session_state.bullets = 2
    st.session_state.last_charge_time = datetime.datetime.now()
    st.session_state.current_date = today
    st.rerun()

def log_action(action, bullet_change, current_day_saved_money):
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            action, 
            bullet_change, 
            f"￥{current_day_saved_money:,.1f}"
        ])

# --- 5. ロジック計算（時間と残弾・上限突破の監視） ---
charge_interval_seconds = (24 * 60 * 60) / target
now = datetime.datetime.now()
elapsed_seconds = (now - st.session_state.last_charge_time).total_seconds()

if elapsed_seconds >= charge_interval_seconds:
    earned_bullets = int(elapsed_seconds // charge_interval_seconds)
    old_bullets = st.session_state.bullets
    st.session_state.bullets += earned_bullets
    
    # 上限を超えた場合の処理
    if st.session_state.bullets > max_stock:
        overflow_bullets = st.session_state.bullets - max_stock
        st.session_state.bullets = max_stock
        # 上限を超えて消滅した本数を明確に記録（これでガツンと金額が増える）
        log_action(f"上限超過で破棄({overflow_bullets}本)", f"±0", current_today_saved)
    else:
        actual_earned = st.session_state.bullets - old_bullets
        if actual_earned > 0:
            log_action("自動チャージ", f"+{actual_earned}", current_today_saved)
            
    st.session_state.last_charge_time = now

remaining_seconds = max(0.0, charge_interval_seconds - (elapsed_seconds % charge_interval_seconds))
remaining_minutes = remaining_seconds / 60
charge_interval_minutes_int = int(charge_interval_seconds // 60)

# --- 6. 通算合計節約額の確定値表示 ---
# 「過去の確定節約額」を表示する（じわじわ増えない）
total_saved_money = total_past_saved_money

# --- 7. メイン画面表示 ---
st.metric(label="💰 これまでの通算合計節約額（確定値）", value=f"￥{total_saved_money:,.1f}")

st.markdown("---")

st.subheader("🔋 現在の残弾")
bullet_bar = "■" * st.session_state.bullets + "□" * (max_stock - st.session_state.bullets)
st.markdown(f'<div class="gauge-container">{bullet_bar} &nbsp; {st.session_state.bullets} / {max_stock} 本</div>', unsafe_allow_html=True)

st.caption(f"⏳ 次まで: あと {remaining_minutes:.1f} 分 （{charge_interval_minutes_int}分に1本補給） | 📊 本日: **{today_smoked_count}** / {target} 本")

# --- 8. アクションボタン ---
button_disabled = st.session_state.bullets <= 0
if st.button("🚬 1本吸う (残弾 -1)", use_container_width=True, disabled=button_disabled):
    st.session_state.bullets -= 1
    new_today_saved = max(0.0, (usual - (today_smoked_count + 1)) * cost_per_piece)
    log_action("吸った", "-1", new_today_saved)
    st.session_state.last_charge_time = datetime.datetime.now()  
    st.rerun()

st.markdown("---")

# --- 9. 過去の履歴表示エリア ---
with st.expander("📜 過去の行動履歴を表示する"):
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.write("履歴はまだありません。")

# 画面の自動リフレッシュ（1秒ごと）
time.sleep(1)
st.rerun()