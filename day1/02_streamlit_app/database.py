# database.py

import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
from config import DB_FILE, QUIZ_TABLE
from metrics import calculate_metrics

# --- テーブル名定義 ---
CHAT_TABLE = "chat_history"

# --- スキーマ定義 ---
# チャット（評価）用テーブル
CHAT_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {CHAT_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    question TEXT,
    answer TEXT,
    feedback TEXT,
    correct_answer TEXT,
    is_correct REAL,       -- 0.0, 0.5, 1.0 を許容
    response_time REAL,
    bleu_score REAL,
    similarity_score REAL,
    word_count INTEGER,
    relevance_score REAL
);
"""

# クイズ履歴テーブルは config.QUIZ_TABLE で定義
QUIZ_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {QUIZ_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genre TEXT NOT NULL,
    question TEXT NOT NULL,
    correct_answer TEXT,
    user_answer TEXT,
    is_correct INTEGER,    -- 0 or 1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def init_db():
    """データベースと各テーブルを初期化する"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # チャット評価用テーブル
        c.execute(CHAT_SCHEMA)
        # クイズ履歴用テーブル
        c.execute(QUIZ_SCHEMA)
        conn.commit()
    except Exception as e:
        st.error(f"データベースの初期化に失敗しました: {e}")
        raise
    finally:
        conn.close()

# --- チャット（評価）データ操作関数 ---

def save_to_db(question, answer, feedback, correct_answer, is_correct, response_time):
    """
    チャットの質問／回答と評価指標を保存する
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 各種メトリクスを計算
        bleu, sim, wc, rel = calculate_metrics(answer, correct_answer)
        c.execute(f"""
            INSERT INTO {CHAT_TABLE}
            (timestamp, question, answer, feedback, correct_answer,
             is_correct, response_time, bleu_score, similarity_score,
             word_count, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, question, answer, feedback, correct_answer,
            is_correct, response_time, bleu, sim, wc, rel
        ))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"チャット評価データの保存中にエラーが発生しました: {e}")
    finally:
        conn.close()

def get_chat_history():
    """
    チャット評価履歴を DataFrame で取得する
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(f"SELECT * FROM {CHAT_TABLE} ORDER BY timestamp DESC", conn)
        # is_correct を数値に変換
        if 'is_correct' in df.columns:
            df['is_correct'] = pd.to_numeric(df['is_correct'], errors='coerce')
        return df
    except sqlite3.Error as e:
        st.error(f"チャット履歴の取得中にエラーが発生しました: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_db_count():
    """
    チャット評価テーブルのレコード数を返す
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM {CHAT_TABLE}")
        return c.fetchone()[0]
    except sqlite3.Error as e:
        st.error(f"レコード数の取得中にエラーが発生しました: {e}")
        return 0
    finally:
        conn.close()

def clear_db():
    """
    チャット評価テーブルを全削除する（2回押しで実行）
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        confirmed = st.session_state.get("confirm_clear", False)
        if not confirmed:
            st.warning("本当に全データを削除しますか？再度「データベースをクリア」ボタンを押すと実行されます。")
            st.session_state.confirm_clear = True
            return False

        c = conn.cursor()
        c.execute(f"DELETE FROM {CHAT_TABLE}")
        conn.commit()
        st.success("チャット評価データを全て削除しました。")
        st.session_state.confirm_clear = False
        return True
    except sqlite3.Error as e:
        st.error(f"データベースのクリア中にエラーが発生しました: {e}")
        st.session_state.confirm_clear = False
        return False
    finally:
        conn.close()

# --- クイズ履歴データ操作関数 ---

def save_quiz_result(genre, question, correct_answer, user_answer, is_correct):
    """
    クイズの結果を保存する
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute(f"""
            INSERT INTO {QUIZ_TABLE}
            (genre, question, correct_answer, user_answer, is_correct)
            VALUES (?, ?, ?, ?, ?)
        """, (genre, question, correct_answer, user_answer, int(is_correct)))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"クイズ結果の保存中にエラーが発生しました: {e}")
    finally:
        conn.close()

def get_quiz_history():
    """
    クイズ履歴を取得する（リスト形式）
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(f"""
            SELECT genre, question, correct_answer, user_answer, is_correct, created_at
            FROM {QUIZ_TABLE}
            ORDER BY created_at DESC
        """)
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"クイズ履歴の取得中にエラーが発生しました: {e}")
        return []
    finally:
        conn.close()