#!/usr/bin/env python3
"""Genera las tablas y figuras del artículo a partir de experimento/.

Uso:
    python docs/scripts/analyze.py

No modifica backend/, frontend/ ni experimento/. Escribe en docs/tablas/
y docs/figuras/. Todas las cifras se calculan desde los CSV; no hay valores
codificados a mano salvo las etiquetas de presentación.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experimento"
TAB = ROOT / "docs" / "tablas"
FIG = ROOT / "docs" / "figuras"
TAB.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- estilo
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.6,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
)
OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
BLUE, VERMIL, GREEN, PURPLE, ORANGE, SKY = OKABE[:6]
GREY = "#6B7280"
CMAP = LinearSegmentedColormap.from_list(
    "cis", ["#B2182B", "#F4A582", "#F7F7F7", "#92C5DE", "#2166AC"]
)


def load(name: str) -> list[dict]:
    with open(EXP / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    with open(TAB / name, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def ci95(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n < 2:
        return (values[0], values[0]) if values else (0.0, 0.0)
    m = st.mean(values)
    se = st.stdev(values) / math.sqrt(n)
    # t de Student, aproximación para 2 <= n <= 60 (tabla reducida)
    tcrit = {39: 2.0227, 38: 2.0244, 37: 2.0262, 5: 2.5706}.get(n - 1, 1.96)
    return m - tcrit * se, m + tcrit * se


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = 1.959964
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def bootstrap_rate(flags: list[bool], seed: int = 20261104, reps: int = 10000) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(flags)
    values = []
    for _ in range(reps):
        values.append(sum(flags[rng.randrange(n)] for _ in range(n)) / n)
    values.sort()
    return values[int(0.025 * reps)], values[int(0.975 * reps) - 1]


# --------------------------------------------------------------------------- datos
servers = load("servers.csv")
controls = load("controls.csv")
runs = load("audit_runs.csv")
checks = load("check_results.csv")
findings = load("findings.csv")

clean = [r for r in checks if not r["injected_fault"]]
faulty = [r for r in checks if r["injected_fault"]]
code_order = [c["control_code"] for c in controls]
control_by_code = {c["control_code"]: c for c in controls}
host_by_id = {s["host_id"]: s for s in servers}


def is_true(value: str) -> bool:
    return value == "True"


def pct(num: float, den: float) -> float:
    return 100.0 * num / den if den else 0.0


# --------------------------------------------------------------------------- métricas
status_counts = Counter(r["status"] for r in checks)
gt_counts = Counter(r["ground_truth"] for r in checks)

TP = sum(1 for r in clean if r["ground_truth"] == "failed" and r["status"] == "failed")
FP = sum(1 for r in clean if r["ground_truth"] == "passed" and r["status"] == "failed")
FN = sum(1 for r in clean if r["ground_truth"] == "failed" and r["status"] == "passed")
TN = sum(1 for r in clean if r["ground_truth"] == "passed" and r["status"] == "passed")
N_BIN = TP + FP + FN + TN
precision = TP / (TP + FP)
recall = TP / (TP + FN)
f1 = 2 * precision * recall / (precision + recall)
accuracy = (TP + TN) / N_BIN
pe = ((TP + FP) * (TP + FN) + (FN + TN) * (FP + TN)) / (N_BIN**2)
kappa = (accuracy - pe) / (1 - pe)
exact = sum(1 for r in clean if is_true(r["match"]))
exact_rate = exact / len(clean)

# Hallazgos del motor: desacuerdos por control
disagreement_by_control = Counter(
    r["control_code"] for r in clean if not is_true(r["match"])
)
fp_by_control = Counter(
    r["control_code"]
    for r in clean
    if r["status"] == "failed" and r["ground_truth"] == "passed"
)
fn_by_control = Counter(
    r["control_code"]
    for r in clean
    if r["status"] == "passed" and r["ground_truth"] == "failed"
)

# Rondas
round_rows = []
round_scores = {}
for rnd in range(1, 7):
    rr = [r for r in runs if int(r["round"]) == rnd]
    vals = [float(r["compliance_pct"]) for r in rr if r["compliance_pct"] != ""]
    round_scores[rnd] = vals
    durations = [int(r["total_duration_ms"]) for r in rr if int(r["total_duration_ms"]) > 0]
    round_rows.append(
        {
            "round": rnd,
            "n": len(rr),
            "mean": st.mean(vals),
            "sd": st.stdev(vals),
            "median": st.median(vals),
            "min": min(vals),
            "max": max(vals),
            "coverage": st.mean(float(r["coverage_pct"]) for r in rr),
            "not_evaluated": sum(int(r["not_evaluated"]) for r in rr),
            "unreachable": sum(1 for r in rr if r["run_outcome"] == "unreachable"),
            "duration": st.mean(durations),
        }
    )

# Prueba pareada ronda 1 vs ronda 6
host_scores = defaultdict(dict)
for r in runs:
    if r["compliance_pct"] != "":
        host_scores[r["host_id"]][int(r["round"])] = float(r["compliance_pct"])
paired = [
    host_scores[h][6] - host_scores[h][1]
    for h in host_scores
    if 1 in host_scores[h] and 6 in host_scores[h]
]
n_paired = len(paired)
mean_diff = st.mean(paired)
sd_diff = st.stdev(paired)
se_diff = sd_diff / math.sqrt(n_paired)
t_stat = mean_diff / se_diff
dz = mean_diff / sd_diff
tcrit = 2.0244  # t(0.975, 38)
diff_ci = (mean_diff - tcrit * se_diff, mean_diff + tcrit * se_diff)

# Trayectorias por subgrupo
def trajectory(field: str, value: str) -> list[float]:
    hosts = [s["host_id"] for s in servers if s[field] == value]
    out = []
    for rnd in range(1, 7):
        vals = [
            host_scores[h][rnd]
            for h in hosts
            if rnd in host_scores[h]
        ]
        out.append(st.mean(vals))
    return out


groups = {
    "hardened": trajectory("archetype", "hardened"),
    "partial": trajectory("archetype", "partial"),
    "default_install": trajectory("archetype", "default_install"),
    "neglected": trajectory("archetype", "neglected"),
    "production": trajectory("environment", "production"),
    "staging": trajectory("environment", "staging"),
    "development": trajectory("environment", "development"),
}

# Hallazgos
findings_total = len(findings)
findings_resolved = sum(1 for f in findings if f["status"] == "resolved")
findings_open = sum(1 for f in findings if f["status"] == "open")
findings_reopened = sum(1 for f in findings if is_true(f["reopened"]))
findings_by_sev = {}
for sev in ("high", "medium"):
    rows = [f for f in findings if f["severity"] == sev]
    open_rows = [f for f in rows if f["status"] == "open"]
    resolved_rows = [f for f in rows if f["status"] == "resolved"]
    findings_by_sev[sev] = {
        "total": len(rows),
        "resolved": len(resolved_rows),
        "open": len(open_rows),
        "reopened": sum(1 for f in rows if is_true(f["reopened"])),
        "median_open_rounds": st.median(int(f["rounds_open"]) for f in rows),
        "max_open_rounds": max(int(f["rounds_open"]) for f in rows),
    }

# Duración por control
dur_by_control = {
    code: [int(r["duration_ms"]) for r in checks if r["control_code"] == code]
    for code in code_order
}
all_durations = [int(r["duration_ms"]) for r in checks if int(r["duration_ms"]) > 0]
run_durations = [int(r["total_duration_ms"]) for r in runs if int(r["total_duration_ms"]) > 0]

metrics = {
    "rows_total": len(checks),
    "runs_total": len(runs),
    "hosts": len(servers),
    "controls": len(controls),
    "status_counts": dict(status_counts),
    "gt_counts": dict(gt_counts),
    "faults": dict(Counter(r["injected_fault"] for r in checks)),
    "clean_rows": len(clean),
    "exact_matches": exact,
    "exact_rate_pct": pct(exact, len(clean)),
    "confusion": {"TP": TP, "FP": FP, "FN": FN, "TN": TN},
    "precision_pct": 100 * precision,
    "recall_pct": 100 * recall,
    "f1_pct": 100 * f1,
    "accuracy_bin_pct": 100 * accuracy,
    "kappa": kappa,
    "accuracy_wilson": [100 * x for x in wilson(TP + TN, N_BIN)],
    "precision_bootstrap": [100 * x for x in bootstrap_rate(
        [r["ground_truth"] == "failed" for r in clean if r["status"] == "failed"]
    )],
    "recall_bootstrap": [100 * x for x in bootstrap_rate(
        [r["status"] == "failed" for r in clean if r["ground_truth"] == "failed" and r["status"] in ("passed", "failed")]
    )],
    "disagreement_by_control": dict(disagreement_by_control),
    "fp_by_control": dict(fp_by_control),
    "fn_by_control": dict(fn_by_control),
    "rounds": round_rows,
    "paired": {
        "n": n_paired,
        "mean_diff": mean_diff,
        "sd_diff": sd_diff,
        "t": t_stat,
        "df": n_paired - 1,
        "ci95": diff_ci,
        "dz": dz,
    },
    "groups": groups,
    "findings": {
        "total": findings_total,
        "resolved": findings_resolved,
        "open": findings_open,
        "reopened": findings_reopened,
        "by_severity": findings_by_sev,
        "by_first_round": dict(Counter(int(f["first_detected_round"]) for f in findings)),
        "by_rounds_open": dict(Counter(int(f["rounds_open"]) for f in findings)),
        "resolved_by_round": dict(
            Counter(int(f["resolved_round"]) for f in findings if f["resolved_round"])
        ),
    },
    "duration": {
        "check_mean": st.mean(all_durations),
        "check_median": st.median(all_durations),
        "check_p95": float(np.percentile(all_durations, 95)),
        "check_min": min(all_durations),
        "check_max": max(all_durations),
        "run_mean": st.mean(run_durations),
        "run_median": st.median(run_durations),
        "run_min": min(run_durations),
        "run_max": max(run_durations),
        "by_control": {
            code: {
                "mean": st.mean(v),
                "median": st.median(v),
                "p95": float(np.percentile(v, 95)),
            }
            for code, v in dur_by_control.items()
        },
    },
    "archetypes": dict(Counter(s["archetype"] for s in servers)),
    "environments": dict(Counter(s["environment"] for s in servers)),
    "organizations": dict(Counter(s["organization"] for s in servers)),
    "openssh_absent": [s["host_id"] for s in servers if s["openssh_installed"] == "False"],
}

with open(TAB / "metricas.json", "w", encoding="utf-8") as fh:
    json.dump(metrics, fh, ensure_ascii=False, indent=2)

# --------------------------------------------------------------------------- tabla 1
rows = []
for c in controls:
    rows.append(
        [
            c["control_code"],
            c["cis_reference"] or "—",
            "Sí" if is_true(c["official_cis_mapping"]) else "No (interno)",
            c["title"],
            "Alta" if c["severity"] == "high" else "Media",
            c["category"],
        ]
    )
write_csv(
    "tabla1_catalogo.csv",
    ["Código", "Ref. CIS", "Mapeo oficial", "Control", "Severidad", "Categoría"],
    rows,
)

# --------------------------------------------------------------------------- tabla 2
envs = ["production", "staging", "development"]
archs = ["hardened", "partial", "default_install", "neglected"]
arch_label = {
    "hardened": "Endurecido",
    "partial": "Parcial",
    "default_install": "Instalación por defecto",
    "neglected": "Descuidado",
}
rows = []
for a in archs:
    counts = [sum(1 for s in servers if s["archetype"] == a and s["environment"] == e) for e in envs]
    rows.append([arch_label[a]] + counts + [sum(counts)])
rows.append(["Total"] + [sum(1 for s in servers if s["environment"] == e) for e in envs] + [len(servers)])
write_csv(
    "tabla2_flota.csv",
    ["Arquetipo", "Producción", "Staging", "Desarrollo", "Total"],
    rows,
)

# --------------------------------------------------------------------------- tabla 3
rows = []
for code in code_order:
    subset = [r for r in clean if r["control_code"] == code]
    passed = sum(1 for r in subset if r["status"] == "passed")
    failed = sum(1 for r in subset if r["status"] == "failed")
    na = sum(1 for r in subset if r["status"] == "not_applicable")
    matches = sum(1 for r in subset if is_true(r["match"]))
    rows.append(
        [
            code,
            len(subset),
            passed,
            failed,
            na,
            fmt(pct(matches, len(subset)), 1),
            fp_by_control.get(code, 0),
            fn_by_control.get(code, 0),
        ]
    )
write_csv(
    "tabla3_por_control.csv",
    ["Control", "Evaluadas", "Aprobadas", "Incumplidas", "N/A", "Concordancia (%)", "FP", "FN"],
    rows,
)

# --------------------------------------------------------------------------- tabla 4
rows = []
for r in round_rows:
    rows.append(
        [
            r["round"],
            r["n"],
            fmt(r["mean"], 2),
            fmt(r["sd"], 2),
            fmt(r["median"], 2),
            fmt(r["min"], 2),
            fmt(r["max"], 2),
            fmt(r["coverage"], 2),
            r["not_evaluated"],
            r["unreachable"],
            fmt(r["duration"], 0),
        ]
    )
write_csv(
    "tabla4_rondas.csv",
    ["Ronda", "Hosts", "Media (%)", "DE", "Mediana", "Mín.", "Máx.", "Cobertura (%)", "No evaluadas", "Auditorías inalcanzables", "Duración media (ms)"],
    rows,
)

# --------------------------------------------------------------------------- tabla 5
n_na = sum(1 for r in clean if r["status"] == "not_applicable")
rows = [
    ["Motor: aprobado", TN, FN, 0, TN + FN],
    ["Motor: incumplido", FP, TP, 0, FP + TP],
    ["Motor: N/A", 0, 0, n_na, n_na],
    ["Total", TN + FP, FN + TP, n_na, len(clean)],
    ["Panel B. Métricas", "Valor", "IC 95 %", "Base (n)", "Lectura"],
    ["Concordancia exacta (todas las filas)", f"{exact}/{len(clean)} ({fmt(exact_rate*100,2)} %)", "—", f"{len(clean)} filas", "Coincidencia global"],
    ["Exactitud binaria (aprobado/incumplido)", fmt(100 * accuracy, 2) + " %", f"{fmt(metrics['accuracy_wilson'][0],2)}–{fmt(metrics['accuracy_wilson'][1],2)} %", f"{N_BIN} binarias", "Wilson"],
    ["Precisión (incumplimiento)", fmt(100 * precision, 2) + " %", f"{fmt(metrics['precision_bootstrap'][0],2)}–{fmt(metrics['precision_bootstrap'][1],2)} %", f"{TP + FP} predichos", "Bootstrap"],
    ["Sensibilidad (recall)", fmt(100 * recall, 2) + " %", f"{fmt(metrics['recall_bootstrap'][0],2)}–{fmt(metrics['recall_bootstrap'][1],2)} %", f"{TP + FN} reales", "Bootstrap"],
    ["F1", fmt(100 * f1, 2) + " %", "—", f"{TP + FN}/{TP + FP}", "Media armónica"],
    ["Kappa de Cohen", fmt(kappa, 3), "—", f"{N_BIN} binarias", "Casi perfecta"],
]
write_csv(
    "tabla5_concordancia.csv",
    ["Panel A. Matriz de confusión", "Verdad: aprobado", "Verdad: incumplido", "Verdad: N/A", "Total"],
    rows,
)

# --------------------------------------------------------------------------- tabla 6
rows = []
for sev, label in (("high", "Alta"), ("medium", "Media")):
    d = findings_by_sev[sev]
    rows.append(
        [
            label,
            d["total"],
            d["resolved"],
            d["open"],
            d["reopened"],
            fmt(float(d["median_open_rounds"]), 1),
            d["max_open_rounds"],
        ]
    )
rows.append(
    [
        "Total",
        findings_total,
        findings_resolved,
        findings_open,
        findings_reopened,
        fmt(float(st.median(int(f["rounds_open"]) for f in findings)), 1),
        max(int(f["rounds_open"]) for f in findings),
    ]
)
write_csv(
    "tabla6_hallazgos.csv",
    ["Severidad", "Total", "Resueltos", "Abiertos", "Reabiertos", "Persistencia mediana (rondas)", "Persistencia máxima"],
    rows,
)

# --------------------------------------------------------------------------- figura 1
fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.1), sharey=True)
rounds = [r["round"] for r in round_rows]
means = [r["mean"] for r in round_rows]
lo, hi = zip(*[ci95(round_scores[r]) for r in rounds])
axes[0].fill_between(rounds, lo, hi, color=BLUE, alpha=0.18, linewidth=0)
axes[0].plot(rounds, means, color=BLUE, marker="o", linewidth=2)
axes[0].set_title("(a) Flota completa")
axes[0].set_xlabel("Ronda de auditoría")
axes[0].set_ylabel("Cumplimiento (%)")
axes[0].set_xticks(rounds)
axes[0].set_ylim(0, 100)

for key, color, label, style in (
    ("production", BLUE, "Producción", "-"),
    ("staging", ORANGE, "Staging", "--"),
    ("development", GREEN, "Desarrollo", "-."),
):
    axes[1].plot(rounds, groups[key], color=color, marker="o", markersize=4, linestyle=style, label=label)
axes[1].set_title("(b) Por entorno")
axes[1].set_xlabel("Ronda de auditoría")
axes[1].set_xticks(rounds)
axes[1].legend(frameon=False, loc="lower right")

for key, color, label in (
    ("hardened", BLUE, "Endurecido"),
    ("partial", GREEN, "Parcial"),
    ("default_install", ORANGE, "Por defecto"),
    ("neglected", VERMIL, "Descuidado"),
):
    axes[2].plot(rounds, groups[key], color=color, marker="o", markersize=4, label=label)
axes[2].set_title("(c) Por arquetipo")
axes[2].set_xlabel("Ronda de auditoría")
axes[2].set_xticks(rounds)
axes[2].legend(frameon=False, loc="lower right", ncol=2, fontsize=7)
fig.tight_layout()
fig.savefig(FIG / "figura1_cumplimiento_rondas.png")
plt.close(fig)

# --------------------------------------------------------------------------- figura 2
hosts_sorted = sorted(
    servers,
    key=lambda s: (
        archs.index(s["archetype"]),
        s["environment"],
        s["host_id"],
    ),
)
matrix = np.full((len(hosts_sorted), 6), np.nan)
for i, s in enumerate(hosts_sorted):
    for rnd in range(1, 7):
        if rnd in host_scores[s["host_id"]]:
            matrix[i, rnd - 1] = host_scores[s["host_id"]][rnd]
fig, ax = plt.subplots(figsize=(5.6, 8.4))
im = ax.imshow(matrix, aspect="auto", cmap=CMAP, vmin=0, vmax=100)
ax.set_xticks(range(6), [f"R{r}" for r in range(1, 7)])
ax.set_yticks(range(len(hosts_sorted)), [s["host_id"] for s in hosts_sorted], fontsize=6)
ax.set_xlabel("Ronda")
ax.grid(False)
arch_colors = {
    "hardened": BLUE,
    "partial": GREEN,
    "default_install": ORANGE,
    "neglected": VERMIL,
}
for label in ax.get_yticklabels():
    host = next(s for s in hosts_sorted if s["host_id"] == label.get_text())
    label.set_color(arch_colors[host["archetype"]])
ax.legend(
    handles=[Patch(facecolor=arch_colors[a], label=arch_label[a]) for a in archs],
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.055),
    ncol=2,
    fontsize=7,
)
for i in range(len(hosts_sorted)):
    for j in range(6):
        if np.isnan(matrix[i, j]):
            ax.text(j, i, "s/e", ha="center", va="center", fontsize=5, color=GREY)
# separadores por arquetipo
start = 0
for a in archs:
    n = sum(1 for s in hosts_sorted if s["archetype"] == a)
    if n and start:
        ax.axhline(start - 0.5, color="white", linewidth=1.6)
    start += n
cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
cb.set_label("Cumplimiento (%)")
fig.tight_layout()
fig.savefig(FIG / "figura2_mapa_calor.png")
plt.close(fig)

# --------------------------------------------------------------------------- figura 3
fig, ax = plt.subplots(figsize=(7.2, 4.6))
y = np.arange(len(code_order))
engine_pass = [
    100 * sum(1 for r in clean if r["control_code"] == c and r["status"] == "passed")
    / sum(1 for r in clean if r["control_code"] == c and r["status"] in ("passed", "failed"))
    for c in code_order
]
truth_pass = [
    100 * sum(1 for r in clean if r["control_code"] == c and r["ground_truth"] == "passed")
    / sum(1 for r in clean if r["control_code"] == c and r["status"] in ("passed", "failed"))
    for c in code_order
]
for i, c in enumerate(code_order):
    ax.plot([truth_pass[i], engine_pass[i]], [i, i], color="#CBD5E1", linewidth=3, zorder=1)
ax.scatter(truth_pass, y, color=GREY, s=38, label="Verdad esperada", zorder=2)
ax.scatter(engine_pass, y, color=BLUE, s=38, label="Motor", zorder=3)
for i, c in enumerate(code_order):
    if fp_by_control.get(c) or fn_by_control.get(c):
        ax.annotate(
            f"+{fp_by_control.get(c, 0)} FP / +{fn_by_control.get(c, 0)} FN",
            (min(engine_pass[i], truth_pass[i]) - 2, i),
            ha="right",
            va="center",
            fontsize=7,
            color=VERMIL,
        )
ax.set_yticks(y, code_order)
ax.invert_yaxis()
ax.set_xlabel("Tasa de aprobación sobre controles evaluados (%)")
ax.set_xlim(0, 105)
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig(FIG / "figura3_control_verdad.png")
plt.close(fig)

# --------------------------------------------------------------------------- figura 4
labels = ["Aprobado", "Incumplido", "N/A", "No evaluado"]
cm = np.zeros((4, 4), dtype=int)
idx = {"passed": 0, "failed": 1, "not_applicable": 2, "not_evaluated": 3}
for r in checks:
    cm[idx[r["status"]], idx[r["ground_truth"]]] += 1
fig, ax = plt.subplots(figsize=(4.8, 4.2))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(4), labels, rotation=20, ha="right")
ax.set_yticks(range(4), labels)
ax.set_xlabel("Verdad esperada")
ax.set_ylabel("Resultado del motor")
for i in range(4):
    for j in range(4):
        if cm[i, j]:
            color = "white" if cm[i, j] > cm.max() * 0.55 else "#0B1220"
            ax.text(j, i, f"{cm[i, j]}", ha="center", va="center", fontsize=10, color=color, fontweight="bold")
ax.grid(False)
fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
fig.tight_layout()
fig.savefig(FIG / "figura4_matriz_confusion.png")
plt.close(fig)

# --------------------------------------------------------------------------- figura 5
fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.3))
new_by_round = [metrics["findings"]["by_first_round"].get(r, 0) for r in range(1, 7)]
res_by_round = [metrics["findings"]["resolved_by_round"].get(r, 0) for r in range(1, 7)]
cum_open = []
open_now = 0
for r in range(1, 7):
    open_now += new_by_round[r - 1] - res_by_round[r - 1]
    cum_open.append(open_now)
x = np.arange(1, 7)
axes[0].bar(x - 0.18, new_by_round, width=0.34, color=VERMIL, label="Nuevos")
axes[0].bar(x + 0.18, res_by_round, width=0.34, color=GREEN, label="Resueltos")
axes[0].plot(x, cum_open, color=BLUE, marker="o", linewidth=1.8, label="Abiertos acumulados")
axes[0].set_xticks(x, [f"R{r}" for r in range(1, 7)])
axes[0].set_xlabel("Ronda")
axes[0].set_ylabel("Hallazgos")
axes[0].set_title("(a) Flujo de hallazgos")
axes[0].legend(frameon=False, fontsize=7)

persist = [int(f["rounds_open"]) for f in findings if f["status"] == "resolved"]
persist_open = [int(f["rounds_open"]) for f in findings if f["status"] == "open"]
bins = np.arange(0.5, 7.5, 1)
axes[1].hist([persist, persist_open], bins=bins, color=[GREEN, ORANGE], label=["Resueltos", "Abiertos"], stacked=True)
axes[1].set_xticks(range(1, 7))
axes[1].set_xlabel("Rondas consecutivas abierto")
axes[1].set_ylabel("Hallazgos")
axes[1].set_title("(b) Persistencia")
axes[1].legend(frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(FIG / "figura5_hallazgos.png")
plt.close(fig)

# --------------------------------------------------------------------------- figura 6
order = sorted(code_order, key=lambda c: st.median(dur_by_control[c]))
fig, ax = plt.subplots(figsize=(7.0, 4.6))
bp = ax.boxplot(
    [dur_by_control[c] for c in order],
    orientation="horizontal",
    patch_artist=True,
    widths=0.62,
    showfliers=False,
    medianprops={"color": "#0B1220", "linewidth": 1.4},
)
for patch in bp["boxes"]:
    patch.set_facecolor("#BFDBFE")
    patch.set_edgecolor(BLUE)
for i, c in enumerate(order, start=1):
    mean = st.mean(dur_by_control[c])
    ax.plot(mean, i, marker="D", color=VERMIL, markersize=4, zorder=3)
ax.set_yticks(range(1, len(order) + 1), order)
ax.set_xlabel("Duración por control (ms)")
ax.set_xlim(0, max(all_durations) * 1.05)
ax.legend(
    handles=[Patch(facecolor="#BFDBFE", edgecolor=BLUE, label="Rango intercuartílico"), plt.Line2D([], [], marker="D", color=VERMIL, linestyle="", label="Media")],
    frameon=False,
    loc="lower right",
)
fig.tight_layout()
fig.savefig(FIG / "figura6_latencia.png")
plt.close(fig)

print("Tablas y figuras generadas en docs/tablas y docs/figuras")
print(json.dumps({k: metrics[k] for k in ("exact_rate_pct", "precision_pct", "recall_pct", "kappa")}, ensure_ascii=False))
