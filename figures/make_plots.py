"""Regenerate the computed figures of the paper (Figures 6, 8 and 9).

Figure 6  worked checksum-localization example (all values computed exactly)
Figure 8  Eq. 6, verification cost / computation cost for dense matmul
Figure 9  Eq. 9, expected waste vs. period for three forward-recovery rates

Figures 8 and 9 are analytical curves, not measurements. The parameters of
Figure 9 (V + C = 120 s, lambda = 1/21600 s^-1) are hypothetical and are used
only to illustrate the model.

Usage:  python figures/make_plots.py [--outdir figures/out]
"""

import argparse, os

import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10})

_ap = argparse.ArgumentParser()
_ap.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "out"))
OUT = _ap.parse_args().outdir
os.makedirs(OUT, exist_ok=True)
_p = lambda name: os.path.join(OUT, name)

# ---- Fig 6: checksum localization toy example ----
A = np.array([[1,2,0,1],[0,1,3,2],[2,0,1,1],[1,1,1,0]])
B = np.array([[2,1,0,1],[1,0,2,1],[0,3,1,2],[1,1,1,1]])
C = A@B
Cc = C.copy(); ei, ej, e = 1, 2, 5   # row 2, column 3 (1-based), error +5
Cc[ei,ej] += e
w1 = np.ones(4); w2 = np.arange(1,5)
d1 = Cc@w1 - A@(B@w1); d2 = Cc@w2 - A@(B@w2)
print("C=",C.tolist(),"d1=",d1,"d2=",d2)
fig, ax = plt.subplots(figsize=(8.2,3.3)); ax.axis("off")
x0,y0,s = 0.3, 3.6, 0.8
ax.text(x0+1.6, y0+0.35, "Computed product C", ha="center", fontsize=10, weight="bold")
for i in range(4):
    for j in range(4):
        bad = (i==ei and j==ej)
        ax.add_patch(Rectangle((x0+j*s, y0-(i+1)*s), s, s, fc="#FADBD8" if bad else "white", ec="#34495E"))
        ax.text(x0+j*s+s/2, y0-(i+1)*s+s/2, str(int(Cc[i,j])), ha="center", va="center", fontsize=11, weight="bold" if bad else "normal")
    ax.text(x0-0.18, y0-(i+1)*s+s/2, f"row {i+1}", ha="right", va="center", fontsize=8)
for j in range(4):
    ax.text(x0+j*s+s/2, y0+0.08, f"col {j+1}", ha="center", fontsize=8)
x1 = x0+4*s+0.9
ax.text(x1+0.85, y0+0.35, "Discrepancies", ha="center", fontsize=10, weight="bold")
for k,(lab,d) in enumerate([("δ\u2081 (w\u207d\u00b9\u207e = ones)", d1), ("δ\u2082 (w\u207d\u00b2\u207e = 1,2,3,4)", d2)]):
    ax.text(x1+k*s*1.1+s/2, y0+0.08, ["δ\u2081","δ\u2082"][k], ha="center", fontsize=9)
    for i in range(4):
        nz = d[i]!=0
        ax.add_patch(Rectangle((x1+k*s*1.1, y0-(i+1)*s), s, s, fc="#FCF3CF" if nz else "white", ec="#34495E"))
        ax.text(x1+k*s*1.1+s/2, y0-(i+1)*s+s/2, f"{int(d[i])}", ha="center", va="center", fontsize=11)
x2 = x1+2.6
txt = (f"Row {ei+1} is the only row with a nonzero discrepancy.\n\n"
       f"Column index:  j = δ\u2082 / δ\u2081 = {int(d2[ei])} / {int(d1[ei])} = {int(d2[ei]/d1[ei])}\n\n"
       f"Correction:  C[{ei+1},{int(d2[ei]/d1[ei])}] \u2190 {int(Cc[ei,ej])} \u2212 {int(d1[ei])} = {int(Cc[ei,ej]-d1[ei])}\n\n"
       f"(Correct value from A\u00b7B: {int(C[ei,ej])})")
ax.text(x2, y0-2.0, txt, va="center", fontsize=9.5, bbox=dict(fc="#EEF2F7", ec="#34495E"))
ax.set_xlim(-0.6, 11.2); ax.set_ylim(0, 4.1)
plt.savefig(_p("fig6.png"), dpi=220, bbox_inches="tight"); plt.close()

# ---- Fig 8: verification/computation ratio ----
n = np.logspace(2, 5, 200)
fig, ax = plt.subplots(figsize=(6.4,3.6))
for k,ls in [(1,"-"),(5,"--"),(10,":")]:
    ax.loglog(n, 3*k*n**2/n**3, ls, color="#34495E", label=f"k = {k} trials")
ax.set_xlabel("Matrix dimension n"); ax.set_ylabel("Verification / computation\n(floating-point operations)")
ax.grid(True, which="both", alpha=0.3); ax.legend(frameon=False)
plt.tight_layout(); plt.savefig(_p("fig8.png"), dpi=220); plt.close()

# ---- Fig 9: waste curves ----
VC, lam = 120.0, 1/21600.0
T = np.linspace(200, 12000, 600); rows=[]
fig, ax = plt.subplots(figsize=(6.4,3.8))
for pc,ls in [(0,"-"),(0.5,"--"),(0.75,":")]:
    W = VC/T + lam*(1-pc)*T
    Ts = np.sqrt(VC/(lam*(1-pc))); Ws = 2*np.sqrt(lam*(1-pc)*VC)
    ax.plot(T, W*100, ls, color="#34495E", label=f"$p_c$ = {pc}")
    ax.plot(Ts, Ws*100, "o", color="#C0392B", ms=5)
    rows.append(f"$p_c$ = {pc}:  T* = {Ts:,.0f} s,  W* = {Ws*100:.1f}%")
    print(pc, Ts, Ws)
ax.text(8450, 34.5, "Optima (red markers)\n"+"\n".join(rows), fontsize=7, va="center", bbox=dict(fc="white", ec="#34495E"))
ax.set_xlabel("Verification-and-checkpoint period T (seconds)"); ax.set_ylabel("Expected waste W(T) (%)")
ax.set_ylim(0, 40); ax.grid(True, alpha=0.3); ax.legend(frameon=False, loc="lower right")
plt.tight_layout(); plt.savefig(_p("fig9.png"), dpi=220); plt.close()
