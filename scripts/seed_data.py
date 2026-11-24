"""Generate a synthetic checkout-button A/B test (one row per visitor)."""
import os
import sys

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n_control, n_treat = 24_890, 25_110
def arm(name, n, p_conv, mean_rev):
    converted = rng.random(n) < p_conv
    revenue = np.where(converted, rng.gamma(shape=2.0, scale=mean_rev / 2.0, size=n), 0.0)
    return pd.DataFrame({
        "visitor_id": [f"{name[0]}{i:06d}" for i in range(n)],
        "variant": name,
        "device": rng.choice(["desktop", "mobile", "tablet"], size=n, p=[0.45, 0.48, 0.07]),
        "converted": converted.astype(int),
        "revenue": revenue.round(2),
    })
df = pd.concat([arm("control", n_control, 0.0410, 58.0), arm("treatment", n_treat, 0.0452, 57.0)])
df = df.sample(frac=1, random_state=7).reset_index(drop=True)
out = sys.argv[1] if len(sys.argv) > 1 else "checkout_button_test.csv"
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
df.to_csv(out, index=False)
print(out, len(df), df.groupby("variant")["converted"].mean().round(4).to_dict())
