import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Fixture que provee una instancia de la app con BD temporal aislada.

    Cada prueba recibe una base de datos SQLite independiente creada en un
    directorio temporal de Pytest, que se elimina automáticamente al finalizar.
    No se usa ':memory:' para garantizar compatibilidad con todas las pruebas.
    """
    test_database = tmp_path / "test_sigi_ai.db"
    application = create_app({
        "TESTING": True,
        "DATABASE_PATH": str(test_database),
        "SECRET_KEY": "test-secret",
    })
    yield application


@pytest.fixture
def client(app):
    """Fixture que provee el cliente HTTP de prueba de Flask."""
    return app.test_client()
