"""Pruebas unitarias para IncidentRepository.

Usa la fixture ``app`` de conftest.py que provee una base de datos SQLite
temporal aislada por prueba (tmp_path). Nunca toca instance/sigi_ai.db.
Patrón: AAA (Arrange, Act, Assert).
"""

import time
from datetime import datetime, timezone

import pytest

from app.repositories.incident_repository import IncidentRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_incident(**overrides) -> dict:
    """Retorna un diccionario con todos los campos requeridos por save()."""
    base = {
        "title": "Incidente de prueba",
        "description": "Descripción de prueba del incidente.",
        "location": "Sala de servidores",
        "incident_date": "2026-07-31",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "category": "Hardware",
        "priority": "Media",
        "classification_explanation": (
            "El clasificador detectó palabras clave de Hardware en el título. "
            "La prioridad Media fue asignada al no encontrar términos de alta urgencia."
        ),
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# test_save_returns_positive_id
# Req. 1.1 — save() retorna entero positivo
# ---------------------------------------------------------------------------

class TestSaveReturnsPositiveId:
    def test_save_returns_integer(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            incident = _make_incident()

            # Act
            incident_id = repo.save(incident)

            # Assert
            assert isinstance(incident_id, int)

    def test_save_returns_positive_value(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            incident = _make_incident()

            # Act
            incident_id = repo.save(incident)

            # Assert
            assert incident_id > 0

    def test_save_second_record_has_higher_id(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            incident_a = _make_incident(title="Incidente A")
            incident_b = _make_incident(title="Incidente B")

            # Act
            id_a = repo.save(incident_a)
            id_b = repo.save(incident_b)

            # Assert
            assert id_b > id_a


# ---------------------------------------------------------------------------
# test_find_all_ordered_desc
# Req. 3.1 — find_all() ordena por created_at DESC, id DESC
# ---------------------------------------------------------------------------

class TestFindAllOrderedDesc:
    def test_two_incidents_most_recent_first(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            older_ts = "2026-07-01T10:00:00+00:00"
            newer_ts = "2026-07-01T11:00:00+00:00"
            id_old = repo.save(_make_incident(title="Antiguo", created_at=older_ts))
            id_new = repo.save(_make_incident(title="Reciente", created_at=newer_ts))

            # Act
            incidents = repo.find_all()

            # Assert — el más reciente debe aparecer primero
            assert incidents[0]["id"] == id_new
            assert incidents[1]["id"] == id_old

    def test_find_all_returns_all_records(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            for i in range(3):
                repo.save(_make_incident(title=f"Incidente {i}"))

            # Act
            incidents = repo.find_all()

            # Assert
            assert len(incidents) == 3

    def test_same_created_at_orders_by_id_desc(self, app):
        # Arrange — mismo timestamp, el ID más alto debe ir primero
        with app.app_context():
            repo = IncidentRepository()
            ts = "2026-07-01T10:00:00+00:00"
            id_first = repo.save(_make_incident(title="Primero", created_at=ts))
            id_second = repo.save(_make_incident(title="Segundo", created_at=ts))

            # Act
            incidents = repo.find_all()

            # Assert — id_second es mayor → debe aparecer antes
            assert incidents[0]["id"] == id_second
            assert incidents[1]["id"] == id_first


# ---------------------------------------------------------------------------
# test_filter_by_category
# Req. 3.2 — filtro por categoría retorna solo los coincidentes
# ---------------------------------------------------------------------------

class TestFilterByCategory:
    def test_filter_hardware_returns_only_hardware(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident(title="HW", category="Hardware"))
            repo.save(_make_incident(title="SW", category="Software"))
            repo.save(_make_incident(title="HW2", category="Hardware"))

            # Act
            results = repo.find_all(category="Hardware")

            # Assert
            assert len(results) == 2
            assert all(r["category"] == "Hardware" for r in results)

    def test_filter_category_with_no_matches_returns_empty(self, app):
        # Arrange — solo hay Hardware, se filtra por Software
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident(category="Hardware"))

            # Act
            results = repo.find_all(category="Software")

            # Assert
            assert results == []

    def test_filter_por_revisar_category(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident(category="Por revisar"))
            repo.save(_make_incident(category="Hardware"))

            # Act
            results = repo.find_all(category="Por revisar")

            # Assert
            assert len(results) == 1
            assert results[0]["category"] == "Por revisar"


# ---------------------------------------------------------------------------
# test_filter_by_priority
# Req. 3.3 — filtro por prioridad retorna solo los coincidentes
# ---------------------------------------------------------------------------

class TestFilterByPriority:
    def test_filter_alta_returns_only_alta(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident(title="Alta", priority="Alta"))
            repo.save(_make_incident(title="Media", priority="Media"))
            repo.save(_make_incident(title="Baja", priority="Baja"))

            # Act
            results = repo.find_all(priority="Alta")

            # Assert
            assert len(results) == 1
            assert results[0]["priority"] == "Alta"

    def test_filter_baja_returns_only_baja(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident(title="A", priority="Alta"))
            repo.save(_make_incident(title="B", priority="Baja"))
            repo.save(_make_incident(title="C", priority="Baja"))

            # Act
            results = repo.find_all(priority="Baja")

            # Assert
            assert len(results) == 2
            assert all(r["priority"] == "Baja" for r in results)


# ---------------------------------------------------------------------------
# test_filter_combined
# Req. 3.4 — filtro combinado retorna solo los que cumplen ambas condiciones
# ---------------------------------------------------------------------------

class TestFilterCombined:
    def test_combined_hardware_alta_returns_correct_subset(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident(title="HW+Alta",  category="Hardware", priority="Alta"))
            repo.save(_make_incident(title="HW+Media", category="Hardware", priority="Media"))
            repo.save(_make_incident(title="SW+Alta",  category="Software", priority="Alta"))

            # Act
            results = repo.find_all(category="Hardware", priority="Alta")

            # Assert — solo el primero cumple ambas condiciones
            assert len(results) == 1
            assert results[0]["title"] == "HW+Alta"

    def test_combined_no_matches_returns_empty(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident(category="Hardware", priority="Media"))

            # Act
            results = repo.find_all(category="Software", priority="Alta")

            # Assert
            assert results == []

    def test_combined_filter_orders_results_desc(self, app):
        # Arrange — dos coincidencias, verificar orden
        with app.app_context():
            repo = IncidentRepository()
            ts_old = "2026-06-01T10:00:00+00:00"
            ts_new = "2026-07-01T10:00:00+00:00"
            id_old = repo.save(_make_incident(
                title="Antiguo", category="Software", priority="Alta",
                created_at=ts_old,
            ))
            id_new = repo.save(_make_incident(
                title="Reciente", category="Software", priority="Alta",
                created_at=ts_new,
            ))

            # Act
            results = repo.find_all(category="Software", priority="Alta")

            # Assert — el más reciente primero
            assert results[0]["id"] == id_new
            assert results[1]["id"] == id_old


# ---------------------------------------------------------------------------
# test_empty_db_returns_empty_list
# Req. 3.6 — base vacía → lista vacía (sin filtros ni con ellos)
# ---------------------------------------------------------------------------

class TestEmptyDbReturnsEmptyList:
    def test_find_all_no_filter_empty_db(self, app):
        # Arrange — BD recién creada, sin datos
        with app.app_context():
            repo = IncidentRepository()

            # Act
            results = repo.find_all()

            # Assert
            assert results == []

    def test_find_all_with_category_filter_empty_db(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()

            # Act
            results = repo.find_all(category="Hardware")

            # Assert
            assert results == []

    def test_find_all_with_priority_filter_empty_db(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()

            # Act
            results = repo.find_all(priority="Alta")

            # Assert
            assert results == []


# ---------------------------------------------------------------------------
# test_invalid_category_raises_value_error
# Req. 3.7 — categoría inválida lanza ValueError
# ---------------------------------------------------------------------------

class TestInvalidCategoryRaisesValueError:
    def test_invalid_category_raises(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()

            # Act & Assert
            with pytest.raises(ValueError):
                repo.find_all(category="Categoría Inexistente")

    def test_invalid_category_error_message_descriptive(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                repo.find_all(category="INVALIDA")

            # el mensaje debe mencionar la categoría inválida
            assert "INVALIDA" in str(exc_info.value) or "inválida" in str(exc_info.value).lower()

    def test_empty_string_category_raises(self, app):
        # Arrange — cadena vacía no pertenece al conjunto válido
        with app.app_context():
            repo = IncidentRepository()

            # Act & Assert
            with pytest.raises(ValueError):
                repo.find_all(category="")

    def test_none_category_does_not_raise(self, app):
        # Arrange — None significa "sin filtro", no debe lanzar
        with app.app_context():
            repo = IncidentRepository()

            # Act & Assert — no debe lanzar
            results = repo.find_all(category=None)
            assert isinstance(results, list)


# ---------------------------------------------------------------------------
# test_invalid_priority_raises_value_error
# Req. 3.7 — prioridad inválida lanza ValueError
# ---------------------------------------------------------------------------

class TestInvalidPriorityRaisesValueError:
    def test_invalid_priority_raises(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()

            # Act & Assert
            with pytest.raises(ValueError):
                repo.find_all(priority="Urgente")

    def test_invalid_priority_error_message_descriptive(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                repo.find_all(priority="MAXIMA")

            assert "MAXIMA" in str(exc_info.value) or "inválida" in str(exc_info.value).lower()

    def test_empty_string_priority_raises(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()

            # Act & Assert
            with pytest.raises(ValueError):
                repo.find_all(priority="")

    def test_none_priority_does_not_raise(self, app):
        # Arrange — None significa "sin filtro", no debe lanzar
        with app.app_context():
            repo = IncidentRepository()

            # Act & Assert
            results = repo.find_all(priority=None)
            assert isinstance(results, list)


# ---------------------------------------------------------------------------
# test_nine_fields_retrieved
# Req. 3.5 — cada fila recuperada expone los nueve campos
# ---------------------------------------------------------------------------

class TestNineFieldsRetrieved:
    EXPECTED_FIELDS = {
        "id",
        "title",
        "description",
        "location",
        "incident_date",
        "created_at",
        "category",
        "priority",
        "classification_explanation",
    }

    def test_saved_incident_has_nine_fields(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident())

            # Act
            incidents = repo.find_all()

            # Assert
            assert len(incidents) == 1
            assert self.EXPECTED_FIELDS == set(incidents[0].keys())

    def test_all_nine_fields_have_correct_values(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            payload = _make_incident(
                title="Phishing detectado",
                description="Correo malicioso recibido.",
                location="Sede central",
                incident_date="2026-07-15",
                created_at="2026-07-15T12:00:00+00:00",
                category="Seguridad de la Información",
                priority="Alta",
                classification_explanation="Palabra clave phishing detectada. Prioridad Alta asignada.",
            )
            saved_id = repo.save(payload)

            # Act
            incidents = repo.find_all()
            record = incidents[0]

            # Assert — cada campo coincide con lo persistido
            assert record["id"] == saved_id
            assert record["title"] == payload["title"]
            assert record["description"] == payload["description"]
            assert record["location"] == payload["location"]
            assert record["incident_date"] == payload["incident_date"]
            assert record["created_at"] == payload["created_at"]
            assert record["category"] == payload["category"]
            assert record["priority"] == payload["priority"]
            assert record["classification_explanation"] == payload["classification_explanation"]

    def test_find_all_returns_list_of_dicts(self, app):
        # Arrange
        with app.app_context():
            repo = IncidentRepository()
            repo.save(_make_incident())

            # Act
            incidents = repo.find_all()

            # Assert
            assert isinstance(incidents, list)
            assert isinstance(incidents[0], dict)
