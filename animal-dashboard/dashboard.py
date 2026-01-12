import os
import json
import streamlit as st
import pandas as pd
import altair as alt
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# -------------------------------
# Google Sheets 読み込み設定
# -------------------------------
SPREADSHEET_ID = "1cKGeC-cXA3fIeQxNhdfsZ_gyPiJjc_kFzrMJLKo1Q_g"
SHEET_NAME = "シート1"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Vercel の環境変数から token.json の中身を読む
token_json_str = os.environ["TOKEN_JSON"]          # 環境変数（文字列）
token_data = json.loads(token_json_str)            # Python の dict に変換

creds = Credentials.from_authorized_user_info(token_data, SCOPES)
sheets = build("sheets", "v4", credentials=creds)


# -------------------------------
# Google Sheets → DataFrame
# -------------------------------
def load_data():
    result = sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:C"
    ).execute()

    values = result.get("values", [])

    if len(values) < 2:
        return pd.DataFrame(columns=["filename", "prediction", "time"])

    df = pd.DataFrame(values[1:], columns=["filename", "prediction", "time"])
    return df


# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="動物観測ダッシュボード", layout="wide")

st.title("🦌 動物観測ダッシュボード（研究室モニター）")
st.caption("Google Drive → FastAPI → Sheets → Streamlit の完全自動パイプライン")

df = load_data()

if df.empty:
    st.warning("まだデータがありません")
    st.stop()

# -------------------------------
# 最新データ表示
# -------------------------------
st.subheader("📸 最新の観測データ")

latest = df.iloc[-1]
col1, col2 = st.columns(2)

with col1:
    st.metric("最新ファイル", latest["filename"])
    st.metric("分類結果", latest["prediction"])
    st.metric("撮影日時 (JST)", latest["time"])

with col2:
    # Drive の画像 URL を生成
    file_id = latest["filename"].split(".")[0]
    st.write("（Drive の画像プレビューは必要なら追加できます）")

# -------------------------------
# 全データ一覧
# -------------------------------
st.subheader("📄 全ログ一覧")
st.dataframe(df, use_container_width=True)

# -------------------------------
# 動物ごとの出現数グラフ
# -------------------------------
st.subheader("📊 動物ごとの出現数")

count_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x="prediction:N",
        y="count():Q",
        color="prediction:N"
    )
)

st.altair_chart(count_chart, use_container_width=True)

# -------------------------------
# 時間帯ヒートマップ
# -------------------------------
st.subheader("⏰ 時間帯ヒートマップ")

df["hour"] = pd.to_datetime(df["time"]).dt.hour

heatmap = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x="hour:O",
        y="prediction:N",
        color="count():Q"
    )
)

st.altair_chart(heatmap, use_container_width=True)
