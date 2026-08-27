import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from src.features.schema import NUMERICAL_FEATURES, CATEGORICAL_FEATURES, validate_input_schema


class TextileFeatureEngineer(BaseEstimator, TransformerMixin):
    """Computes domain specific proxy features for FibreOptima pipeline."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        validate_input_schema(X)
        df = X.copy()
        df["Waste percentage"] = (df["Waste quantity"] / df["Production quantity"].replace(0, 1)) * 100
        df["High speed"] = (df["Production speed"] > 250).astype(float)
        df["Old machine"] = (df["Machine age"] > 10).astype(float)
        df["Missing humidity"] = df["Humidity"].isna().astype(float)
        return df


def build_preprocessor():
    """Builds scikit-learn preprocessing pipeline aligned with FEATURE_SCHEMA."""
    num_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    cat_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, NUMERICAL_FEATURES),
            ("cat", cat_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return Pipeline(
        steps=[
            ("engineer", TextileFeatureEngineer()),
            ("preprocessor", preprocessor),
        ]
    )
