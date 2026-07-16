import streamlit as st
import pandas as pd
from scipy.stats import hypergeom

st.title("🎤 神椿TCG マリガン確率計算機 (公式ルール準拠)")
st.caption("※初手にArtistが1枚も来ない場合、引けるまで何度でも引き直す公式ルールに完全対応しています。")

# 固定ルール
N = 60  # デッキ枚数
n = 7   # 初期手札枚数

# 入力フォーム
st.header("📋 デッキ内のArtist枚数設定")
K_good = st.number_input("① 理想のArtist（アタリ）の枚数", value=12, min_value=0, max_value=60)
K_bad = st.number_input("② 妥協のArtist（ハズレ）の枚数", value=2, min_value=0, max_value=60)

K_total_artist = K_good + K_bad

if K_total_artist > N:
    st.error("Artistの合計枚数がデッキ枚数(60枚)を超えています。")
elif K_total_artist == 0:
    st.error("デッキにアーティストが0枚の場合、ゲームを開始できません。")
else:
    # --- 1回の手札(7枚)における基本的な確率 ---
    # Artistが1枚も出ない確率（＝引き直しをループする確率）
    p_zero = hypergeom.pmf(0, N, K_total_artist, n)
    
    # 7枚の中にアタリが1枚以上ある確率
    p_good_any = 1 - hypergeom.pmf(0, N, K_good, n)
    
    # 7枚の中にアタリがなく、ハズレだけがある確率（＝引き直しが終了し、妥協スタートになる確率）
    p_bad_only = 1 - p_zero - p_good_any
    if p_bad_only < 0: p_bad_only = 0

    # --- 無限ループ（幾何級数）による最終着地確率の計算 ---
    # アーティストが来るまで絶対に引き直すため、分母は「アーティストが1枚以上出る確率」になります。
    p_end = 1 - p_zero 
    
    p_final_good = p_good_any / p_end
    p_final_bad = p_bad_only / p_end
    p_final_brick = 0.0  # 何度でも引き直すため「Artistなし」で始まる確率は0%

    # --- 結果表示 ---
    st.header("🔄 引き直しの発生率")
    st.metric(
        label="🚨 最初の7枚がArtist 0枚で【引き直し（ループ）】になる確率", 
        value=f"{p_zero * 100:.2f}%"
    )
    st.caption("※神椿TCGでは、この確率のときは手札が配り直されるため、大事故でのゲーム開始を防げます。")

    st.header("📊 最終的な初手パターンの確率")
    st.caption("アーティストが手札に来るまで引き直した結果、最終的にゲームが始まる際の手札の確率です。")
    
    # メトリック表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✨ 理想スタート (アタリあり)", f"{p_final_good * 100:.2f}%")
    with col2:
        st.metric("⚠️ 妥協スタート (ハズレのみ)", f"{p_final_bad * 100:.2f}%")
    with col3:
        st.metric("❌ Artistなし (大事故)", f"{p_final_brick * 100:.2f}%")

    # グラフ用データ作成
    df_chart = pd.DataFrame({
        "初期手札の結果": ["理想スタート", "妥協スタート", "Artistなし事故"],
        "確率 (%)": [p_final_good * 100, p_final_bad * 100, p_final_brick * 100]
    })
    st.bar_chart(data=df_chart, x="初期手札の結果", y="確率 (%)")
