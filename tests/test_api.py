import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.api.schemas import TextAnalysisRequest


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "bert_ged" in data["models_loaded"]
    assert "t5_gec" in data["models_loaded"]


def test_taxonomy_endpoint(client):
    response = client.get("/api/v1/taxonomy")
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) >= 10
    cat_ids = [c["id"] for c in categories]
    assert "VERB_AGREEMENT" in cat_ids
    assert "VERB_TENSE" in cat_ids
    assert "ARTICLES_DETERMINERS" in cat_ids


def test_analyze_endpoint_valid_sentence(client):
    payload = {"text": "She go to school yesterday and saw two apple ."}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["is_changed"] is True
    assert len(data["explanations"]) >= 1
    assert "reconciliation" in data
    assert data["reconciliation"]["total_gec_edits"] >= 1
    assert data["reconciliation"]["concordance_rate"] >= 0.0


def test_analyze_clean_sentence(client):
    payload = {"text": "The students are reading their books in the library ."}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_detect_endpoint(client):
    payload = {"text": "She go to school ."}
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sentences" in data
    assert len(data["sentences"]) > 0


def test_correct_endpoint(client):
    payload = {"text": "She go to school ."}
    response = client.post("/api/v1/correct", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "corrected" in data


def test_explain_endpoint(client):
    payload = {"text": "She go to school yesterday ."}
    response = client.post("/api/v1/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "explanations" in data


def test_error_empty_input(client):
    response = client.post("/api/v1/analyze", json={"text": "   "})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error_type"] == "EMPTY_INPUT"


def test_error_invalid_language(client):
    response = client.post("/api/v1/analyze", json={"text": "Это текст на русском языке"})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error_type"] == "INVALID_LANGUAGE_INPUT"


def test_error_validation_schema(client):
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_type"] == "VALIDATION_ERROR"


def test_web_app_endpoint(client):
    response = client.get("/app")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
