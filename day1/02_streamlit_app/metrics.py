import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.tokenize import word_tokenize
from janome.tokenizer import Tokenizer
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def initialize_nltk():
    """
    NLTK の punkt トークナイザデータをダウンロードします。
    起動時に一度呼び出してください。
    """
    try:
        nltk.download('punkt', quiet=True)
    except Exception:
        pass


def calculate_metrics(answer: str, correct_answer: str):
    """
    回答と正解から各種評価指標を計算して返します。

    Returns:
        bleu_score        : 0.0～1.0 の BLEU スコア
        similarity_score  : 0.0～1.0 の TF-IDF コサイン類似度
        word_count        : 回答の単語数
        relevance_score   : 正解との共通単語比率 (0.0～1.0)
    """
    # 初期値
    bleu_score = 0.0
    similarity_score = 0.0
    word_count = 0
    relevance_score = 0.0

    if not answer:
        return bleu_score, similarity_score, word_count, relevance_score

    # 1) 単語数
    tokenizer = Tokenizer()
    tokens = list(tokenizer.tokenize(answer))
    word_count = len(tokens)

    # 正解がある場合のみその他を計算
    if correct_answer:
        ans_lower = answer.lower()
        corr_lower = correct_answer.lower()

        # 2) BLEU (4-gram)
        try:
            ref = [word_tokenize(corr_lower)]
            cand = word_tokenize(ans_lower)
            if cand:
                bleu_score = sentence_bleu(ref, cand,
                                          weights=(0.25, 0.25, 0.25, 0.25))
        except Exception:
            bleu_score = 0.0

        # 3) TF-IDF コサイン類似度
        try:
            vec = TfidfVectorizer()
            tfidf = vec.fit_transform([ans_lower, corr_lower])
            similarity_score = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        except Exception:
            similarity_score = 0.0

        # 4) 共通単語比率（関連性スコア）
        try:
            ans_words = set(re.findall(r'\w+', ans_lower))
            corr_words = set(re.findall(r'\w+', corr_lower))
            if corr_words:
                relevance_score = len(ans_words & corr_words) / len(corr_words)
        except Exception:
            relevance_score = 0.0

    return bleu_score, similarity_score, word_count, relevance_score


def get_metrics_descriptions():
    """
    各評価指標の説明を返します。
    """
    return {
        "BLEU スコア": "機械翻訳評価指標。正解文と出力文の n-gram 一致度を 0～1 で示します。",
        "コサイン類似度": "TF-IDF ベクトル間のコサイン類似度。意味的な近さを 0～1 で示します。",
        "単語数": "回答に含まれる単語（形態素）の数。情報量の指標です。",
        "関連性スコア": "正解文と回答文の共通単語比率(0～1)。トピックの一致度を示します。"}