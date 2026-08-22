"""Pruebas unitarias para validate_incident_data.

Cubre los criterios de aceptación del Requisito 1 (1.4 – 1.8).
Patrón: AAA (Arrange, Act, Assert).
"""

import pytest

from app.validators.incident_validator import validate_incident_data


# ---------------------------------------------------------------------------
# Datos auxiliares
# ---------------------------------------------------------------------------

def _valid_data(**overrides) -> dict:
    """Retorna un diccionario con todos los campos obligatorios válidos."""
    base = {
        "title": "Correo de phishing detectado",
        "description": "Se recibió un correo sospechoso con enlace malicioso.",
        "location": "Oficina central",
        "incident_date": "2026-07-31",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# test_valid_data
# Req. 1.1 — datos completos y válidos → (True, [])
# ---------------------------------------------------------------------------

class TestValidData:
    def test_valid_data_returns_true_and_empty_errors(self):
        # Arrange
        data = _valid_data()

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is True
        assert errors == []

    def test_valid_data_with_minimum_content(self):
        # Arrange — un solo carácter es suficiente para los campos de texto
        data = _valid_data(title="X", description="Y", location="Z")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is True
        assert errors == []

    def test_valid_data_date_boundary_leap_year(self):
        # Arrange — 2024 es bisiesto, 29-Feb existe
        data = _valid_data(incident_date="2024-02-29")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is True
        assert errors == []


# ---------------------------------------------------------------------------
# test_empty_title
# Req. 1.4 — título vacío → error de título
# ---------------------------------------------------------------------------

class TestEmptyTitle:
    def test_empty_title_returns_false(self):
        # Arrange
        data = _valid_data(title="")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False

    def test_empty_title_returns_one_error(self):
        # Arrange
        data = _valid_data(title="")

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert
        assert len(errors) == 1

    def test_empty_title_error_mentions_title(self):
        # Arrange
        data = _valid_data(title="")

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert — el mensaje debe mencionar "título"
        assert any("título" in e.lower() or "titulo" in e.lower() for e in errors)

    def test_absent_title_key_returns_error(self):
        # Arrange — clave ausente del diccionario
        data = _valid_data()
        del data["title"]

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# test_whitespace_only_fields
# Req. 1.4–1.6 — campos con solo espacios → errores correspondientes
# ---------------------------------------------------------------------------

class TestWhitespaceOnlyFields:
    def test_whitespace_title_rejected(self):
        # Arrange
        data = _valid_data(title="   ")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert any("título" in e.lower() or "titulo" in e.lower() for e in errors)

    def test_whitespace_description_rejected(self):
        # Arrange
        data = _valid_data(description="\t\n")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert any("descripción" in e.lower() or "descripcion" in e.lower() for e in errors)

    def test_whitespace_location_rejected(self):
        # Arrange
        data = _valid_data(location="  ")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert any("ubicación" in e.lower() or "ubicacion" in e.lower() for e in errors)

    def test_whitespace_date_rejected(self):
        # Arrange — la fecha con espacios no cumple el formato
        data = _valid_data(incident_date="   ")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert any("fecha" in e.lower() for e in errors)

    def test_all_fields_whitespace_returns_four_errors(self):
        # Arrange
        data = {
            "title": "   ",
            "description": "   ",
            "location": "   ",
            "incident_date": "   ",
        }

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert len(errors) == 4


# ---------------------------------------------------------------------------
# test_invalid_date_format — formato incorrecto dd-MM-YYYY
# Req. 1.7 — fecha "31-07-2026" no es AAAA-MM-DD → error de formato
# ---------------------------------------------------------------------------

class TestInvalidDateFormatDMY:
    def test_date_ddmmyyyy_format_rejected(self):
        # Arrange — formato europeo invertido
        data = _valid_data(incident_date="31-07-2026")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False

    def test_date_ddmmyyyy_error_mentions_format(self):
        # Arrange
        data = _valid_data(incident_date="31-07-2026")

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert — el mensaje debe mencionar el formato esperado
        assert any("aaaa-mm-dd" in e.lower() or "2025-07-15" in e for e in errors)

    def test_date_ddmmyyyy_returns_exactly_one_error(self):
        # Arrange — solo la fecha es inválida, el resto está bien
        data = _valid_data(incident_date="31-07-2026")

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert
        assert len(errors) == 1


# ---------------------------------------------------------------------------
# test_non_strict_date — fecha sin ceros "2026-8-2"
# Req. 1.7 — strptime("%Y-%m-%d") no acepta mes/día sin cero → error
# ---------------------------------------------------------------------------

class TestNonStrictDate:
    def test_date_without_leading_zeros_rejected(self):
        # Arrange — "2026-8-2" no cumple el formato estricto %Y-%m-%d
        data = _valid_data(incident_date="2026-8-2")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False

    def test_date_without_leading_zeros_error_count(self):
        # Arrange
        data = _valid_data(incident_date="2026-8-2")

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert
        assert len(errors) == 1

    def test_date_correct_zero_padding_accepted(self):
        # Arrange — la versión con ceros es válida
        data = _valid_data(incident_date="2026-08-02")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is True
        assert errors == []


# ---------------------------------------------------------------------------
# test_nonexistent_date — fecha "2026-02-30" no existe en el calendario
# Req. 1.7 — strptime rechaza fechas inexistentes
# ---------------------------------------------------------------------------

class TestNonexistentDate:
    def test_february_30_rejected(self):
        # Arrange — febrero nunca tiene 30 días
        data = _valid_data(incident_date="2026-02-30")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False

    def test_february_30_error_mentions_format(self):
        # Arrange
        data = _valid_data(incident_date="2026-02-30")

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert
        assert any("aaaa-mm-dd" in e.lower() or "2025-07-15" in e for e in errors)

    def test_month_13_rejected(self):
        # Arrange — mes 13 no existe
        data = _valid_data(incident_date="2026-13-01")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False

    def test_day_32_rejected(self):
        # Arrange — día 32 no existe en ningún mes
        data = _valid_data(incident_date="2026-01-32")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False


# ---------------------------------------------------------------------------
# test_multiple_invalid_fields — acumulación exacta de errores
# Req. 1.8 — varios campos inválidos → todos los mensajes en una sola llamada
# ---------------------------------------------------------------------------

class TestMultipleInvalidFields:
    def test_two_invalid_fields_returns_two_errors(self):
        # Arrange — título y descripción vacíos
        data = _valid_data(title="", description="")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert len(errors) == 2

    def test_three_invalid_fields_returns_three_errors(self):
        # Arrange — título, descripción y fecha inválidos
        data = _valid_data(title="", description="", incident_date="31-07-2026")

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert len(errors) == 3

    def test_four_invalid_fields_returns_four_errors(self):
        # Arrange — todos los campos inválidos
        data = {
            "title": "",
            "description": "",
            "location": "",
            "incident_date": "not-a-date",
        }

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert
        assert is_valid is False
        assert len(errors) == 4

    def test_errors_include_title_message(self):
        # Arrange
        data = {
            "title": "",
            "description": "",
            "location": "",
            "incident_date": "",
        }

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert — debe haber un mensaje de error para el título
        assert any("título" in e.lower() or "titulo" in e.lower() for e in errors)

    def test_errors_include_description_message(self):
        # Arrange
        data = {
            "title": "",
            "description": "",
            "location": "",
            "incident_date": "",
        }

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert — debe haber un mensaje de error para la descripción
        assert any("descripción" in e.lower() or "descripcion" in e.lower() for e in errors)

    def test_errors_include_location_message(self):
        # Arrange
        data = {
            "title": "",
            "description": "",
            "location": "",
            "incident_date": "",
        }

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert
        assert any("ubicación" in e.lower() or "ubicacion" in e.lower() for e in errors)

    def test_errors_include_date_message(self):
        # Arrange
        data = {
            "title": "",
            "description": "",
            "location": "",
            "incident_date": "",
        }

        # Act
        _is_valid, errors = validate_incident_data(data)

        # Assert
        assert any("fecha" in e.lower() for e in errors)

    def test_single_call_returns_all_errors(self):
        """validate_incident_data acumula todos los errores en una sola llamada."""
        # Arrange
        data = {
            "title": "",
            "description": "   ",
            "location": "",
            "incident_date": "31-07-2026",
        }

        # Act
        is_valid, errors = validate_incident_data(data)

        # Assert — una sola llamada, cuatro errores acumulados
        assert is_valid is False
        assert len(errors) == 4
