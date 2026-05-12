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


class TestSyntheticDataGeneration:
    def test_generates_correct_count(self):
        from app.ml.train import generate_synthetic_dataset
        df = generate_synthetic_dataset(100)
        assert len(df) == 100

    def test_has_required_columns(self):
        from app.ml.train import generate_synthetic_dataset
        df = generate_synthetic_dataset(50)
        for col in ["text", "category", "priority", "sentiment", "cleaned_text"]:
            assert col in df.columns

    def test_categories_are_valid(self):
        from app.ml.train import generate_synthetic_dataset
        df = generate_synthetic_dataset(200)
        VALID = {"billing","technical_support","account","shipping","returns",
                 "product_inquiry","complaint","feedback"}
        assert set(df["category"].unique()).issubset(VALID)

    def test_priorities_are_valid(self):
        from app.ml.train import generate_synthetic_dataset
        df = generate_synthetic_dataset(200)
        assert set(df["priority"].unique()).issubset({"low","medium","high","urgent"})

    def test_sentiments_are_valid(self):
        from app.ml.train import generate_synthetic_dataset
        df = generate_synthetic_dataset(200)
        assert set(df["sentiment"].unique()).issubset({"positive","neutral","negative"})

    def test_no_empty_texts(self):
        from app.ml.train import generate_synthetic_dataset
        df = generate_synthetic_dataset(100)
        assert not df["text"].str.strip().eq("").any()


class TestPredictorFallback:
    """Test the predictor returns safe defaults when models aren't loaded."""

    def test_returns_default_when_not_ready(self):
        from app.ml.predictor import predict, registry
        # Force unloaded state
        registry.category_model = None
        registry._loaded = False

        result = predict("I need help with my account")
        assert result["label_category"] == "other"
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
        from app.ml.train import build_pipeline
        pipeline = build_pipeline(LogisticRegression(max_iter=100))
        assert pipeline is not None
        assert "tfidf" in pipeline.named_steps
        assert "clf" in pipeline.named_steps

    def test_tfidf_config(self):
        from app.ml.train import build_pipeline
        from sklearn.linear_model import LogisticRegression
        pipeline = build_pipeline(LogisticRegression())
        tfidf = pipeline.named_steps["tfidf"]
        assert tfidf.ngram_range == (1, 2)
        assert tfidf.max_features == 10000
        assert tfidf.sublinear_tf is True

    @pytest.mark.slow
    def test_full_training_run(self, tmp_path):
        """Full training pipeline — marked as slow, skipped in fast CI."""
        import os
        from app.ml.train import train_all
        # Override models dir
        os.environ["MODELS_PATH"] = str(tmp_path)
        results = train_all()
        for model_name in ["category", "priority", "sentiment"]:
            assert model_name in results
            assert results[model_name]["accuracy"] > 0.3  # reasonable floor
