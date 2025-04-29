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

    # プロンプトに具体例を含め、4択形式を指定
    prompt = (
        f"ジャンル『{genre}』の一般知識クイズを{n}問作成してください。\n"
        "各問題に4つの選択肢を用意し、正解は選択肢リストのインデックス(0～3)で示してください。\n"
        "JSONのリスト形式で返してください。例：\n"
        "[\n"
        "  {\"question\":\"日本の首都はどこですか？\",\n"
        "   \"options\":[\"大阪\",\"京都\",\"東京\",\"名古屋\"],\n"
        "   \"answer\":2},\n"
        "  {\"question\":\"光の速さは？\",\n"
        "   \"options\":[\"3万km/s\",\"30万km/s\",\"300万km/s\",\"3000km/s\"],\n"
        "   \"answer\":1}\n"
        "]\n"
    )

    try:
        # モデル呼び出し
        output = pipe(prompt, max_new_tokens=512)[0]["generated_text"]

        # JSON配列の部分をすべて抽出し、最後の要素を取得
        lists = re.findall(r"\[.*?\]", output, re.S)
        if not lists:
            raise ValueError("JSONリストが見つかりませんでした")
        json_str = lists[-1]

        # パース
        try:
            quiz_list = json.loads(json_str)
        except json.JSONDecodeError:
            # 末尾カンマを削除して再試行
            cleaned = re.sub(r",\s*([\]\}])", r"\1", json_str)
            quiz_list = eval(cleaned)

        return quiz_list

    except Exception as e:
        st.error(f"クイズ生成中にエラーが発生しました: {e}")
        if 'output' in locals():
            st.error(f"@@ raw output start @@\n{output}\n@@ raw output end @@")
        return []


def check_quiz_answer(pipe, question: str, user_answer: str):
    """
    LLMに採点を依頼し、(メッセージ, 正誤フラグ(bool), 正答文字列)を返します。
    自由記述式の採点が必要な場合に使用。
    """
    if pipe is None:
        return "モデルがロードされていないため、採点できません。", False, ""

    prompt = (
        f"以下のクイズを採点してください。\n"
        f"問題: {question}\n"
        f"ユーザーの解答: {user_answer}\n"
        "JSON形式で出力してください：{\"is_correct\":0 or 1, \"correct_answer\":\"...\"}"
    )

    try:
        output = pipe(prompt, max_new_tokens=128)[0]["generated_text"]
        m = re.search(r"\{.*?\}", output, re.S)
        if not m:
            raise ValueError("採点結果のJSONが見つかりませんでした")

        result = json.loads(m.group(0))
        is_correct = bool(result.get("is_correct", 0))
        correct_answer = result.get("correct_answer", "")
        message = "正解です！" if is_correct else f"不正解です。正答は『{correct_answer}』です。"

        return message, is_correct, correct_answer

    except Exception as e:
        st.error(f"採点中にエラーが発生しました: {e}")
        if 'output' in locals():
            st.error(f"@@ raw output start @@\n{output}\n@@ raw output end @@")
        return "採点に失敗しました。", False, ""