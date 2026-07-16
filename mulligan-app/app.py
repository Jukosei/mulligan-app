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

# 入力フォーム（キーカード設定）
st.header("🔮 キーカード＆ドロー設定")

turn_choice = st.radio("手番を選択してください（1ターン目の通常ドローに影響）", ["先攻 (通常ドローなし)", "後攻 (通常ドロー 1枚)"])
turn_draw = 0 if "先攻" in turn_choice else 1

card_name = st.text_input("狙いたいキーカードの名前", value="過去を喰らう")
K_magic = st.number_input(f"デッキ内の『{card_name}』の枚数", value=4, min_value=0, max_value=4)

# 🌌 強力な手札リセットマジック枠
st.subheader("🌌 手札リセットマジックの考慮")
col_w1, col_w2 = st.columns(2)
with col_w1:
    K_warp = st.number_input("『ディメンションワープ』の枚数", value=4, min_value=0, max_value=4)
with col_w2:
    K_next = st.number_input("『ネクストタイム』の枚数", value=4, min_value=0, max_value=4)

# 入力フォーム（通常のドローカード5系統）
st.subheader("🃏 その他の手札交換・ドローカードの考慮")
st.markdown("採用しているドローカードの枚数と、引ける枚数を入力してください（使わない枠は0枚）。")

draw_configs = [
    {"label": "ドローカードA", "key_count": "cnt_a", "key_amt": "amt_a", "def_cnt": 4, "def_amt": 2},
    {"label": "ドローカードB", "key_count": "cnt_b", "key_amt": "amt_b", "def_cnt": 0, "def_amt": 1},
    {"label": "ドローカードC", "key_count": "cnt_c", "key_amt": "amt_c", "def_cnt": 0, "def_amt": 1},
    {"label": "ドローカードD", "key_count": "cnt_d", "key_amt": "amt_d", "def_cnt": 0, "def_amt": 1},
    {"label": "ドローカードE", "key_count": "cnt_e", "key_amt": "amt_e", "def_cnt": 0, "def_amt": 1},
]

K_draw_total = 0
draw_inputs = []

for config in draw_configs:
    col_l, col_r = st.columns(2)
    with col_l:
        cnt = st.number_input(f"【{config['label']}】採用枚数", value=config["def_cnt"], min_value=0, max_value=60, key=config["key_count"])
    with col_r:
        amt = st.number_input(f"【{config['label']}】引ける枚数", value=config["def_amt"], min_value=1, max_value=10, key=config["key_amt"])
    
    K_draw_total += cnt
    if cnt > 0:
        draw_inputs.append({"count": cnt, "amount": amt})

if K_total_artist > N:
    st.error("Artistの合計枚数がデッキ枚数(60枚)を超えています。")
elif K_total_artist == 0:
    st.error("デッキにアーティストが0枚の場合、ゲームを開始できません。")
elif K_magic + K_draw_total + K_warp + K_next > N:
    st.error("カードの合計枚数がデッキ枚数を超えています。")
else:
    # --- 確率計算（アーティスト側） ---
    p_zero = hypergeom.pmf(0, N, K_total_artist, n)
    p_good_any = 1 - hypergeom.pmf(0, N, K_good, n)
    p_bad_only = max(0.0, 1 - p_zero - p_good_any)

    p_end = 1 - p_zero 
    p_final_good = p_good_any / p_end
    p_final_bad = p_bad_only / p_end

    # --- 確率計算（手番ドロー＋各種ドロー連携） ---
    base_cards = n + turn_draw

    # パターン1: 何も使わずに最初からキーカードを直接引いている確率
    p_magic_direct = 1 - hypergeom.pmf(0, N, K_magic, base_cards)
    p_no_magic_before_draw = hypergeom.pmf(0, N, K_magic, base_cards)
    
    # 手札のリセット札・通常ドロー札の所持率
    p_has_warp = 1 - hypergeom.pmf(0, N, K_warp, base_cards)
    p_has_next = 1 - hypergeom.pmf(0, N, K_next, base_cards)

    p_use_warp = p_has_warp
    p_magic_in_warp = 1 - hypergeom.pmf(0, N - base_cards, K_magic, 5)
    p_via_warp = p_use_warp * p_magic_in_warp

    p_no_warp = 1 - p_has_warp
    p_not_via_normal_draw = 1.0
    for draw_info in draw_inputs:
        p_has_this_draw = 1 - hypergeom.pmf(0, N, draw_info["count"], base_cards)
        p_magic_in_this_draw = 1 - hypergeom.pmf(0, N - base_cards, K_magic, draw_info["amount"])
        p_not_via_this_draw = 1 - (p_has_this_draw * p_magic_in_this_draw)
        p_not_via_normal_draw *= p_not_via_this_draw
    
    p_has_any_normal_draw = 1 - hypergeom.pmf(0, N, K_draw_total, base_cards) if K_draw_total > 0 else 0.0
    p_via_normal_draw = p_no_warp * (1 - p_not_via_normal_draw)

    p_no_warp_and_no_normal = p_no_warp * (1 - p_has_any_normal_draw)
    p_use_next_lastly = p_no_warp_and_no_normal * p_has_next
    p_magic_in_next = 1 - hypergeom.pmf(0, N - base_cards, K_magic, 3)
    p_via_next = p_use_next_lastly * p_magic_in_next

    p_magic_via_any_action = p_via_warp + p_via_normal_draw + p_via_next
    p_total_magic_success = p_magic_direct + (p_no_magic_before_draw * p_magic_via_any_action)
    if p_total_magic_success > 1.0: p_total_magic_success = 1.0

    # --- 🔥 2枚目以降のArtistをキープできている確率の計算 ---
    # マリガンによって「Artistが1枚以上いる確定した7枚」における、Artistの合計枚数が「2枚以上」である確率
    p_artist_exactly_1 = hypergeom.pmf(1, N, K_total_artist, n)
    p_artist_at_least_2_in_7 = (p_end - p_artist_exactly_1) / p_end # 7枚時点での条件付き確率
    
    # 2ターン目以降（手番ドロー base_cards 枚時点）で、Artistが2枚以上手札にある確率
    p_artist_exactly_1_in_base = hypergeom.pmf(1, N, K_total_artist, base_cards)
    p_artist_zero_in_base = hypergeom.pmf(0, N, K_total_artist, base_cards)
    # アーティスト1枚以上が確定している世界線での、2枚以上の確率
    p_artist_at_least_2_final = (1.0 - p_artist_zero_in_base - p_artist_exactly_1_in_base) / (1.0 - p_artist_zero_in_base)

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

    # 🔥 追加：アーティストの重複キープ率
    st.header("🧑‍🎤 2枚目以降のArtistカード所持率")
    st.metric(
        label="👥 ゲーム開始〜自身の最初のターン時に、Artistが2枚以上手札にある確率",
        value=f"{p_artist_at_least_2_final * 100:.2f}%"
    )
    st.caption("※「Artistが最低1枚いる確定手札」からスタートし、手番ドロー（後攻なら1枚追加）を終えた段階で、手札に2枚目以降のArtistがダブってキープできている確率です。")

    # 指定カードの確保率表示
    st.header(f"🃏 『{card_name}』の引き込み確率")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="🌟 通常ルール（手札）での純粋な確保率", value=f"{p_magic_direct * 100:.2f}%")
    with col_m2:
        st.metric(label="🔥 ワープ・通常ドロー・ネクスト（最後尾）込み最終確保率", value=f"{p_total_magic_success * 100:.2f}%")
