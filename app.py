import streamlit as st
import datetime
import pandas as pd
import requests
import io

# 設定
st.set_page_config(page_title="SmokeSaver", layout="centered")

# デザイン微調整
st.markdown("""
    <style>
    h1 { font-size: 1.5rem !important; margin-bottom: 0.5rem !important; }
    .stSelectbox { margin-top: -10px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🚬 スモークセーバー (SS)")

# ユーザー別のデータ格納先（IDを個別に設定）
user_db_map = {
    "(U)": "11LhDcF9hZzHDa3ewq-KrNvvMCqMwMlWnWW1b9uK7hG0", 
    "Guest1": "別のスプレッドシートID", 
    "Guest2": "別のスプレッドシートID"
}

current_user = st.sidebar.selectbox("ユーザーを選択", list(user_db_map.keys()))

def load_data(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
    except:
        return None
    return None

# データ取得
df = load_data(user_db_map[current_user])

if df is not None:
    st.success(f"{current_user} のデータを読み込みました")
    st.write(df.head()) # 個別のデータが表示される
else:
    st.warning("データが取得できませんでした（シートIDが正しいか確認してください）")

# 残弾管理など（略）