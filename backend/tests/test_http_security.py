import unittest
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.http import install_http_middleware


class HttpSecurityTestCase(unittest.TestCase):
    def setUp(self) -> None:
        settings = Settings(
            environment="development",
            database_url="sqlite://",
            default_organization_id=uuid4(),
            jwt_secret="h" * 64,
            http_max_request_bytes=64,
        )
        app = FastAPI()
        install_http_middleware(app, settings)

        @app.get("/ok")
        def ok() -> dict[str, bool]:
            return {"ok": True}

        @app.post("/echo")
        async def echo(request: Request) -> dict[str, int]:
            body = await request.body()
            return {"bytes": len(body)}

        self.client = TestClient(app)

    def test_security_and_request_id_headers_are_added(self) -> None:
        response = self.client.get("/ok", headers={"X-Request-ID": "portfolio-test-1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-request-id"], "portfolio-test-1")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["cross-origin-resource-policy"], "same-origin")

    def test_invalid_or_oversized_content_length_is_rejected(self) -> None:
        invalid = self.client.post("/echo", headers={"Content-Length": "invalid"})
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["detail"], "Invalid Content-Length header")

        oversized = self.client.post("/echo", headers={"Content-Length": "65"})
        self.assertEqual(oversized.status_code, 413)
        self.assertEqual(oversized.json()["detail"], "Request body is too large")

    def test_chunked_body_is_limited_without_content_length(self) -> None:
        def chunks():
            yield b"a" * 40
            yield b"b" * 40

        response = self.client.post("/echo", content=chunks())
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["detail"], "Request body is too large")


if __name__ == "__main__":
    unittest.main()
