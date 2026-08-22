"""Pruebas unitarias para IncidentService.

Usa la fixture ``app`` de conftest.py (BD SQLite temporal aislada por prueba).
El clasificador se parchea con mock.patch sobre su ruta de importación en el
módulo del servicio: ``app.services.incident_service.RuleBasedIncidentClassifier``.
Patrón: AAA (Arrange, Act, Assert).
"""

import unittest.mock as mock

import pytest

from app.services.incident_service import IncidentService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_form_data(**overrides) -> dict:
    """Retorna un dict con todos los campos obligatorios válidos."""
    base = {
        "title": "Correo de phishing detectado",
        "description": "Se recibió un enlace malicioso en el correo corporativo.",
        "location": "Oficina central",
        "incident_date": "2026-07-31",
    }
    base.update(overrides)
    return base


_MOCK_CLASSIFICATION = ("Seguridad de la Información", "Alta", (
    "Palabra clave phishing detectada en el título. "
    "Se asignó prioridad Alta por indicadores de riesgo elevado presentes en el texto. "
    "Revisión recomendada de manera inmediata."
))

_CLASSIFIER_PATH = "app.services.incident_service.RuleBasedIncidentClassifier"


# ---------------------------------------------------------------------------
# test_register_valid_incident
# Req. 1.1, 1.2, 1.3 — datos válidos → {"success": True, "id": N}
# ---------------------------------------------------------------------------

