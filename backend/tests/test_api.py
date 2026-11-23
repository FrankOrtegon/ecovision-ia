import pytest
from conftest import CLASSES, FakeClassifier, make_image, make_settings, peaked
from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.main import create_app


def img(name: str = "a.jpg", fmt: str = "JPEG") -> tuple[str, tuple[str, bytes, str]]:
    return ("file", (name, make_image(fmt), f"image/{fmt.lower()}"))


# ---------- sistema ----------
def test_health_ok(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["model_configured"] is True


def test_health_degraded_without_model(unconfigured_client: TestClient) -> None:
    j = unconfigured_client.get("/api/health").json()
    assert j["status"] == "degraded" and j["model_configured"] is False


def test_health_publishes_limits_for_the_frontend(client: TestClient) -> None:
    lim = client.get("/api/health").json()["limits"]
    assert lim == {
        "max_image_mb": 1.0,
        "max_batch_files": 3,
        "max_eval_files": 10,
        "low_confidence_threshold": 0.6,
        "allowed_extensions": [".jpeg", ".jpg", ".png", ".webp"],
    }


def test_model_info_reports_selected_model_without_claiming_test_metrics(client: TestClient) -> None:
    j = client.get("/api/model/info").json()
    assert j["status"] == "ready" and j["model_id"] == "ecovision-trashnet/1"
    assert j["classes"] == CLASSES
    assert "Validación" in j["metrics"]["Conjunto evaluado"]
    # Las métricas sobre test no se publican hasta ejecutar la evaluación final.
    assert "Pendientes" in j["metrics"]["Métricas sobre el conjunto de prueba"]
    assert j["trained_at"] == "2026-11-22"


def test_docs_and_openapi_available(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    for p in ("/api/health", "/api/model/info", "/api/predict", "/api/predict/batch", "/api/evaluate"):
        assert p in paths


# ---------- predicción individual ----------
def test_predict_success(client: TestClient, fake: FakeClassifier) -> None:
    fake.queue.append(peaked("glass", 0.82))
    r = client.post("/api/predict", files=[img("botella.jpg")])
    assert r.status_code == 200
    j = r.json()
    assert j["result"]["predicted_label"] == "glass"
    assert j["result"]["confidence"] == pytest.approx(0.82)
    assert j["result"]["low_confidence"] is False
    probs = j["result"]["probabilities"]
    assert [p["label"] for p in probs] == CLASSES
    assert sum(p["probability"] for p in probs) == pytest.approx(1.0)
    assert j["model_id"] == "proyecto-prueba/1"


def test_predict_low_confidence_flag(client: TestClient, fake: FakeClassifier) -> None:
    fake.queue.append(peaked("metal", 0.4))
    assert client.post("/api/predict", files=[img()]).json()["result"]["low_confidence"] is True


@pytest.mark.parametrize("fmt,name", [("PNG", "a.png"), ("WEBP", "a.webp"), ("JPEG", "a.JPEG")])
def test_predict_accepts_supported_formats(client: TestClient, fmt: str, name: str) -> None:
    assert client.post("/api/predict", files=[img(name, fmt)]).status_code == 200


def test_predict_estimates_omitted_classes_with_the_residual(
    client: TestClient, fake: FakeClassifier
) -> None:
    # El proveedor devuelve glass 0.97 y metal 0.02. Residuo = 0.01 repartido entre 4 clases omitidas = 0.0025.
    fake.queue.append({"glass": 0.97, "metal": 0.02})
    j = client.post("/api/predict", files=[img()]).json()["result"]
    assert j["estimated_probabilities"] is True
    probs = {p["label"]: p["probability"] for p in j["probabilities"]}
    assert probs["glass"] == 0.97 and probs["metal"] == 0.02
    for c in ("cardboard", "paper", "plastic", "trash"):
        assert probs[c] == pytest.approx(0.0025)
    assert sum(probs.values()) == pytest.approx(1.0)
    assert j["resolved_model"] == "workspace-prueba/modelo-falso"


def test_predict_complete_probabilities_are_not_flagged(client: TestClient, fake: FakeClassifier) -> None:
    fake.queue.append(peaked("glass", 0.9))
    assert client.post("/api/predict", files=[img()]).json()["result"]["estimated_probabilities"] is False


def test_predict_rejects_bad_extension(client: TestClient, fake: FakeClassifier) -> None:
    r = client.post("/api/predict", files=[("file", ("a.gif", make_image("GIF"), "image/gif"))])
    assert r.status_code == 415 and r.json()["detail"]["code"] == "invalid_file"
    assert fake.calls == 0


def test_predict_rejects_non_image_content_with_image_extension(
    client: TestClient, fake: FakeClassifier
) -> None:
    r = client.post("/api/predict", files=[("file", ("a.jpg", b"esto no es una imagen", "image/jpeg"))])
    assert r.status_code == 422 and r.json()["detail"]["code"] == "invalid_file"
    assert fake.calls == 0


def test_predict_rejects_empty_file(client: TestClient) -> None:
    r = client.post("/api/predict", files=[("file", ("a.jpg", b"", "image/jpeg"))])
    assert r.status_code == 422


def test_predict_rejects_oversize(client: TestClient, fake: FakeClassifier) -> None:
    big = make_image() + b"\0" * (1024 * 1024 + 10)
    r = client.post("/api/predict", files=[("file", ("a.jpg", big, "image/jpeg"))])
    assert r.status_code == 413 and r.json()["detail"]["code"] == "file_too_large"
    assert fake.calls == 0


def test_predict_rejects_too_many_pixels(fake: FakeClassifier) -> None:
    from app.api.deps import get_classifier

    app = create_app(make_settings(max_image_pixels=100))
    app.dependency_overrides[get_classifier] = lambda: fake
    with TestClient(app) as c:
        r = c.post("/api/predict", files=[img()])
    assert r.status_code == 413


def test_predict_missing_file_gives_uniform_validation_error(client: TestClient) -> None:
    r = client.post("/api/predict")
    assert r.status_code == 422 and r.json()["detail"]["code"] == "validation_error"


def test_predict_without_configured_model_returns_503_not_fake_prediction(
    unconfigured_client: TestClient,
) -> None:
    r = unconfigured_client.post("/api/predict", files=[img()])
    assert r.status_code == 503 and r.json()["detail"]["code"] == "model_not_configured"


@pytest.mark.parametrize(
    "err,status,code",
    [
        (AppError("upstream_error", "x", 502), 502, "upstream_error"),
        (AppError("upstream_timeout", "x", 504), 504, "upstream_timeout"),
    ],
)
def test_predict_propagates_upstream_errors(
    client: TestClient, fake: FakeClassifier, err, status, code
) -> None:
    fake.queue.append(err)
    r = client.post("/api/predict", files=[img()])
    assert r.status_code == status and r.json()["detail"]["code"] == code


# ---------- lote ----------
def test_batch_mixed_results(client: TestClient, fake: FakeClassifier) -> None:
    fake.queue += [peaked("paper", 0.9), peaked("trash", 0.7)]
    files = [
        ("files", ("ok1.jpg", make_image(), "image/jpeg")),
        ("files", ("mal.jpg", b"basura", "image/jpeg")),
        ("files", ("ok2.png", make_image("PNG"), "image/png")),
    ]
    j = client.post("/api/predict/batch", files=files).json()
    assert (j["total"], j["succeeded"], j["failed"]) == (3, 2, 1)
    by = {i["filename"]: i for i in j["items"]}
    assert by["mal.jpg"]["status"] == "error" and by["mal.jpg"]["error_code"] == "invalid_file"
    assert by["ok1.jpg"]["result"]["predicted_label"] == "paper"
    assert by["ok2.png"]["result"]["predicted_label"] == "trash"


def test_batch_upstream_failure_is_per_file(client: TestClient, fake: FakeClassifier) -> None:
    fake.queue += [AppError("upstream_timeout", "lento", 504), peaked("glass", 0.8)]
    files = [("files", (f"{n}.jpg", make_image(), "image/jpeg")) for n in ("a", "b")]
    j = client.post("/api/predict/batch", files=files).json()
    assert j["failed"] == 1 and j["succeeded"] == 1
    assert j["items"][0]["error_code"] == "upstream_timeout"


def test_batch_too_many_files(client: TestClient) -> None:
    files = [("files", (f"{n}.jpg", make_image(), "image/jpeg")) for n in range(4)]
    r = client.post("/api/predict/batch", files=files)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "too_many_files"


def test_batch_oversize_file_reported_individually(client: TestClient) -> None:
    big = make_image() + b"\0" * (1024 * 1024 + 10)
    files = [("files", ("grande.jpg", big, "image/jpeg")), ("files", ("ok.jpg", make_image(), "image/jpeg"))]
    j = client.post("/api/predict/batch", files=files).json()
    assert j["items"][0]["error_code"] == "file_too_large" and j["items"][1]["status"] == "ok"


# ---------- evaluación ----------
def eval_files(names: list[str]) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("files", (n, make_image(), "image/jpeg")) for n in names]


def csv_file(text: str) -> tuple[str, tuple[str, bytes, str]]:
    return ("labels_csv", ("labels.csv", text.encode(), "text/csv"))


def test_evaluate_success_and_hand_checked_numbers(client: TestClient, fake: FakeClassifier) -> None:
    # 4 imágenes: 3 aciertos y 1 error (glass -> metal).
    fake.queue += [peaked("glass", 0.9), peaked("metal", 0.8), peaked("paper", 0.9), peaked("plastic", 0.7)]
    csv = "filename,true_label\ng1.jpg,glass\ng2.jpg,glass\np1.jpg,paper\npl1.jpg,plastic\n"
    r = client.post(
        "/api/evaluate", files=eval_files(["g1.jpg", "g2.jpg", "p1.jpg", "pl1.jpg"]) + [csv_file(csv)]
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["n_evaluated"] == 4 and j["accuracy"] == pytest.approx(0.75)
    pc = {p["label"]: p for p in j["per_class"]}
    assert pc["glass"]["recall"] == pytest.approx(0.5) and pc["glass"]["precision"] == pytest.approx(1.0)
    # metal no tiene ejemplos reales: sus métricas no se calculan (no se inventan ceros).
    assert pc["metal"]["support"] == 0 and pc["metal"]["precision"] is None and pc["metal"]["recall"] is None
    cm = j["confusion_matrix"]
    assert cm["labels"] == CLASSES and cm["matrix"][1][2] == 1  # glass real -> metal predicho
    assert j["top_confusions"][0] == {
        "true": "glass",
        "predicted": "metal",
        "count": 1,
        "share_of_true_class": 0.5,
    }
    # Clases sin ejemplos reales: AUC no calculable y AUC macro ausente, con motivo.
    assert j["auc_macro"] is None and "no calculable" in j["auc_macro_note"]
    assert any(c["label"] == "cardboard" and c["score"] is None for c in j["roc"])
    assert len(j["rows"]) == 4
    assert j["resolved_models"] == ["workspace-prueba/modelo-falso"]
    assert j["n_estimated_probabilities"] == 0


def test_evaluate_reports_unmatched_and_failed(client: TestClient, fake: FakeClassifier) -> None:
    fake.queue += [peaked("glass", 0.9), peaked("paper", 0.9)]
    csv = "filename,true_label\na.jpg,glass\nb.jpg,paper\nc.jpg,metal\nfalta.jpg,trash\n"
    files = eval_files(["a.jpg", "b.jpg", "c.jpg", "sin_etiqueta.jpg"])
    files[2] = ("files", ("c.jpg", b"danado", "image/jpeg"))
    j = client.post("/api/evaluate", files=files + [csv_file(csv)]).json()
    assert j["n_evaluated"] == 2
    assert j["unmatched_images"] == ["sin_etiqueta.jpg"]
    assert j["unmatched_labels"] == ["falta.jpg"]
    assert [f["filename"] for f in j["failed"]] == ["c.jpg"]
    assert len(j["warnings"]) >= 3


@pytest.mark.parametrize(
    "csv,fragment",
    [
        ("nombre,etiqueta\na.jpg,glass\n", "columnas"),
        ("filename,true_label\n", "no tiene filas"),
        ("filename,true_label\na.jpg,vidrio\n", "no válidas"),
        ("filename,true_label\na.jpg,glass\na.jpg,metal\n", "repetidos"),
    ],
)
def test_evaluate_bad_csv(client: TestClient, csv: str, fragment: str) -> None:
    r = client.post("/api/evaluate", files=eval_files(["a.jpg"]) + [csv_file(csv)])
    assert r.status_code == 422 and r.json()["detail"]["code"] == "bad_csv"
    assert fragment in r.json()["detail"]["message"]


def test_evaluate_no_matches(client: TestClient) -> None:
    r = client.post(
        "/api/evaluate", files=eval_files(["x.jpg"]) + [csv_file("filename,true_label\ny.jpg,glass\n")]
    )
    assert r.status_code == 422 and r.json()["detail"]["code"] == "no_matches"


def test_evaluate_requires_csv(client: TestClient) -> None:
    r = client.post("/api/evaluate", files=eval_files(["x.jpg"]))
    assert r.status_code == 422


# ---------- CORS y cabeceras ----------
def test_cors_allows_configured_origin_only(client: TestClient) -> None:
    ok = client.options(
        "/api/predict",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options(
        "/api/predict",
        headers={"Origin": "https://malicioso.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in bad.headers


def test_security_headers(client: TestClient) -> None:
    h = client.get("/api/health").headers
    assert h["x-content-type-options"] == "nosniff" and h["cache-control"] == "no-store"


def test_production_rejects_wildcard_origin() -> None:
    with pytest.raises(ValueError):
        make_settings(environment="production", allowed_origins="*")
