"""
Titanic モデルの検証用テストスイート.

- 精度 (>= 0.75)
- 推論時間 (< 1.0 s)
- 再現性 (同一 seed で同一予測)
- モデルファイルの存在確認
"""

from __future__ import annotations

import pickle
import time
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.datasets import fetch_openml
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# --------------------------------------------------
# 定数・パス設定
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "Titanic.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "titanic_model.pkl"

NUMERIC_COLS = ["Age", "Pclass", "SibSp", "Parch", "Fare"]
CATEGORICAL_COLS = ["Sex", "Embarked"]
TARGET_COL = "Survived"
SEED = 42


# --------------------------------------------------
# 共通フィクスチャ
# --------------------------------------------------
@pytest.fixture(scope="session")
def titanic_df() -> pd.DataFrame:
    """Titanic データを取得し CSV キャッシュ."""
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH)

    df = fetch_openml("titanic", version=1, as_frame=True).frame
    df = df[NUMERIC_COLS + CATEGORICAL_COLS + [TARGET_COL]]  # 必要列だけ残す
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    return df


@pytest.fixture(scope="session")
def preprocessor() -> ColumnTransformer:
    """数値/カテゴリ前処理を返す."""
    num_pipe = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    cat_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        [("num", num_pipe, NUMERIC_COLS), ("cat", cat_pipe, CATEGORICAL_COLS)]
    )


@pytest.fixture(scope="session")
def trained_model(
    titanic_df: pd.DataFrame, preprocessor: ColumnTransformer
) -> Tuple[Pipeline, pd.DataFrame, pd.Series]:
    """モデルを学習し、必要なオブジェクトを返す."""
    X = titanic_df.drop(TARGET_COL, axis=1)
    y = titanic_df[TARGET_COL].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED)

    model = Pipeline(
        [
            ("pre", preprocessor),
            ("clf", RandomForestClassifier(n_estimators=100, random_state=SEED)),
        ]
    ).fit(X_tr, y_tr)

    MODEL_DIR.mkdir(exist_ok=True)
    with MODEL_PATH.open("wb") as f:
        pickle.dump(model, f)

    return model, X_te, y_te


# --------------------------------------------------
# テストケース
# --------------------------------------------------
def test_model_file_exists(
    trained_model: Tuple[Pipeline, pd.DataFrame, pd.Series],
) -> None:  # noqa: D103
    assert MODEL_PATH.exists(), "モデルファイルが保存されていません。"


def test_accuracy(
    trained_model: Tuple[Pipeline, pd.DataFrame, pd.Series],
) -> None:  # noqa: D103
    model, X_te, y_te = trained_model
    acc = accuracy_score(y_te, model.predict(X_te))
    assert acc >= 0.75, f"精度が低すぎます (acc={acc:.3f})"


def test_inference_time(
    trained_model: Tuple[Pipeline, pd.DataFrame, pd.Series],
) -> None:  # noqa: D103
    model, X_te, _ = trained_model
    start = time.perf_counter()
    model.predict(X_te)
    duration = time.perf_counter() - start
    assert duration < 1.0, f"推論に時間がかかりすぎています ({duration:.2f}s)"


def test_reproducibility(
    preprocessor: ColumnTransformer, titanic_df: pd.DataFrame
) -> None:  # noqa: D103
    X = titanic_df.drop(TARGET_COL, axis=1)
    y = titanic_df[TARGET_COL].astype(int)
    X_tr, X_te, y_tr, _ = train_test_split(X, y, test_size=0.2, random_state=SEED)

    def build() -> Pipeline:
        return Pipeline(
            [
                ("pre", preprocessor),
                ("clf", RandomForestClassifier(n_estimators=100, random_state=SEED)),
            ]
        ).fit(X_tr, y_tr)

    pred1 = build().predict(X_te)
    pred2 = build().predict(X_te)
    assert np.array_equal(pred1, pred2), "同一シードでも予測が一致しません。"
