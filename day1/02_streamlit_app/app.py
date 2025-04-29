# app.py

import streamlit as st
import torch
from transformers import pipeline
from config import MODEL_NAME
import metrics
import database
from ui import display_quiz_page, display_quiz_history_page, display_data_page

# --- アプリケーション設定 ---
st.set_page_config(page_title="Gemma Quiz Game", layout="wide")

# --- 初期化処理 ---
metrics.initialize_nltk()
database.init_db()

# --- モデルロード ---
@st.cache_resource
def load_model():
    """LLMモデルをロードして返します"""
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        st.info(f"Using device: {device}")
        pipe = pipeline(
            "text-generation",
            model=MODEL_NAME,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device=device
        )
        st.success(f"モデル '{MODEL_NAME}' の読み込みに成功しました。")
        return pipe
    except Exception as e:
        st.error(f"モデル '{MODEL_NAME}' の読み込みに失敗しました: {e}")
        return None

pipe = load_model()

# --- サイドバー設定 ---
if "score" not in st.session_state:
    st.session_state.score = 0
st.sidebar.metric("スコア", st.session_state.score)

st.sidebar.title("ナビゲーション")
page = st.sidebar.radio(
    "ページ選択",
    ["クイズ", "過去のクイズ", "サンプルデータ管理"],
    index=["クイズ", "過去のクイズ", "サンプルデータ管理"].index(st.session_state.get("page", "クイズ"))
)
st.session_state.page = page

# --- メインコンテンツ ---
st.title("🧩 Gemma Quiz Game")
st.markdown("---")

if page == "クイズ":
    display_quiz_page(pipe)
elif page == "過去のクイズ":
    display_quiz_history_page()
else:
    display_data_page()

# --- フッター ---
st.sidebar.markdown("---")
st.sidebar.info("開発者: Your Name")