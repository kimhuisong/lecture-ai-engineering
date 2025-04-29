# ui.py

import streamlit as st
from llm import generate_quiz, check_quiz_answer
from database import save_quiz_result, get_quiz_history
from data import get_sample_questions


def display_quiz_page(pipe):
    """
    クイズ出題ページを表示する
    """
    st.header("🧩 クイズチャレンジ")

    # ジャンル選択と問題数スライダー
    genre = st.selectbox("ジャンルを選択してください", ["動物", "健康", "スポーツ", "科学", "社会"])
    count = st.slider("問題数", min_value=1, max_value=20, value=5)

    # セッションステート初期化
    if 'quiz_list' not in st.session_state:
        st.session_state.quiz_list = []
        st.session_state.current_idx = 0
        st.session_state.score = 0

    # 出題開始
    if st.button("出題開始"):
        st.session_state.quiz_list = generate_quiz(pipe, genre, count)
        st.session_state.current_idx = 0
        st.session_state.score = 0

    # 問題生成エラーチェック
    if not st.session_state.quiz_list:
        st.info("「出題開始」を押してクイズを生成してください。")
        return

    # 現在の問題番号
    idx = st.session_state.current_idx
    total = len(st.session_state.quiz_list)

    # 全問題終了後
    if idx >= total:
        st.success(f"全{total}問終了！ 最終スコア：{st.session_state.score}")
        if st.button("再度チャレンジ"):
            st.session_state.quiz_list = []
            st.session_state.current_idx = 0
            st.session_state.score = 0
        return

    # 問題取得
    q = st.session_state.quiz_list[idx]
    # 辞書形式でない場合エラー
    if not isinstance(q, dict):
        st.error("問題の生成に失敗しました。再度「出題開始」を押してください。")
        return
    question_text = q.get('question', '')
    options = q.get('options', [])
    correct_idx = q.get('answer', None)

    # 表示
    st.subheader(f"問題 {idx+1} ／ {total}")
    st.write(question_text)

    # 選択肢ボタン表示
    if isinstance(options, list) and correct_idx is not None:
        cols = st.columns(len(options))
        for i, opt in enumerate(options):
            if cols[i].button(opt, key=f"btn_{idx}_{i}"):
                # 採点
                correct_ans = options[correct_idx]
                is_correct = (i == correct_idx)
                if is_correct:
                    st.success("正解！")
                else:
                    st.error(f"不正解… 正答は「{correct_ans}」です。")
                # 保存
                save_quiz_result(genre, question_text, correct_ans, opt, is_correct)
                if is_correct:
                    st.session_state.score += 1
                st.session_state.current_idx += 1
                return
    else:
        # 万一選択肢がない場合のフォールバックテキスト入力
        ans = st.text_input("あなたの解答を入力してください", key=f"text_{idx}")
        if st.button("解答を提出", key=f"sub_{idx}"):
            msg, is_correct, correct_ans = check_quiz_answer(pipe, question_text, ans)
            st.write(msg)
            save_quiz_result(genre, question_text, correct_ans, ans, is_correct)
            if is_correct:
                st.session_state.score += 1
            st.session_state.current_idx += 1
            return

    # スコア表示
    st.sidebar.metric("スコア", st.session_state.score)


def display_quiz_history_page():
    """
    過去のクイズ履歴ページを表示する
    """
    st.header("🕘 過去のクイズ履歴")
    rows = get_quiz_history()

    if not rows:
        st.info("まだクイズ履歴がありません。")
        return
    data = []
    for genre, question, correct_ans, user_ans, is_correct, created_at in rows:
        data.append({
            "ジャンル": genre,
            "問題": question,
            "あなたの解答": user_ans,
            "正答": correct_ans,
            "正誤": "✅" if is_correct else "❌",
            "日時": created_at
        })
    st.table(data)


def display_data_page():
    """
    サンプルデータ管理ページ（サンプルクイズ一覧）を表示する
    """
    st.header("📚 サンプルクイズデータ一覧")
    sample_qs = get_sample_questions()
    for idx, item in enumerate(sample_qs, start=1):
        st.subheader(f"{idx}. {item['question']}")
        for opt_idx, opt in enumerate(item['options']):
            st.write(f"- ({opt_idx}) {opt}")
        correct = item['answer']
        st.markdown(f"**正解：** {item['options'][correct]} ({correct})")
        st.markdown("---")