# data.py

"""
一般知識クイズ用のサンプルデータを定義するモジュール
メモリ上で問題を保持し、DB投入は行いません。
"""

# サンプルクイズデータのリスト
# 各要素は
#  - question: 問題文（文字列）
#  - options : 選択肢のリスト（文字列のリスト）
#  - answer  : 正解選択肢のインデックス（0始まり）
SAMPLE_QUESTIONS_DATA = [
    {
        "question": "日本の首都はどこですか？",
        "options": ["大阪", "京都", "東京", "名古屋"],
        "answer": 2
    },
    {
        "question": "月は地球のまわりを何時間で一周しますか？",
        "options": ["24時間", "27.3時間", "30時間", "72時間"],
        "answer": 1
    },
    {
        "question": "世界で最も人口が多い国はどこですか？",
        "options": ["インド", "アメリカ合衆国", "中国", "ロシア"],
        "answer": 2
    },
    {
        "question": "フランスの有名なエッフェル塔がある都市はどこですか？",
        "options": ["リヨン", "パリ", "マルセイユ", "ニース"],
        "answer": 1
    },
    {
        "question": "水の沸点は何度（℃）ですか？",
        "options": ["90℃", "100℃", "110℃", "120℃"],
        "answer": 1
    },
    {
        "question": "世界三大料理に含まれないものはどれですか？",
        "options": ["中華料理", "フランス料理", "イタリア料理", "アメリカ料理"],
        "answer": 3
    },
    {
        "question": "ピカソはどの国の画家ですか？",
        "options": ["スペイン", "イタリア", "フランス", "ドイツ"],
        "answer": 0
    },
    {
        "question": "サッカーのワールドカップは何年ごとに開催されますか？",
        "options": ["2年", "3年", "4年", "5年"],
        "answer": 2
    },
    {
        "question": "光の速さはおよそ何km/sですか？",
        "options": ["3万km/s", "30万km/s", "300万km/s", "3000km/s"],
        "answer": 1
    },
    {
        "question": "太陽系で最も大きい惑星は何ですか？",
        "options": ["地球", "火星", "木星", "土星"],
        "answer": 2
    }
]

def get_sample_questions():
    """
    SAMPLE_QUESTIONS_DATA のディープコピーを返します。
    アプリ起動時に何度でも同じリストを使いたい場合はこちらを呼び出してください。
    """
    import copy
    return copy.deepcopy(SAMPLE_QUESTIONS_DATA)