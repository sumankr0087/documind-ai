"""Automated tests for document upload, listing, retrieval, and deletion endpoints."""
import io


def test_upload_valid_pdf(test_client, sample_pdf_bytes):
    """Test uploading a valid PDF document."""
    files = {"file": ("manual.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    response = test_client.post("/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()

    assert "document" in data
    doc = data["document"]
    assert doc["filename"] == "manual.pdf"
    assert doc["content_type"] == "application/pdf"
    assert doc["chunk_count"] > 0
    assert doc["page_count"] == 2
    assert "document_id" in doc


def test_upload_valid_txt(test_client, sample_txt_bytes):
    """Test uploading a valid TXT document."""
    files = {"file": ("notes.txt", io.BytesIO(sample_txt_bytes), "text/plain")}
    response = test_client.post("/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["document"]["filename"] == "notes.txt"
    assert data["document"]["content_type"] == "text/plain"


def test_upload_valid_markdown(test_client, sample_md_bytes):
    """Test uploading a valid Markdown document."""
    files = {"file": ("spec.md", io.BytesIO(sample_md_bytes), "text/markdown")}
    response = test_client.post("/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["document"]["filename"] == "spec.md"


def test_upload_empty_file(test_client):
    """Test uploading an empty file returns 400."""
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    response = test_client.post("/documents/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_unsupported_type(test_client):
    """Test uploading an unsupported file format returns 415."""
    files = {"file": ("script.py", io.BytesIO(b"print('hello')"), "text/x-python")}
    response = test_client.post("/documents/upload", files=files)
    assert response.status_code == 415
    assert "unsupported" in response.json()["detail"].lower()


def test_list_and_get_documents(test_client, sample_txt_bytes):
    """Test listing documents and fetching a single document by ID."""
    # Upload one document
    files = {"file": ("lookup.txt", io.BytesIO(sample_txt_bytes), "text/plain")}
    upload_res = test_client.post("/documents/upload", files=files)
    doc_id = upload_res.json()["document"]["document_id"]

    # List documents
    list_res = test_client.get("/documents")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total_documents"] >= 1
    assert any(d["document_id"] == doc_id for d in list_data["documents"])

    # Get single document
    get_res = test_client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["document"]["document_id"] == doc_id
    assert len(get_data["chunks"]) > 0


def test_get_nonexistent_document(test_client):
    """Test getting nonexistent document returns 404."""
    response = test_client.get("/documents/nonexistent-uuid-1234")
    assert response.status_code == 404


def test_delete_document(test_client, sample_txt_bytes):
    """Test deleting an uploaded document and its vectors."""
    files = {"file": ("delete_me.txt", io.BytesIO(sample_txt_bytes), "text/plain")}
    upload_res = test_client.post("/documents/upload", files=files)
    doc_id = upload_res.json()["document"]["document_id"]

    # Delete
    del_res = test_client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["document_id"] == doc_id
    assert del_data["chunks_deleted"] > 0

    # Ensure it no longer exists
    get_res = test_client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 404


def test_delete_nonexistent_document(test_client):
    """Test deleting nonexistent document returns 404."""
    response = test_client.delete("/documents/nonexistent-uuid-1234")
    assert response.status_code == 404
