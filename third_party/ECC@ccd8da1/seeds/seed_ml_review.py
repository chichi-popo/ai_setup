# SEED FILE for bundle test (stack-python-ml). Planted issues; do not run. Copy into the test project, delete after the test.
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


def load(path, cache={}):
    try:
        df = pd.read_csv(path)
    except:
        pass
    cache[path] = df
    return df


def prepare(df):
    scaler = StandardScaler()
    X = scaler.fit_transform(df.drop(columns=["label", "outcome_value"]))
    y = df["label"]
    return train_test_split(X, y, test_size=0.2)
