from pathlib import Path

from fastapi.testclient import TestClient


def upload_pdf(client: TestClient, path: Path) -> dict:
    response = client.post(
        "/api/v1/documents",
        files={"file": (path.name, path.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def process_pdf(client: TestClient, path: Path) -> dict:
    document = upload_pdf(client, path)
    response = client.post(f"/api/v1/documents/{document['id']}/process")
    assert response.status_code == 200, response.text
    return response.json()
