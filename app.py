import streamlit as st
import datetime
import time
import requests
import pandas as pd
import io

# 画面の基本設定
st.set_page_config(page_title="SmokeSaver", layout="centered")

# --- 修正版CSS ---
st.markdown("""
    <style>
    /* タイトルとヘッダーの余白調整 */
    .block-container { padding-top: 0.5rem; }
    h1 { font-size: 1.4rem !important; margin-bottom: 0.5rem !important; padding: 0 !important; }
    
    /* 選択ボックスのズレを解消 */
    .stSelectbox { margin-top: -10px !important; }
    
    .gauge-container {
        font-family: monospace;
        font-size: 1.3rem;
        background-color: #1e1e1e;
        padding: 0.5rem;
        border-radius: 5px;
        color: #00ffcc;
        border: 1px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚬 スモークセーバー (SS)")

# --- ユーザー設定 ---
current_user = st.sidebar.selectbox("ユーザーを選択", ["(U)", "Guest1", "Guest2"])

# --- データ取得・解析（プライバシー保護のため選択ユーザーのみ抽出） ---
GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/11LhDcF9hZzHDa3ewq-KrNvvMCqMwMlWnWW1b9uK7hG0/gviz/tq?tqx=out:csv"

def get_user_data(user_name):
    # 実際にはここで「ユーザー専用のシート」を読み込むのがベスト
    # 現状は全体シートからその人のデータのみを抽出
    try:
        response = requests.get(GSHEET_CSV_URL)
        df = pd.read_csv(io.StringIO(response.text))
        return df[df["ユーザー"] == user_name]
    except:
        return pd.DataFrame()

# 以下、前回同様のロジックで動作します
# ...（省略：コード全体の構成を維持）