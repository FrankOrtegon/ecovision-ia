"""Pruebas de ecovision_eval con casos calculados a mano (datos sintéticos solo para pruebas)."""
import json

import numpy as np
import pytest

from ecovision_eval import CLASSES, compute_metrics, save_results

C3 = ["a", "b", "c"]

# Caso con un error en a->b y otro en c->a.
Y = ["a", "a", "b", "b", "c", "c"]
P = np.array(
    [
        [0.8, 0.1, 0.1],  # real a, pred a
        [0.3, 0.5, 0.2],  # real a, pred b
        [0.1, 0.8, 0.1],  # real b, pred b
        [0.2, 0.6, 0.2],  # real b, pred b
        [0.1, 0.1, 0.8],  # real c, pred c
        [0.5, 0.1, 0.4],  # real c, pred a
    ]
)


def test_hand_computed_classification_metrics() -> None:
    r = compute_metrics(Y, P, C3)
    assert r.confusion_matrix == [[1, 1, 0], [0, 2, 0], [1, 0, 1]]
    assert r.accuracy == pytest.approx(4 / 6)
    pc = {x.label: x for x in r.per_class}
    # precision: a=1/2, b=2/3, c=1; recall: a=1/2, b=1, c=1/2
    assert pc["a"].precision == pytest.approx(0.5)
    assert pc["b"].precision == pytest.approx(2 / 3)
    assert pc["c"].precision == pytest.approx(1.0)
    assert pc["a"].recall == pytest.approx(0.5)
    assert pc["b"].recall == pytest.approx(1.0)
    assert pc["c"].recall == pytest.approx(0.5)
    assert pc["b"].f1 == pytest.approx(0.8)
    assert pc["c"].f1 == pytest.approx(2 / 3)
    assert r.macro["precision"] == pytest.approx((0.5 + 2 / 3 + 1) / 3)
    assert r.macro["recall"] == pytest.approx(2 / 3)
    # soportes iguales: ponderado == macro
    assert r.weighted["f1"] == pytest.approx(r.macro["f1"])


def test_hand_computed_auc_and_ap() -> None:
    r = compute_metrics(Y, P, C3)
    auc = {c.label: c.score for c in r.roc}
    assert auc["a"] == pytest.approx(7 / 8)
    assert auc["b"] == pytest.approx(1.0)
    assert auc["c"] == pytest.approx(1.0)
    assert r.auc_macro == pytest.approx((7 / 8 + 1 + 1) / 3)
    ap = {c.label: c.score for c in r.pr}
    assert ap["a"] == pytest.approx((1 + 2 / 3) / 2)


def test_perfect_predictions() -> None:
    y = list(CLASSES) * 3
    p = np.eye(6)[[CLASSES.index(c) for c in y]]
    r = compute_metrics(y, p)
    assert r.accuracy == 1.0
    assert r.auc_macro == 1.0
    assert r.ap_macro == 1.0
    assert r.top_confusions == []


def test_roc_uses_probabilities_not_labels() -> None:
    """Mismas etiquetas predichas y mismo accuracy, pero ordenamiento de probabilidades distinto."""
    y = ["a", "a", "b", "b"]
    # Columna a de cada matriz; la columna b es 1 - a.
    col_a_1 = [0.9, 0.6, 0.7, 0.1]  # positivos {0.9, 0.6} vs negativos {0.7, 0.1} -> AUC 3/4
    col_a_2 = [0.6, 0.55, 0.9, 0.1]  # positivos {0.6, 0.55} vs negativos {0.9, 0.1} -> AUC 2/4
    p1 = np.column_stack([col_a_1, 1 - np.array(col_a_1)])
    p2 = np.column_stack([col_a_2, 1 - np.array(col_a_2)])
    r1 = compute_metrics(y, p1, ["a", "b"])
    r2 = compute_metrics(y, p2, ["a", "b"])
    assert r1.predicted_labels == r2.predicted_labels == ["a", "a", "a", "b"]
    assert r1.accuracy == r2.accuracy == 0.75
    assert r1.roc[0].score == pytest.approx(0.75)
    assert r2.roc[0].score == pytest.approx(0.5)
    assert r1.auc_macro == pytest.approx(0.75)
    assert r2.auc_macro == pytest.approx(0.5)


def test_class_without_positives_is_reported_not_invented() -> None:
    y = ["a", "a", "b", "b"]
    p = np.array([[0.7, 0.2, 0.1], [0.6, 0.3, 0.1], [0.2, 0.7, 0.1], [0.3, 0.6, 0.1]])
    r = compute_metrics(y, p, C3)
    c = next(x for x in r.roc if x.label == "c")
    assert c.score is None and "positivos" in c.note
    assert r.auc_macro is None and "c" in r.auc_macro_note
    pcc = next(x for x in r.per_class if x.label == "c")
    assert pcc.precision is None and pcc.recall is None and pcc.f1 is None
    assert any("'c'" in w for w in r.warnings)
    assert r.macro["f1"] == pytest.approx(1.0)  # solo a y b


def test_class_without_negatives() -> None:
    p = np.array([[0.9, 0.1], [0.8, 0.2]])
    r = compute_metrics(["a", "a"], p, ["a", "b"])
    assert r.roc[0].score is None and "negativos" in r.roc[0].note
    assert r.auc_macro is None


def test_top_confusions_sorted() -> None:
    y = ["a"] * 4 + ["b"] * 2
    pred = [1, 1, 1, 0, 0, 1]  # a->b x3, b->a x1
    p = np.eye(2)[pred]
    r = compute_metrics(y, p, ["a", "b"])
    assert r.top_confusions[0] == {"true": "a", "predicted": "b", "count": 3, "share_of_true_class": 0.75}
    assert r.top_confusions[1]["count"] == 1


@pytest.mark.parametrize(
    "y,p,msg",
    [
        ([], np.zeros((0, 3)), "muestras"),
        (["a", "x"], np.full((2, 3), 1 / 3), "desconocidas"),
        (["a", "b"], np.full((2, 2), 0.5), "forma"),
        (["a", "b"], np.array([[np.nan, 1, 0], [0, 1, 0]]), "NaN"),
        (["a", "b"], np.array([[-0.1, 1.1, 0], [0, 1, 0]]), "entre 0 y 1"),
    ],
)
def test_invalid_inputs(y, p, msg) -> None:
    with pytest.raises(ValueError, match=msg):
        compute_metrics(y, p, C3)


def test_warns_when_probabilities_do_not_sum_to_one() -> None:
    r = compute_metrics(["a", "b"], np.array([[0.5, 0.1, 0.1], [0.1, 0.5, 0.1]]), C3)
    assert any("no suman 1" in w for w in r.warnings)


def test_to_dict_is_json_serializable() -> None:
    json.dumps(compute_metrics(Y, P, C3).to_dict())


def test_save_results_creates_expected_files(tmp_path) -> None:
    r = compute_metrics(Y, P, C3)
    save_results(r, [f"img{i}.jpg" for i in range(6)], Y, P, tmp_path, {"model_id": "prueba"})
    names = {p.name for p in tmp_path.iterdir()}
    assert {
        "predictions.csv", "metrics.json", "classification_report.txt", "model_config.json",
        "confusion_matrix.png", "confusion_matrix_normalized.png", "roc_curves.png", "pr_curves.png",
    } <= names
    header = (tmp_path / "predictions.csv").read_text().splitlines()[0]
    assert header == "filename,true_label,predicted_label,prob_a,prob_b,prob_c"
