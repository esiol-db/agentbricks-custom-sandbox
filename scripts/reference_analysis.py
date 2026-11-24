"""Reference A/B analysis used to check the agent's answers. Runs in the custom sandbox image.

Usage: python3 reference_analysis.py /Volumes/main/default/ab_data/checkout_button_test.csv
"""
import sys

import duckdb
import pandas as pd
import pingouin as pg
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import (confint_proportions_2indep, proportion_effectsize,
                                          proportions_ztest)

df = pd.read_csv(sys.argv[1])
s = duckdb.sql("""select variant, count(*) n, sum(converted) conv, avg(revenue) rpv
                  from df group by 1 order by 1""").df().set_index("variant")
n_c, n_t = int(s.n["control"]), int(s.n["treatment"])
x_c, x_t = int(s.conv["control"]), int(s.conv["treatment"])
p_c, p_t = x_c / n_c, x_t / n_t

print(f"SRM            n={n_c:,} vs {n_t:,}  chi2 p={stats.chisquare([n_c, n_t]).pvalue:.2f}")
z, p = proportions_ztest([x_t, x_c], [n_t, n_c])
lo, hi = confint_proportions_2indep(x_t, n_t, x_c, n_c, method="wald")
h = proportion_effectsize(p_t, p_c)
power_conv = NormalIndPower().power(effect_size=h, nobs1=n_t, ratio=n_c / n_t, alpha=0.05)
n_needed = NormalIndPower().solve_power(effect_size=h, power=0.8, alpha=0.05, ratio=1.0)
print(f"Conversion     {p_c:.3%} -> {p_t:.3%}  diff={100*(p_t-p_c):+.3f} pp "
      f"CI95=[{100*lo:+.2f}, {100*hi:+.2f}] pp  z={z:.2f} p={p:.3f}")
print(f"               power={power_conv:.0%}  n/arm for 80% power={n_needed:,.0f}")
r = pg.ttest(df[df.variant == "treatment"].revenue, df[df.variant == "control"].revenue,
             correction=True)
print(f"Revenue/visitor ${s.rpv['control']:.2f} -> ${s.rpv['treatment']:.2f}  "
      f"Welch p={r['p_val'].iloc[0]:.3f} d={r['cohen_d'].iloc[0]:.3f} power={r['power'].iloc[0]:.0%}")
