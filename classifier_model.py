import pandas as pd, numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib, os

class ClassifierModel:
    def __init__(self, model_path="classifier_model.pkl"):
        self.model_path = model_path
        self.model = None
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
            except Exception:
                self.model = None

    def create_labels(self, df, horizon=3, ret_thresh=0.01):
        df = df.copy().sort_values("date").reset_index(drop=True)
        df["future_close"] = df["close"].shift(-horizon)
        df["future_ret"] = df["future_close"]/df["close"] - 1.0
        df["label"] = (df["future_ret"] > ret_thresh).astype(int)
        df = df.dropna().reset_index(drop=True)
        return df

    def featurize(self, df):
        df = df.copy().sort_values("date").reset_index(drop=True)
        df["ret1"] = df["close"].pct_change().fillna(0)
        for lag in range(1,6):
            df[f"lag{lag}"] = df["close"].shift(lag).fillna(method="bfill")
        df["ma10"] = df["close"].rolling(10).mean().fillna(method="bfill")
        df["vol_ma10"] = df["volume"].rolling(10).mean().fillna(0)
        features = ["ret1","lag1","lag2","lag3","lag4","lag5","ma10","vol_ma10"]
        return df, df[features]

    def train(self, df, horizon=3, ret_thresh=0.01):
        df_l = self.create_labels(df, horizon=horizon, ret_thresh=ret_thresh)
        df_feats, X = self.featurize(df_l)
        y = df_l["label"]
        if len(X) < 50:
            raise ValueError("Not enough data to train classifier (need ~50 rows).")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        clf = RandomForestClassifier(n_estimators=200, random_state=42)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        proba = clf.predict_proba(X_test)[:,1]
        metrics = {"accuracy": float(accuracy_score(y_test, preds)), "roc_auc": float(roc_auc_score(y_test, proba))}
        self.model = clf
        try:
            joblib.dump(clf, self.model_path)
        except Exception:
            pass
        return metrics

    def predict_from_signals(self, hist, forms_df=None, headlines_df=None, horizon=3):
        if hist is None or hist.empty:
            return {"prob_pos":0.0, "metrics":{}, "features":{}}
        df, X = self.featurize(hist)
        lastX = X.iloc[[-1]]
        if self.model is None:
            try:
                self.train(hist, horizon=horizon)
            except Exception:
                pass
        if self.model is None:
            return {"prob_pos":0.0, "metrics":{}, "features":{}}
        proba = float(self.model.predict_proba(lastX)[0][1])
        return {"prob_pos": proba, "metrics":{}, "features":{}}