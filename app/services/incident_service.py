"""Servicio de aplicación para incidentes.

Orquesta la validación, clasificación y persistencia de incidentes.
No accede directamente a la base de datos ni contiene lógica de validación
propia: delega en el validador, el clasificador y el repositorio.
"""

from datetime import datetime, timezone

from app.classifier.rule_based_incident_classifier import RuleBasedIncidentClassifier
from app.repositories.incident_repository import IncidentRepository
from app.validators.incident_validator import validate_incident_data

# Texto de fallback cuando el clasificador produce un error inesperado.
_FALLBACK_EXPLANATION = (
    "La clasificación automática no estuvo disponible debido a un error "
    "interno del sistema. Se asigna la categoría Por revisar con prioridad "
    "Media. Se requiere revisión manual por parte del Oficial de Seguridad "
    "para determinar la categoría y prioridad correctas."
)


class IncidentService:
    """Coordina el flujo de registro y consulta de incidentes."""

    def register_incident(self, data: dict) -> dict:
        """Registra un incidente nuevo aplicando validación y clasificación.

        No modifica el diccionario ``data`` original: trabaja sobre una copia.

        Args:
            data: Campos del formulario. Debe contener ``title``,
                  ``description``, ``location`` e ``incident_date``.

        Returns:
            ``{"success": True, "id": int}`` si el registro fue exitoso.
            ``{"success": False, "errors": list[str]}`` si la validación falló.
        """
        # 1. Validar
        is_valid, errors = validate_incident_data(data)
        if not is_valid:
            return {"success": False, "errors": errors}

        # 2. Construir diccionario limpio con solo los campos permitidos.
        #    .strip() elimina espacios innecesarios e impide que campos
        #    adicionales del formulario lleguen a la capa de datos.
        incident = {
            "title": data["title"].strip(),
            "description": data["description"].strip(),
            "location": data["location"].strip(),
            "incident_date": data["incident_date"].strip(),
        }

        # 3. Clasificar (con fallback ante error de inicialización o classify)
        try:
            classifier = RuleBasedIncidentClassifier()
            category, priority, explanation = classifier.classify(
                incident["title"], incident["description"]
            )
        except Exception:
            category = "Por revisar"
            priority = "Media"
            explanation = _FALLBACK_EXPLANATION

        incident["category"] = category
        incident["priority"] = priority
        incident["classification_explanation"] = explanation

        # 4. Timestamp de creación en UTC
        incident["created_at"] = datetime.now(timezone.utc).isoformat()

        # 5. Persistir
        repository = IncidentRepository()
        incident_id = repository.save(incident)

        return {"success": True, "id": incident_id}

    def get_incidents(
        self,
        category: str | None = None,
        priority: str | None = None,
    ) -> dict:
        """Retorna los incidentes, aplicando filtros opcionales.

        Delega completamente en ``IncidentRepository.find_all()``.

        Args:
            category: Categoría por la que filtrar, o ``None``.
            priority: Prioridad por la que filtrar, o ``None``.

        Returns:
            - ``{"incidents": list, "message": None}`` si hay resultados.
            - ``{"incidents": [], "message": str}`` si no hay resultados
              (el mensaje indica si se usaron filtros o no).
            - ``{"error": str}`` si los filtros tienen valores inválidos.
        """
        has_filters = category is not None or priority is not None

        repository = IncidentRepository()
        try:
            incidents = repository.find_all(category=category, priority=priority)
        except ValueError as exc:
            return {"error": str(exc)}

        if not incidents:
            if has_filters:
                message = "No se encontraron incidentes con los criterios seleccionados."
            else:
                message = "No hay incidentes registrados."
            return {"incidents": [], "message": message}

        return {"incidents": incidents, "message": None}
