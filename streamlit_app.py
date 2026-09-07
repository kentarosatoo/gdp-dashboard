import streamlit as st
import pandas as pd
import math
from pathlib import Path

# ブラウザのタブに表示されるタイトルとアイコン
st.set_page_config(
    page_title='GDP dashboard',
    page_icon=':earth_americas:',
)

# -----------------------------------------------------------------------------
# データの読み込みと前処理（キャッシュ機能付き）
@st.cache_data
def get_gdp_data():
    # app.py と同じ場所にある data/gdp_data.csv を指定
    data_path = Path(__file__).parent / 'data/gdp_data.csv'
    
    # 世界銀行のCSVは先頭4行がメタ情報なので skiprows=4 でスキップ
    raw_df = pd.read_csv(data_path, skiprows=4)

    # 1960年から2024年までのうち、CSVに実在する年の列名を抽出
    year_columns = [str(year) for year in range(1960, 2025) if str(year) in raw_df.columns]

    # 横に広がった年ごとの列を、「Year」「GDP」の縦持ちデータに変換
    df = raw_df.melt(
        id_vars=['Country Name', 'Country Code'],
        value_vars=year_columns,
        var_name='Year',
        value_name='GDP',
    )

    # 数値型に変換（文字列のままだとグラフや計算が崩れるため）
    df['Year'] = pd.to_numeric(df['Year'])
    df['GDP'] = pd.to_numeric(df['GDP'], errors='coerce')
    return df

# データの読み込み実行
gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# 画面の表示部分

'''
# :earth_americas: GDP Dashboard (〜2024年)

世界銀行（World Bank）のオープンデータをもとに作成したGDPダッシュボードです。
'''

# 年の選択スライダー
min_year = int(gdp_df['Year'].min())
max_year = int(gdp_df['Year'].max())

from_year, to_year = st.slider(
    '期間を選択してください',
    min_value=min_year,
    max_value=max_year,
    value=[min_year, max_year]
)

# 国コードの一覧取得
countries = sorted(gdp_df['Country Name'].dropna().unique())

# 国の複数選択ボックス
selected_countries = st.multiselect(
    '表示する国を選択してください（複数選択可）',
    options=countries,
    default=['United States', 'Japan', 'Germany', 'United Kingdom', 'France']
)

# もし国が1つも選ばれていない場合は警告を出して以降の描画を停止
if not selected_countries:
    st.info("国を1つ以上選択してください。")
    st.stop()

# ↓↓↓ 【変更後】Country Name で一致判定する
filtered_df = gdp_df[
    (gdp_df['Country Name'].isin(selected_countries))
    & (gdp_df['Year'] >= from_year)
    & (gdp_df['Year'] <= to_year)
]

# 折れ線グラフの描画
st.header('GDPの推移', divider='gray')
# ↓↓↓ 【変更後】凡例を 正式国名 にする
st.line_chart(
    filtered_df,
    x='Year',
    y='GDP',
    color='Country Name'
)

# 選択した最終年の統計カード（メトリクス）表示
st.header(f'{to_year}年のGDPと成長倍率', divider='gray')
cols = st.columns(4)

first_year_data = gdp_df[gdp_df['Year'] == from_year]
last_year_data = gdp_df[gdp_df['Year'] == to_year]

for i, country in enumerate(selected_countries):
    col = cols[i % 4]
    with col:
        # ↓↓↓ 【変更後】Country Name で行を探す
        first_val = first_year_data[first_year_data['Country Name'] == country]['GDP'].values
        last_val = last_year_data[last_year_data['Country Name'] == country]['GDP'].values

        # 単位を10億ドル（Billion USD）に換算
        gdp_start = first_val[0] / 1e9 if len(first_val) > 0 else float('nan')
        gdp_end = last_val[0] / 1e9 if len(last_val) > 0 else float('nan')

        # 成長倍率の計算（欠損値チェック）
        if math.isnan(gdp_start) or gdp_start == 0 or math.isnan(gdp_end):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{gdp_end / gdp_start:,.2f}倍'
            delta_color = 'normal'

        display_val = f'{gdp_end:,.0f} B$' if not math.isnan(gdp_end) else 'データなし'

        st.metric(
            label=f'{country}',
            value=display_val,
            delta=growth,
            delta_color=delta_color
        )
