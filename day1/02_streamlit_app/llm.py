# llm.py

import re
import json
import torch
import streamlit as st
from transformers import pipeline
from config import MODEL_NAME

@st.cache_resource
def load_model():
    """
    LLMモデルをロードして返します
    """
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


def generate_quiz(pipe, genre: str, n: int):
    """
    ジャンル genre で n 問の一般知識クイズを生成し、
    選択肢付き JSON リストを返します。
    フォーマット:
      [
        {
          "question": "...",
          "options": ["A","B","C","D"],
          "answer": 0  # options の正解インデックス
        }, ...
      ]
    """
    if pipe is None:
        st.error("モデルがロードされていないため、クイズを生成できません。")
        return []

    # プロンプト文を厳格化（不要な文章を出さないよう制約）
    prompt = (
        f"ジャンル「{genre}」の一般知識に関する4択クイズを{n}問、JSON形式のリストで出力してください。\n"
        "以下の形式に従い、JSONリスト **のみ** を返してください。説明文や例、見出しを含めないでください。\n"
        "[\n"
        "  {\"question\": \"日本の首都はどこですか？\", \"options\": [\"大阪\", \"京都\", \"東京\", \"名古屋\"], \"answer\": 2},\n"
        "  {\"question\": \"光の速さは？\", \"options\": [\"3万km/s\", \"30万km/s\", \"300万km/s\", \"3000km/s\"], \"answer\": 1}\n"
        "]"
    )

    try:
        output = pipe(prompt, max_new_tokens=1024)[0]["generated_text"]

        # JSONリスト抽出を試みる（[]内の全体）
        m = re.search(r'\[\s*{.*?}\s*\]', output, re.S)
        if m:
            json_str = m.group(0)
        else:
            # うまくパースできない場合、すべての { ... } を抽出して強引に整形
            objs = re.findall(r'{\s*"question".*?}', output, re.S)
            if not objs:
                raise ValueError("有効なJSONオブジェクトが見つかりませんでした")
            json_str = "[" + ",".join(objs) + "]"

        # JSONデコード（末尾カンマ除去対応）
        try:
            quiz_list = json.loads(json_str)
        except json.JSONDecodeError:
            cleaned = re.sub(r",\s*([\]}])", r"\1", json_str)
            quiz_list = eval(cleaned)

        # 各問題の形式確認
        valid_quiz_list = []
        for q in quiz_list:
            if isinstance(q, dict) and 'question' in q and 'options' in q and 'answer' in q:
                valid_quiz_list.append(q)

        if not valid_quiz_list:
            raise ValueError("問題データの形式が正しくありません")

        return valid_quiz_list

    except Exception as e:
        st.error(f"クイズ生成中にエラーが発生しました: {e}")
        if 'output' in locals():
            st.error(f"@@ raw output start @@\n{output}\n@@ raw output end @@")
        return []


def check_quiz_answer(pipe, question: str, user_answer: str):
    """
    自由記述形式の解答に対して、LLMに採点を依頼する。
    出力形式: {"is_correct": 0 or 1, "correct_answer": "..."}
    """
    if pipe is None:
        return "モデルがロードされていないため、採点できません。", False, ""

    prompt = (
        f"以下のクイズを採点してください。\n"
        f"問題: {question}\n"
        f"ユーザーの解答: {user_answer}\n"
        "JSON形式で出力してください： {\"is_correct\": 0 or 1, \"correct_answer\": \"...\"}"
    )

    try:
        output = pipe(prompt, max_new_tokens=128)[0]["generated_text"]
        m = re.search(r"\{.*?\}", output, re.S)
        if not m:
            raise ValueError("採点結果のJSONが見つかりませんでした")

        result = json.loads(m.group(0))
        is_correct = bool(result.get("is_correct", 0))
        correct_answer = result.get("correct_answer", "")
        message = "正解です！" if is_correct else f"不正解です。正答は「{correct_answer}」です。"

        return message, is_correct, correct_answer

    except Exception as e:
        st.error(f"採点中にエラーが発生しました: {e}")
        if 'output' in locals():
            st.error(f"@@ raw output start @@\n{output}\n@@ raw output end @@")
        return "採点に失敗しました。", False, ""
