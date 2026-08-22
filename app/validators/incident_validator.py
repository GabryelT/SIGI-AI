"""Validador de datos del formulario de registro de incidentes.

Centraliza toda la validación de los campos obligatorios.
Acumula todos los errores antes de retornar para que el usuario
vea de una sola vez qué campos requieren corrección.
"""
import re
from datetime import datetime


def validate_incident_data(data: dict) -> tuple[bool, list[str]]:
    """Valida los campos obligatorios de un incidente.

    Args:
        data: Diccionario con los datos del formulario. Se esperan las claves
              ``title``, ``description``, ``location`` e ``incident_date``.

    Returns:
        ``(True, [])`` si todos los campos son válidos.
        ``(False, [msg1, msg2, ...])`` con un mensaje por cada campo inválido.
    """
    errors: list[str] = []

    # --- title ---
    title = data.get("title", "")
    if not isinstance(title, str) or not title.strip():
        errors.append("El título es obligatorio.")

    # --- description ---
    description = data.get("description", "")
    if not isinstance(description, str) or not description.strip():
        errors.append("La descripción es obligatoria.")

    # --- location ---
    location = data.get("location", "")
    if not isinstance(location, str) or not location.strip():
        errors.append("La ubicación u origen es obligatoria.")

    # --- incident_date ---
    incident_date = data.get("incident_date", "")
    if not isinstance(incident_date, str) or not incident_date.strip():
        errors.append(
            "La fecha es obligatoria y debe tener el formato AAAA-MM-DD "
            "(por ejemplo: 2025-07-15)."
        )
    else:
        date_value = incident_date.strip()

        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
            errors.append(
                "La fecha debe tener el formato AAAA-MM-DD "
                "(por ejemplo: 2025-07-15)."
            )
        else:
            try:
                datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                errors.append(
                    "La fecha debe tener el formato AAAA-MM-DD "
                    "(por ejemplo: 2025-07-15)."
                )

    if errors:
        return (False, errors)

    return (True, [])