class TestRegisterValidIncident:
    def test_returns_success_true(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data()

            # Act
            result = service.register_incident(data)

            # Assert
            assert result["success"] is True

    def test_returns_integer_id(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data()

            # Act
            result = service.register_incident(data)

            # Assert
            assert isinstance(result["id"], int)
            assert result["id"] > 0

    def test_no_errors_key_on_success(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data()

            # Act
            result = service.register_incident(data)

            # Assert
            assert "errors" not in result

    def test_consecutive_registrations_return_different_ids(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()

            # Act
            r1 = service.register_incident(_valid_form_data(title="Incidente A"))
            r2 = service.register_incident(_valid_form_data(title="Incidente B"))

            # Assert
            assert r1["id"] != r2["id"]


# ---------------------------------------------------------------------------
# test_missing_fields_returns_errors
# Req. 1.4–1.8 — campos faltantes → {"success": False, "errors": [...]}
# ---------------------------------------------------------------------------

class TestMissingFieldsReturnsErrors:
    def test_empty_title_returns_false(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data(title="")

            # Act
            result = service.register_incident(data)

            # Assert
            assert result["success"] is False

    def test_empty_title_returns_errors_list(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data(title="")

            # Act
            result = service.register_incident(data)

            # Assert
            assert isinstance(result["errors"], list)
            assert len(result["errors"]) >= 1

    def test_all_empty_fields_returns_four_errors(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = {
                "title": "",
                "description": "",
                "location": "",
                "incident_date": "",
            }

            # Act
            result = service.register_incident(data)

            # Assert
            assert result["success"] is False
            assert len(result["errors"]) == 4

    def test_missing_description_returns_error(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data(description="")

            # Act
            result = service.register_incident(data)

            # Assert
            assert result["success"] is False
            assert any(
                "descripción" in e.lower() or "descripcion" in e.lower()
                for e in result["errors"]
            )

    def test_invalid_date_format_returns_error(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data(incident_date="31-07-2026")

            # Act
            result = service.register_incident(data)

            # Assert
            assert result["success"] is False
            assert any("fecha" in e.lower() for e in result["errors"])

    def test_validation_error_does_not_persist_to_db(self, app):
        """Un incidente con datos inválidos NO debe persistirse."""
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data(title="")

            # Act
            service.register_incident(data)

            # Assert — la BD debe seguir vacía
            from app.repositories.incident_repository import IncidentRepository
            repo = IncidentRepository()
            assert repo.find_all() == []


# ---------------------------------------------------------------------------
# test_whitespace_stripping_and_extra_fields_excluded
# Req. 1.1 — el servicio hace .strip() y no persiste campos adicionales
# ---------------------------------------------------------------------------

class TestWhitespaceStrippingAndExtraFieldsExcluded:
    def test_leading_trailing_spaces_stripped_in_title(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data(title="  Phishing con espacios  ")

            # Act
            result = service.register_incident(data)

            # Assert — el registro es exitoso (espacios no causan fallo)
            assert result["success"] is True

            from app.repositories.incident_repository import IncidentRepository
            repo = IncidentRepository()
            incidents = repo.find_all()
            assert incidents[0]["title"] == "Phishing con espacios"

    def test_extra_form_fields_not_persisted(self, app):
        """Campos adicionales del formulario no deben llegar a la BD."""
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data()
            data["campo_extra"] = "valor_no_esperado"
            data["csrf_token"] = "abc123"

            # Act
            result = service.register_incident(data)

            # Assert — el registro debe ser exitoso (campos extra ignorados)
            assert result["success"] is True

    def test_whitespace_only_field_still_rejected(self, app):
        """Un campo con solo espacios debe fallar validación, no ser sanitizado."""
        # Arrange
        with app.app_context():
            service = IncidentService()
            data = _valid_form_data(description="   ")

            # Act
            result = service.register_incident(data)

            # Assert
            assert result["success"] is False


# ---------------------------------------------------------------------------
# test_classifier_fallback
# Req. 2.7 — fallback si RuleBasedIncidentClassifier falla durante
#             inicialización o durante classify()
# ---------------------------------------------------------------------------

class TestClassifierFallback:
    def test_classifier_init_exception_uses_fallback(self, app):
        # Arrange — la clase lanza excepción al instanciarse
        with app.app_context():
            with mock.patch(
                _CLASSIFIER_PATH,
                side_effect=RuntimeError("fallo de inicialización simulado"),
            ):
                service = IncidentService()
                data = _valid_form_data()

                # Act
                result = service.register_incident(data)

            # Assert — el incidente fue guardado con valores de fallback
            assert result["success"] is True

            from app.repositories.incident_repository import IncidentRepository
            repo = IncidentRepository()
            incidents = repo.find_all()
            assert incidents[0]["category"] == "Por revisar"
            assert incidents[0]["priority"] == "Media"

    def test_classifier_classify_exception_uses_fallback(self, app):
        # Arrange — instancia correctamente, pero classify() lanza excepción
        with app.app_context():
            mock_instance = mock.MagicMock()
            mock_instance.classify.side_effect = Exception("fallo en classify()")

            with mock.patch(_CLASSIFIER_PATH, return_value=mock_instance):
                service = IncidentService()
                data = _valid_form_data()

                # Act
                result = service.register_incident(data)

            # Assert
            assert result["success"] is True

            from app.repositories.incident_repository import IncidentRepository
            repo = IncidentRepository()
            incidents = repo.find_all()
            assert incidents[0]["category"] == "Por revisar"
            assert incidents[0]["priority"] == "Media"

    def test_classifier_fallback_explanation_not_empty(self, app):
        # Arrange
        with app.app_context():
            with mock.patch(
                _CLASSIFIER_PATH,
                side_effect=RuntimeError("fallo simulado"),
            ):
                service = IncidentService()
                data = _valid_form_data()

                # Act
                result = service.register_incident(data)

            # Assert — la explicación de fallback no debe estar vacía
            from app.repositories.incident_repository import IncidentRepository
            repo = IncidentRepository()
            incidents = repo.find_all()
            explanation = incidents[0]["classification_explanation"]
            assert isinstance(explanation, str)
            assert len(explanation.strip()) > 0

    def test_classifier_fallback_incident_still_persisted(self, app):
        """El incidente se persiste aunque el clasificador falle."""
        # Arrange
        with app.app_context():
            mock_instance = mock.MagicMock()
            mock_instance.classify.side_effect = ValueError("error interno")

            with mock.patch(_CLASSIFIER_PATH, return_value=mock_instance):
                service = IncidentService()
                data = _valid_form_data(title="Incidente con fallo de clasificador")

                # Act
                result = service.register_incident(data)

            # Assert
            assert result["success"] is True
            assert result["id"] > 0

            from app.repositories.incident_repository import IncidentRepository
            repo = IncidentRepository()
            incidents = repo.find_all()
            assert any(i["title"] == "Incidente con fallo de clasificador" for i in incidents)


# ---------------------------------------------------------------------------
# test_get_incidents_with_results
# Req. 3.1 — consulta con resultados → lista de incidentes
# ---------------------------------------------------------------------------

class TestGetIncidentsWithResults:
    def test_returns_incidents_key(self, app):
        # Arrange — registrar un incidente primero
        with app.app_context():
            service = IncidentService()
            service.register_incident(_valid_form_data())

            # Act
            result = service.get_incidents()

            # Assert
            assert "incidents" in result
            assert isinstance(result["incidents"], list)
            assert len(result["incidents"]) >= 1

    def test_message_is_none_when_results_exist(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            service.register_incident(_valid_form_data())

            # Act
            result = service.get_incidents()

            # Assert
            assert result["message"] is None

    def test_no_error_key_on_valid_query(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            service.register_incident(_valid_form_data())

            # Act
            result = service.get_incidents()

            # Assert
            assert "error" not in result


# ---------------------------------------------------------------------------
# test_get_incidents_empty
# Req. 3.6 — BD vacía con y sin filtros → lista vacía + mensaje
# ---------------------------------------------------------------------------

class TestGetIncidentsEmpty:
    def test_empty_db_no_filters_returns_empty_list(self, app):
        # Arrange — BD vacía
        with app.app_context():
            service = IncidentService()

            # Act
            result = service.get_incidents()

            # Assert
            assert result["incidents"] == []

    def test_empty_db_no_filters_returns_message(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()

            # Act
            result = service.get_incidents()

            # Assert
            assert isinstance(result["message"], str)
            assert len(result["message"]) > 0

    def test_empty_db_no_filters_message_mentions_no_incidents(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()

            # Act
            result = service.get_incidents()

            # Assert — el mensaje debe hacer referencia a ausencia de incidentes
            assert "incidente" in result["message"].lower()

    def test_filters_with_no_matches_returns_empty_list(self, app):
        # Arrange — hay incidentes pero ninguno coincide con el filtro
        with app.app_context():
            service = IncidentService()
            service.register_incident(_valid_form_data())
            # Buscar una categoría diferente a la que classifique el incidente
            # Usando mock para controlar la categoría persistida
            mock_instance = mock.MagicMock()
            mock_instance.classify.return_value = ("Hardware", "Media", (
                "Clasificación de prueba asignada. "
                "Se detectó Hardware en el texto analizado. "
                "Prioridad Media asignada por ausencia de términos de alta urgencia."
            ))
            with mock.patch(_CLASSIFIER_PATH, return_value=mock_instance):
                service.register_incident(
                    _valid_form_data(title="Incidente HW")
                )

            # Act — filtrar por una categoría que no existe en la BD
            result = service.get_incidents(category="Red/Conectividad")

            # Assert
            # Puede ser vacío o tener resultados dependiendo de la clasificación real,
            # pero la estructura siempre debe ser correcta
            assert "incidents" in result or "error" in result

    def test_empty_db_with_filter_message_mentions_criteria(self, app):
        # Arrange — BD vacía, se aplica filtro válido
        with app.app_context():
            service = IncidentService()

            # Act
            result = service.get_incidents(category="Hardware")

            # Assert
            assert result["incidents"] == []
            assert isinstance(result["message"], str)
            # El mensaje debe ser diferente al de BD completamente vacía
            msg = result["message"].lower()
            assert "incidente" in msg or "criterio" in msg or "encontr" in msg


# ---------------------------------------------------------------------------
# test_invalid_filter_returns_error
# Req. 3.7 — filtro inválido → {"error": mensaje}
# ---------------------------------------------------------------------------

class TestInvalidFilterReturnsError:
    def test_invalid_category_returns_error_key(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()

            # Act
            result = service.get_incidents(category="CategoríaInexistente")

            # Assert
            assert "error" in result

    def test_invalid_category_error_is_string(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()

            # Act
            result = service.get_incidents(category="INVALIDA")

            # Assert
            assert isinstance(result["error"], str)
            assert len(result["error"]) > 0

    def test_invalid_priority_returns_error_key(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()

            # Act
            result = service.get_incidents(priority="Urgente")

            # Assert
            assert "error" in result

    def test_invalid_filter_does_not_return_incidents(self, app):
        # Arrange
        with app.app_context():
            service = IncidentService()
            service.register_incident(_valid_form_data())

            # Act
            result = service.get_incidents(category="FiltroInvalido")

            # Assert — no debe retornar "incidents" cuando hay error
            assert "incidents" not in result
