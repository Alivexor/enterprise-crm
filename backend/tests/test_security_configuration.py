import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.core.config import Settings


class SecurityConfigurationTestCase(unittest.TestCase):
    def _settings(self, **overrides) -> Settings:
        values = {
            "environment": "development",
            "database_url": "sqlite:///./test.db",
            "default_organization_id": uuid4(),
            "jwt_secret": "s" * 64,
        }
        values.update(overrides)
        return Settings(**values)

    def test_development_sqlite_is_supported(self) -> None:
        settings = self._settings()
        self.assertEqual(settings.environment, "development")
        self.assertTrue(settings.database_url.startswith("sqlite"))

    def test_production_rejects_sqlite(self) -> None:
        with self.assertRaisesRegex(ValidationError, "SQLite is not supported"):
            self._settings(environment="production")

    def test_production_rejects_local_attachment_storage(self) -> None:
        with self.assertRaisesRegex(ValidationError, "ATTACHMENT_STORAGE_BACKEND must be disabled"):
            self._settings(
                environment="production",
                database_url="postgresql+psycopg://crm:crm@db:5432/crm",
                attachment_storage_backend="local",
                attachment_local_storage_path=".attachments",
            )


if __name__ == "__main__":
    unittest.main()
