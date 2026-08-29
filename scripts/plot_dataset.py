"""Quick figures for the paper: density vs modulus/strength coloured by matrix class."""
import matplotlib.pyplot as plt
import pandas as pd

from foamgpt.config import BENCH_DIR
from foamgpt.curate.normalize import CURATED

df = pd.read_csv(CURATED)
df = df[(df["flags"].fillna("") == "") & (df["test_type"] == "compression")]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for ax, col in zip(axes, ["modulus_mpa", "strength_mpa"]):
    for mc, g in df.dropna(subset=[col, "measured_density_g_cc"]).groupby("matrix_class"):
        ax.scatter(g["measured_density_g_cc"], g[col], s=14, alpha=0.7, label=mc)
    ax.set_xlabel("density (g/cm³)"); ax.set_ylabel(col); ax.set_yscale("log")
axes[0].legend(fontsize=7)
fig.tight_layout(); fig.savefig(BENCH_DIR / "density_maps.png", dpi=200)
print("saved", BENCH_DIR / "density_maps.png")
