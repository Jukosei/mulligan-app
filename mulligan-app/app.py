import streamlit as st
import pandas as pd
from scipy.stats import hypergeom

st.title("🎤 神椿TCG マリガン確率計算機")

# 固定ルール
N = 60  # デッキ枚数
n = 7   # 初期手札枚数

# 入力フォーム（アーティスト設定）
st.header("📋 デッキ内のArtist枚数設定")
K_good = st.number_input("① 理想のArtist（アタリ）の枚数", value=12, min_value=0, max_value=60)
K_bad = st.number_input("② 妥協のArtist（ハズレ）の枚数", value=2, min_value=0, max_value=60)

K_total_artist = K_good + K_bad

# 入力フォーム（キーカード＆ドロー設定）
st.header("🔮 キーカード＆ドロー設定")

# 先攻・後攻の選択（通常ドローの自動計算用）
turn_choice = st.radio("手番を選択してください（1ターン目の通常ドローに影響）", ["先攻 (通常ドローなし)", "後攻 (通常ドロー 1枚)"])
turn_draw = 0 if "先攻" in turn_choice else 1

card_name = st.text_input("狙いたいキーカードの名前", value="過去を喰らう")
K_magic = st.number_input(f"デッキ内の『{card_name}』の枚数", value=4, min_value=0, max_value=4)

st.subheader("🃏 手札交換・ドローカードの考慮")
K_draw_cards = st.number_input("デッキ内の「ドローカード」の総数（2枚引くマジックなど）", value=4, min_value=0, max_value=60)
draw_amount = st.number_input("そのドローカードが追加で引っ張ってくる枚数", value=2, min_value=1, max_value=10)

if K_total_artist > N:
    st.error("Artistの合計枚数がデッキ枚数(60枚)を超えています。")
elif K_total_artist == 0:
    st.error("デッキにアーティストが0枚の場合、ゲームを開始できません。")
elif K_magic + K_draw_cards > N:
    st.error("カードの合計枚数がデッキ枚数を超えています。")
else:
    # --- 確率計算（アーティスト側） ---
    p_zero = hypergeom.pmf(0, N, K_total_artist, n)
    p_good_any = 1 - hypergeom.pmf(0, N, K_good, n)
    p_bad_only = max(0.0, 1 - p_zero - p_good_any)

    p_end = 1 - p_zero 
    p_final_good = p_good_any / p_end
    p_final_bad = p_bad_only / p_end

    # --- 確率計算（手番ドロー考慮） ---
    # ターン開始時のドロー枚数（先攻=0枚, 後攻=1枚）を合わせた、ドロー前の総カード枚数
    base_cards = n + turn_draw

    # パターン1: ドローカードを使う前の段階でキーカードを引く確率
    p_magic_direct = 1 - hypergeom.pmf(0, N, K_magic, base_cards)

    # パターン2: ドローカードを使う前の手札にキーカードはないが、ドローカードがあり、ドロー先で引ける確率
    p_no_magic_before_draw = hypergeom.pmf(0, N, K_magic, base_cards)
    p_has_draw_before_draw = 1 - hypergeom.pmf(0, N, K_draw_cards, base_cards)
    
    # マジック使用時点での残り山札から、キーカードを引き当てる確率
    p_magic_in_draw = 1 - hypergeom.pmf(0, N - base_cards, K_magic, draw_amount)
    
    # ドローによって引き込める確率
    p_magic_via_draw = p_no_magic_before_draw * p_has_draw_before_draw * p_magic_in_draw

    # 最終的な合計確保率
    p_total_magic_success = p_magic_direct + p_magic_via_draw
    if p_total_magic_success > 1.0: p_total_magic_success = 1.0

    # --- 結果表示 ---
    st.header("🔄 引き直しの発生率")
    st.metric(label="🚨 最初の7枚がArtist 0枚で【引き直し】になる確率", value=f"{p_zero * 100:.2f}%")

    st.header("📊 最終的な初手パターンの確率")
    col1, col2 = st.columns(2)
    with col1: st.metric("✨ 理想スタート (アタリあり)", f"{p_final_good * 100:.2f}%")
    with col2: st.metric("⚠️ 妥協スタート (ハズレのみ)", f"{p_final_bad * 100:.2f}%")

    df_chart = pd.DataFrame({
        "初期手札の結果": ["理想スタート", "妥協スタート"],
        "確率 (%)": [p_final_good * 100, p_final_bad * 100]
    })
    st.bar_chart(data=df_chart, x="初期手札の結果", y="確率 (%)")

    # 指定カードの確保率表示
    st.header(f"🃏 『{card_name}』の引き込み確率")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="🌟 マジック使用前の純粋な確保率", value=f"{p_magic_direct * 100:.2f}%")
    with col_m2:
        st.metric(label="🔥 マジック使用込みの最終確保率", value=f"{p_total_magic_success * 100:.2f}%")
        
    st.caption(f"※{turn_choice}の通常ルールと、初期手札にない場合にドローマジックをさらに使って {draw_amount} 枚掘り進めた場合を含めた確率です。")
