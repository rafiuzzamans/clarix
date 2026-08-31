import time
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

def run():
    cfpb = pd.read_csv("c:/Project/ml/data/processed/cfpb_clean.csv")
    fpb = pd.read_csv("c:/Project/ml/data/processed/fpb_clean.csv")

    cfpb_subset = cfpb.sample(n=10000, random_state=42)
    fpb_subset = fpb.sample(min(10000, len(fpb)), random_state=42)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "LinearSVC (Calibrated)": CalibratedClassifierCV(LinearSVC(class_weight="balanced", dual=False, random_state=42)),
        "Multinomial Naive Bayes": MultinomialNB(),
        "Random Forest": RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    }

    print(f"{'Model':<30} | {'Category F1':<12} | {'Priority F1':<12} | {'Sentiment F1':<12}")
    print("-" * 75)

    for name, clf in models.items():
        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=10000, sublinear_tf=True)),
            ("clf", clf)
        ])
        
        # Category
        X_train, X_test, y_train, y_test = train_test_split(cfpb_subset['cleaned_text'], cfpb_subset['category'], test_size=0.2, random_state=42)
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        f1_cat = f1_score(y_test, y_pred, average="weighted")
        
        # Priority
        X_train, X_test, y_train, y_test = train_test_split(cfpb_subset['cleaned_text'], cfpb_subset['priority'], test_size=0.2, random_state=42)
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        f1_pri = f1_score(y_test, y_pred, average="weighted")
        
        # Sentiment
        X_train, X_test, y_train, y_test = train_test_split(fpb_subset['cleaned_text'], fpb_subset['sentiment'], test_size=0.2, random_state=42)
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        f1_sen = f1_score(y_test, y_pred, average="weighted")
        
        print(f"{name:<30} | {f1_cat:.3f}        | {f1_pri:.3f}        | {f1_sen:.3f}")

if __name__ == '__main__':
    run()
