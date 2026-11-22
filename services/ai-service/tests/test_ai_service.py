"""
AI Service — Unit Tests
Tests the ML prediction pipeline, text cleaning, and model inference.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestTextCleaning:
    def _clean(self, text: str) -> str:
        from app.ml.predictor import clean_text
        return clean_text(text)

    def test_lowercases_text(self):
        result = self._clean("HELLO WORLD")
        assert result == result.lower()

    def test_removes_urls(self):
        result = self._clean("visit http://example.com for more info")
        assert "http" not in result
        assert "example" not in result

    def test_removes_special_characters(self):
        result = self._clean("order #12345 — status: shipped!")
        assert "#" not in result
        assert "—" not in result
        assert "!" not in result

    def test_removes_stopwords(self):
        result = self._clean("I would like to have a refund please")
        # Common stopwords removed
        assert " i " not in f" {result} "
        assert " the " not in f" {result} "

    def test_empty_string(self):
        result = self._clean("")
        assert result == ""

    def test_whitespace_collapses(self):
        result = self._clean("hello   world")
        assert "  " not in result


class TestClassBalancing:
    """balance_classes() caps large classes and upsamples small ones."""

    def _df(self):
        import pandas as pd
        rows = ([("a b c", "big")] * 50) + ([("d e f", "small")] * 5)
        return pd.DataFrame(rows, columns=["text", "label"])

    def test_caps_majority_class(self):
        from app.ml.train import balance_classes
        out = balance_classes(self._df(), "text", "label", max_per_class=20, min_per_class=10)
        assert (out["label"] == "big").sum() == 20

    def test_upsamples_minority_class(self):
        from app.ml.train import balance_classes
        out = balance_classes(self._df(), "text", "label", max_per_class=20, min_per_class=10)
        assert (out["label"] == "small").sum() == 10

    def test_keeps_columns(self):
        from app.ml.train import balance_classes
        out = balance_classes(self._df(), "text", "label", max_per_class=20, min_per_class=10)
        assert list(out.columns) == ["text", "label"]


class TestPredictorFallback:
    """Test the predictor returns safe defaults when models aren't loaded."""

    def test_returns_default_when_not_ready(self):
        from app.ml.predictor import predict, registry
        # Force unloaded state
        registry.category_model = None
        registry._loaded = False

        result = predict("I need help with my account")
        assert result["label_category"] == "bank_account"  # safe default label
        assert result["label_priority"] == "medium"
        assert result["label_sentiment"] == "neutral"
        assert result["confidence"] == 0.0

    def test_returns_dict_structure(self):
        from app.ml.predictor import predict, registry
        registry._loaded = False
        registry.category_model = None

        result = predict("test")
        # Must contain all required flat convenience keys
        for key in ["label_category", "label_priority", "label_sentiment", "confidence"]:
            assert key in result
        # Must contain nested result objects
        for key in ["category", "priority", "sentiment", "explanation"]:
            assert key in result


class TestModelTraining:
    """Integration tests for training pipeline (runs if models directory exists)."""

    def test_pipeline_builds(self):
        from sklearn.linear_model import LogisticRegression
        from app.ml.train import tfidf_pipeline
        pipeline = tfidf_pipeline(LogisticRegression(max_iter=100))
        assert pipeline is not None
        assert "tfidf" in pipeline.named_steps
        assert "clf" in pipeline.named_steps

    def test_tfidf_config(self):
        from app.ml.train import tfidf_pipeline
        from sklearn.linear_model import LogisticRegression
        pipeline = tfidf_pipeline(LogisticRegression())
        tfidf = pipeline.named_steps["tfidf"]
        assert tfidf.ngram_range == (1, 2)
        assert tfidf.max_features == 15000
        assert tfidf.sublinear_tf is True

    def test_pipeline_fits_and_predicts(self):
        from sklearn.linear_model import LogisticRegression
        from app.ml.train import tfidf_pipeline
        X = ["mortgage escrow foreclosure", "student loan servicer deferment"] * 5
        y = ["mortgage", "student_loan"] * 5
        pipe = tfidf_pipeline(LogisticRegression(max_iter=100))
        pipe.set_params(tfidf__min_df=1)
        pipe.fit(X, y)
        assert pipe.predict(["escrow foreclosure"])[0] == "mortgage"
