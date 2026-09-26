from pathlib import Path

from fastapi.testclient import TestClient


def upload_pdf(
    client: TestClient,
    path: Path,
    *,
    organization_id: str | None = None,
    property_id: str | None = None,
    document_type: str = "lease",
    document_version: int = 1,
) -> dict:
    data = {"document_type": document_type, "document_version": str(document_version)}
    if organization_id:
        data["organization_id"] = organization_id
    if property_id:
        data["property_id"] = property_id
    response = client.post(
        "/api/v1/documents",
        files={"file": (path.name, path.read_bytes(), "application/pdf")},
        data=data,
    )
    assert response.status_code == 201, response.text
    return response.json()


def process_pdf(
    client: TestClient,
    path: Path,
    *,
    organization_id: str | None = None,
    property_id: str | None = None,
    document_type: str = "lease",
    document_version: int = 1,
) -> dict:
    document = upload_pdf(
        client,
        path,
        organization_id=organization_id,
        property_id=property_id,
        document_type=document_type,
        document_version=document_version,
    )
    response = client.post(f"/api/v1/documents/{document['id']}/process")
    assert response.status_code == 200, response.text
    return response.json()
