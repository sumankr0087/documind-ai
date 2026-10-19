"""Verification script for testing live deployed DocuMind AI endpoints."""
import sys
import time
import httpx

SAMPLE_DOC = """# Production Deployment Verification

DocuMind AI is successfully operating in the live public cloud environment.
It provides high-precision document extraction, semantic vector search, and grounded question answering with citations.
The health check endpoint at /health confirms that ChromaDB and Sentence Transformers are initialized.
"""


def verify_deployment(base_url: str):
    """Run end-to-end verification tests against a public DocuMind AI URL."""
    base_url = base_url.rstrip("/")
    print("=" * 80)
    print(f"VERIFYING DEPLOYED DOCUMIND AI INSTANCE: {base_url}")
    print("=" * 80)

    client = httpx.Client(timeout=30.0)

    # 1. Verify GET /health
    print("\n[Step 1/5] Testing GET /health...")
    try:
        health_res = client.get(f"{base_url}/health")
        print(f"  Status Code: {health_res.status_code}")
        health_data = health_res.json()
        print(f"  Response: {health_data}")
        assert health_res.status_code == 200, f"Expected 200, got {health_res.status_code}"
        assert health_data.get("status") == "healthy", "Expected status 'healthy'"
        print("  ✓ Health check passed!")
    except Exception as e:
        print(f"  ✗ Health check failed: {e}")
        sys.exit(1)

    # 2. Verify GET /docs
    print("\n[Step 2/5] Testing OpenAPI documentation at GET /docs...")
    try:
        docs_res = client.get(f"{base_url}/docs")
        print(f"  Status Code: {docs_res.status_code}")
        assert docs_res.status_code == 200, f"Expected 200, got {docs_res.status_code}"
        assert "swagger" in docs_res.text.lower() or "openapi" in docs_res.text.lower(), "Expected Swagger UI HTML"
        print("  ✓ Interactive documentation page is accessible!")
    except Exception as e:
        print(f"  ✗ Docs page check failed: {e}")
        sys.exit(1)

    # 3. Test POST /documents/upload
    print("\n[Step 3/5] Testing document ingestion via POST /documents/upload...")
    doc_id = None
    try:
        files = {"file": ("cloud_verification.md", SAMPLE_DOC.encode("utf-8"), "text/markdown")}
        upload_res = client.post(f"{base_url}/documents/upload", files=files)
        print(f"  Status Code: {upload_res.status_code}")
        upload_data = upload_res.json()
        print(f"  Upload response: {upload_data.get('message')}")
        assert upload_res.status_code == 201, f"Expected 201, got {upload_res.status_code}"
        doc_id = upload_data["document"]["document_id"]
        print(f"  ✓ Document ingested successfully (ID: {doc_id})!")
    except Exception as e:
        print(f"  ✗ Document upload failed: {e}")
        sys.exit(1)

    # 4. Test POST /questions/ask
    print("\n[Step 4/5] Testing grounded Q&A via POST /questions/ask...")
    try:
        qa_res = client.post(
            f"{base_url}/questions/ask",
            json={
                "question": "What does the /health endpoint confirm?",
                "document_id": doc_id,
                "top_k": 3,
            },
        )
        print(f"  Status Code: {qa_res.status_code}")
        qa_data = qa_res.json()
        print(f"  Answer: {qa_data.get('answer')}")
        print(f"  Evidence Sufficient: {qa_data.get('evidence_sufficient')}")
        print(f"  Citations count: {len(qa_data.get('citations', []))}")
        assert qa_res.status_code == 200, f"Expected 200, got {qa_res.status_code}"
        assert qa_data.get("evidence_sufficient") is True, "Expected evidence to be sufficient"
        assert len(qa_data.get("citations", [])) > 0, "Expected at least 1 citation"
        print("  ✓ Question answering and citations verified!")
    except Exception as e:
        print(f"  ✗ Question answering failed: {e}")
        sys.exit(1)

    # 5. Test DELETE /documents/{document_id}
    print("\n[Step 5/5] Cleaning up test document via DELETE /documents/{document_id}...")
    try:
        del_res = client.delete(f"{base_url}/documents/{doc_id}")
        print(f"  Status Code: {del_res.status_code}")
        assert del_res.status_code == 200, f"Expected 200, got {del_res.status_code}"
        print(f"  ✓ Test document cleaned up successfully!")
    except Exception as e:
        print(f"  ✗ Cleanup failed: {e}")

    print("\n" + "=" * 80)
    print("ALL DEPLOYMENT VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_deployment.py <PUBLIC_URL>")
        print("Example: python scripts/verify_deployment.py https://documind-ai.onrender.com")
        sys.exit(1)

    verify_deployment(sys.argv[1])
