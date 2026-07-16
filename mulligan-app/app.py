import streamlit as st
import pandas as pd
from scipy.stats import hypergeom

st.title("🎤 神椿TCG マリガン確率計算機")

N = 60  # デッキ枚数
n = 7   # 初期手札枚数

st.header("📋 デッキ内のArtist枚数設定")
K_good = st.number_input("① 理想のArtist（アタリ）の枚数", value=4, min_value=0, max_value=60)
K_bad = st.number_input("② 妥協のArtist（ハズレ）の枚数", value=4, min_value=0, max_value=60)

K_total_artist = K_good + K_bad

if K_total_artist > N:
    st.error("Artistの合計枚数がデッキ枚数(60枚)を超えています。")
else:
    p_mulligan_trigger = hypergeom.pmf(0, N, K_total_artist, n)
    p_good_in_1st = 1 - hypergeom.pmf(0, N, K_good, n)
    p_bad_start = 1 - p_mulligan_trigger - p_good_in_1st
    if p_bad_start < 0: p_bad_start = 0

    p_good_in_2nd = 1 - hypergeom.pmf(0, N, K_good, n)
    p_final_good = p_good_in_1st + (p_mulligan_trigger * p_good_in_2nd)
    
    p_bad_in_2nd = 1 - hypergeom.pmf(0, N, K_total_artist, n) - p_good_in_2nd
    if p_bad_in_2nd < 0: p_bad_in_2nd = 0
    p_final_bad = p_bad_start + (p_mulligan_trigger * p_bad_in_2nd)
    
    p_final_brick = p_mulligan_trigger * hypergeom.pmf(0, N, K_total_artist, n)

    st.header("🔄 マリガン（引き直し）の発生確率")
    st.metric(label="🚨 最初の7枚がArtist 0枚で【引き直し】になる確率", value=f"{p_mulligan_trigger * 100:.2f}%")

    st.header("📊 最終的な初手パターンの確率")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("✨ 理想スタート", f"{p_final_good * 100:.2f}%")
    with col2: st.metric("⚠️ 妥協スタート", f"{p_final_bad * 100:.2f}%")
    with col3: st.metric("❌ Artistなし (大事故)", f"{p_final_brick * 100:.2f}%")

    df_chart = pd.DataFrame({
        "初期手札の結果": ["理想スタート", "妥協スタート", "Artistなし事故"],
        "確率 (%)": [p_final_good * 100, p_final_bad * 100, p_final_brick * 100]
    })
    st.bar_chart(data=df_chart, x="初期手札の結果", y="確率 (%)")
