import streamlit as st
import datetime
import pandas as pd

# 設定
st.set_page_config(page_title="SmokeSaver", layout="centered")

# CSS修正：タイトルとサイドバーの干渉を排除
st.markdown("""
    <style>
    h1 { font-size: 1.5rem !important; margin-bottom: 1rem !important; }
    .stApp { padding-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🚬 スモークセーバー (SS)")

# ユーザー選択（サイドバー）
current_user = st.sidebar.selectbox("ユーザーを選択", ["(U)", "Guest1", "Guest2"])

# 表示エリア（エラー回避のため一旦DB読み込みをコメントアウトし、UIを復活させる）
st.write(f"### 現在のユーザー: {current_user}")
st.info("※現在、データ同期システムを再調整中です。")

# 残弾表示（UIのデバッグ用）
st.subheader("🔋 現在の残弾")
max_stock = 4
bullets = 2
bullet_bar = "■" * bullets + "□" * (max_stock - bullets)
st.markdown(f"**{bullet_bar} &nbsp; {bullets} / {max_stock} 本**")

if st.button("🚬 1本吸う"):
    st.write("記録しました")