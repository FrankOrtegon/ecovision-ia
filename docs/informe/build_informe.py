"""Construye el informe final (HTML y PDF) leyendo SOLO resultados guardados de ejecuciones reales.

Cada cifra del texto sale de un archivo en ml/results; nada se transcribe a mano.
Uso (desde la raíz del repositorio):  .venv/bin/python docs/informe/build_informe.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "ml" / "results"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
ES = {"cardboard": "Cartón", "glass": "Vidrio", "metal": "Metal", "paper": "Papel", "plastic": "Plástico", "trash": "Otros residuos"}


def jl(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def fc(x: float | None, d: int = 3) -> str:
    return "n/d" if x is None else f"{x:.{d}f}".replace(".", ",")


def pc(x: float, d: int = 2) -> str:
    return f"{x * 100:.{d}f} %".replace(".", ",")


def sh(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or ROOT).stdout


def count_passed(cmd: list[str], cwd: Path, pattern: str) -> int | None:
    out = sh(cmd, cwd)
    m = re.search(pattern, out)
    return int(m.group(1)) if m else None


def month_es(date_iso: str) -> str:
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    y, m, d = (int(v) for v in date_iso[:10].split("-"))
    return f"{d} de {meses[m - 1]} de {y}"


def table(head: list[str], rows: list[list[str]], left_cols: int = 1, bold_last: int = 0) -> str:
    th = "".join(f'<th class="izq">{h}</th>' if i < left_cols else f"<th>{h}</th>" for i, h in enumerate(head))
    body = []
    for ri, r in enumerate(rows):
        bold = ri >= len(rows) - bold_last
        cells = "".join((f"<td>{'<b>' + c + '</b>' if bold else c}</td>") for c in r)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def build_tokens() -> dict[str, str]:
    ds = jl(RES / "dataset_summary.json")
    src = jl(RES / "dataset_source.json")
    sp = jl(RES / "split_summary.json")
    tl = jl(RES / "training_log.json")["selection"]
    v1 = jl(RES / "eval_val_v1" / "metrics.json")
    v2 = jl(RES / "eval_val_v2" / "metrics.json")
    te = jl(RES / "eval_test_v1" / "metrics.json")
    ex = jl(RES / "eval_test_v1" / "extra_analysis.json")
    se = jl(RES / "eval_test_v1" / "sensitivity_fill.json")
    cfg = jl(RES / "eval_test_v1" / "model_config.json")
    assert cfg["final_evaluation"] and cfg["split"] == "test", "La evaluación de prueba debe ser la final"

    per = {p["label"]: p for p in te["per_class"]}
    auc = {c["label"]: c["score"] for c in te["roc"]}
    ap = {c["label"]: c["score"] for c in te["pr"]}
    ci = ex["bootstrap_ci95"]
    lc = ex["low_confidence_test"]
    cal = ex["calibration_test"]
    top = te["top_confusions"]

    tt = {
        "backend": count_passed([str(ROOT / ".venv/bin/python"), "-m", "pytest", "-q"], ROOT / "backend", r"(\d+) passed"),
        "root": count_passed([str(ROOT / ".venv/bin/python"), "-m", "pytest", "tests", "-q"], ROOT, r"(\d+) passed"),
        "front": count_passed(["npx", "vitest", "run"], ROOT / "frontend", r"Tests\s+(\d+) passed"),
    }
    if None in tt.values():
        sys.exit(f"No se pudieron contar las pruebas automatizadas: {tt}")
    lock = jl(ROOT / "frontend" / "package-lock.json")["packages"]
    ver = lambda n: lock[f"node_modules/{n}"]["version"]  # noqa: E731
    dep = jl(HERE / "despliegue.json")
    commit = sh(["git", "rev-parse", "--short", "HEAD"]).strip()

    if dep.get("frontend_url") and dep.get("backend_url"):
        estado = (f"La aplicación está publicada: interfaz en {dep['frontend_url']} y API (con documentación en /docs) en {dep['backend_url']}. "
                  f"Se verificó el {month_es(dep['verified_on'])}.")
    else:
        estado = ("<b>Estado de la publicación.</b> El modelo está desplegado y es accesible por API en Roboflow. La aplicación web se verificó "
                  "en ejecución local y en contenedor, y su configuración de publicación en Render y Vercel está preparada, pero al emitir "
                  "este documento no se había publicado; las direcciones públicas se incorporan al completarla.")

    T: dict[str, str] = {
        "fecha_larga": month_es(dep["document_date"]),
        "repo_url": "https://github.com/FrankOrtegon/ecovision-ia",
        "commit": commit,
        "n_total": str(ds["total_files"]),
        "n_excl": str(sp["images_excluded"]),
        "n_used": str(sp["images_used"]),
        "n_test": str(te["n_samples"]),
        "n_val": str(v1["n_samples"]),
        "n_val_trash": str(next(p["support"] for p in v1["per_class"] if p["label"] == "trash")),
        "n_test_trash": str(per["trash"]["support"]),
        "zip_mb": fc(src["zip_size_bytes"] / 1e6, 1),
        "fecha_descarga": month_es(src["downloaded_utc"]) + " (UTC)",
        "kb_min": fc(ds["bytes"]["min"] / 1000, 1),
        "kb_max": fc(ds["bytes"]["max"] / 1000, 1),
        "ratio": fc(ds["imbalance_ratio_max_over_min"], 2),
        "trash_pct": pc(ds["proportion_per_class"]["trash"], 2),
        "dup_groups": str(ds["exact_duplicates"]["groups"]),
        "groups": str(sp["groups_with_more_than_one_image"]),
        "pct_train": pc(sp["split_fractions"]["train"]),
        "pct_val": pc(sp["split_fractions"]["val"]),
        "pct_test": pc(sp["split_fractions"]["test"]),
        "mcnemar_p": fc(tl["paired_comparison"]["mcnemar_exact_p"], 3),
        "only_v1": str(tl["paired_comparison"]["only_v1_correct"]),
        "only_v2": str(tl["paired_comparison"]["only_v2_correct"]),
        "acc_diff": fc(tl["paired_comparison"]["accuracy_diff_v1_minus_v2"] * 100, 2),
        "diff_ci": f"{fc(tl['paired_comparison']['bootstrap_ci95'][0] * 100, 2)} a +{fc(tl['paired_comparison']['bootstrap_ci95'][1] * 100, 2)} puntos porcentuales",
        "acc_test": pc(te["accuracy"]),
        "acc_val": pc(v1["accuracy"]),
        "acc_ci": f"{pc(ci['test']['accuracy'][0])} a {pc(ci['test']['accuracy'][1])}",
        "f1_macro": fc(te["macro"]["f1"]),
        "f1_weighted": fc(te["weighted"]["f1"]),
        "auc_macro": fc(te["auc_macro"]),
        "auc_ci": f"{fc(ci['test']['auc_macro_approx'][0])} a {fc(ci['test']['auc_macro_approx'][1])}",
        "ap_macro": fc(te["ap_macro"]),
        "f1_trash": fc(per["trash"]["f1"]),
        "ap_trash": fc(ap["trash"]),
        "auc_trash": fc(auc["trash"]),
        "auc_min": fc(min(auc.values())),
        "auc_max": fc(max(auc.values())),
        "conf1_n": str(top[0]["count"]),
        "conf1_pct": pc(top[0]["share_of_true_class"], 1),
        "ece": fc(cal["ece"]),
        "conf_media": pc(cal["mean_confidence"], 1),
        "low_n": str(lc["n_flagged"]),
        "low_acc_flag": pc(lc["accuracy_flagged"], 1),
        "low_acc_ok": pc(lc["accuracy_not_flagged"], 1),
        "low_caught": str(lc["errors_caught_by_flag"]),
        "low_errors": str(lc["errors_total"]),
        "auc_sens": fc(abs(se["auc_macro"]["residual"] - se["auc_macro"]["zero_fill"]), 3),
        "ap_sens": fc(abs(se["ap_macro"]["residual"] - se["ap_macro"]["zero_fill"]), 3),
        "n_test_est": str(se["images_with_estimated_probabilities"]),
        "n_tests_backend": str(tt["backend"]),
        "n_tests_root": str(tt["root"]),
        "n_tests_front": str(tt["front"]),
        "n_tests_total": str(tt["backend"] + tt["root"] + tt["front"]),
        "py_ver": f"{sys.version_info.major}.{sys.version_info.minor}",
        "v_fastapi": metadata.version("fastapi"),
        "v_pydantic": metadata.version("pydantic"),
        "v_react": ver("react"),
        "v_ts": ver("typescript"),
        "v_vite": ver("vite"),
        "v_tw": ver("tailwindcss"),
        "v_recharts": ver("recharts"),
        "max_mb": "5",
        "max_batch": "20",
        "max_eval": "500",
        "lat_min": str(dep["latency_ms_min"]),
        "lat_max": str(dep["latency_ms_max"]),
        "seg_eval": str(dep["eval_seconds_test_via_app"]),
        "estado_despliegue": estado,
    }

    # Tabla 1: conjunto de datos y particiones
    rows = []
    for c in CLASSES:
        s = sp["per_class"][c]
        orig = ds["counts_per_class"][c]
        used = s["train"] + s["val"] + s["test"]
        rows.append([ES[c], str(orig), str(orig - used), str(s["train"]), str(s["val"]), str(s["test"])])
    tot = lambda i: str(sum(int(r[i]) for r in rows))  # noqa: E731
    rows.append(["Total", tot(1), tot(2), tot(3), tot(4), tot(5)])
    T["tbl_dataset"] = table(["Categoría", "Original", "Excluidas", "Entrenamiento", "Validación", "Prueba"], rows, bold_last=1)

    # Tabla 3: validación v1 frente a v2
    def vrow(name: str, f) -> list[str]:  # noqa: ANN001
        return [name, f(v1), f(v2)]
    f1t = lambda m: fc(next(p["f1"] for p in m["per_class"] if p["label"] == "trash"))  # noqa: E731
    T["tbl_validation"] = table(
        ["Métrica", "Modelo 1 (sin aumento)", "Modelo 2 (con aumento)"],
        [
            vrow("Exactitud", lambda m: fc(m["accuracy"], 4)),
            vrow("Precisión macro", lambda m: fc(m["macro"]["precision"], 4)),
            vrow("Recall macro", lambda m: fc(m["macro"]["recall"], 4)),
            vrow("F1 macro", lambda m: fc(m["macro"]["f1"], 4)),
            vrow("F1 de otros residuos", lambda m: f1t(m)),
            vrow("AUC macro (aprox.)", lambda m: fc(m["auc_macro"], 4)),
            vrow("AP macro (aprox.)", lambda m: fc(m["ap_macro"], 4)),
        ],
    )

    # Tabla 6: métricas por clase en prueba
    f1ci = ci["per_class_f1_test"]
    rows = []
    for c in CLASSES:
        p = per[c]
        rows.append([ES[c], fc(p["precision"]), fc(p["recall"]), f"{fc(p['f1'])} [{fc(f1ci[c][0], 2)}; {fc(f1ci[c][1], 2)}]", fc(auc[c]), fc(ap[c]), str(p["support"])])
    rows.append(["Macro", fc(te["macro"]["precision"]), fc(te["macro"]["recall"]), f"{fc(te['macro']['f1'])} [{fc(ci['test']['f1_macro'][0], 2)}; {fc(ci['test']['f1_macro'][1], 2)}]", fc(te["auc_macro"]), fc(te["ap_macro"]), str(te["n_samples"])])
    rows.append(["Ponderado", fc(te["weighted"]["precision"]), fc(te["weighted"]["recall"]), fc(te["weighted"]["f1"]), "—", "—", str(te["n_samples"])])
    T["tbl_percls"] = table(["Categoría", "Precisión", "Recall", "F1 [IC 95 %]", "AUC", "AP", "<i>n</i>"], rows, bold_last=2)

    # Tabla 7: confusiones frecuentes
    T["tbl_conf"] = table(
        ["Clase real", "Clase predicha", "Imágenes", "% de la clase real"],
        [[ES[c["true"]], ES[c["predicted"]], str(c["count"]), pc(c["share_of_true_class"], 1)] for c in top[:6]],
    )

    # Tabla 8: sensibilidad
    srow = [["AUC macro", fc(se["auc_macro"]["residual"], 4), fc(se["auc_macro"]["zero_fill"], 4), fc(abs(se["auc_macro"]["residual"] - se["auc_macro"]["zero_fill"]), 4)],
            ["AP macro", fc(se["ap_macro"]["residual"], 4), fc(se["ap_macro"]["zero_fill"], 4), fc(abs(se["ap_macro"]["residual"] - se["ap_macro"]["zero_fill"]), 4)]]
    for c in CLASSES:
        a = se["auc_per_class"][c]
        srow.append([f"AUC {ES[c].lower()}", fc(a["residual"], 4), fc(a["zero_fill"], 4), fc(abs(a["residual"] - a["zero_fill"]), 4)])
    T["tbl_sens"] = table(["Métrica", "Residuo repartido", "Relleno con ceros", "Diferencia"], srow)

    T["svg_arquitectura"] = (HERE / "arquitectura.svg").read_text(encoding="utf-8")
    return T


def main() -> None:
    T = build_tokens()
    parts = "\n".join(p.read_text(encoding="utf-8") for p in sorted((HERE / "parts").glob("p*.html")))

    def sub(m: re.Match[str]) -> str:
        if m.group(1) not in T:
            raise KeyError(f"Falta el valor para [[{m.group(1)}]]")
        return T[m.group(1)]

    body = re.sub(r"\[\[(\w+)\]\]", sub, parts)
    html = f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>EcoVision IA</title><link rel="stylesheet" href="informe.css"></head><body>{body}</body></html>'
    out_html = HERE / "informe.html"
    out_html.write_text(html, encoding="utf-8")
    pdf = ROOT / "docs" / "Informe_EcoVision_IA.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", out_html.as_uri()],
                   capture_output=True, timeout=180, check=False)
    print("HTML:", out_html, "| PDF:", pdf, "| existe:", pdf.exists(), "| tamaño KB:", round(pdf.stat().st_size / 1024) if pdf.exists() else 0)


if __name__ == "__main__":
    main()
