"""Repositorio de incidentes: encapsula todo el acceso a SQLite.

Usa exclusivamente sentencias SQL parametrizadas con marcadores ``?``
para prevenir inyección SQL.
"""

from contextlib import closing

from flask import current_app

from app.database import get_db_connection

# Conjuntos de valores aceptados para los filtros de consulta.
_VALID_CATEGORIES = frozenset({
    "Seguridad de la Información",
    "Seguridad Física",
    "Hardware",
    "Software",
    "Red/Conectividad",
    "Cuenta/Usuario",
    "Por revisar",
})

_VALID_PRIORITIES = frozenset({"Baja", "Media", "Alta"})


class IncidentRepository:
    """Acceso a datos de la tabla ``incidents``."""

    def find_all(
        self,
        category: str | None = None,
        priority: str | None = None,
    ) -> list[dict]:
        """Retorna todos los incidentes, con filtros opcionales.

        Args:
            category: Categoría exacta por la que filtrar, o ``None`` para
                      no filtrar por categoría.
            priority: Prioridad exacta por la que filtrar, o ``None`` para
                      no filtrar por prioridad.

        Returns:
            Lista de diccionarios con todos los campos de cada incidente,
            ordenados por ``created_at DESC, id DESC``.

        Raises:
            ValueError: Si ``category`` o ``priority`` no pertenecen a los
                        conjuntos de valores permitidos.
        """
        if category is not None and category not in _VALID_CATEGORIES:
            allowed = ", ".join(sorted(_VALID_CATEGORIES))
            raise ValueError(
                f"Categoría inválida: '{category}'. "
                f"Los valores permitidos son: {allowed}."
            )

        if priority is not None and priority not in _VALID_PRIORITIES:
            allowed = ", ".join(sorted(_VALID_PRIORITIES))
            raise ValueError(
                f"Prioridad inválida: '{priority}'. "
                f"Los valores permitidos son: {allowed}."
            )

        conditions: list[str] = []
        params: list[str] = []

        if category is not None:
            conditions.append("category = ?")
            params.append(category)

        if priority is not None:
            conditions.append("priority = ?")
            params.append(priority)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = f"""
            SELECT *
            FROM incidents
            {where_clause}
            ORDER BY created_at DESC, id DESC
        """

        database_path = current_app.config["DATABASE_PATH"]
        connection = get_db_connection(database_path)
        try:
            cursor = connection.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def save(self, incident_data: dict) -> int:
        """Persiste un incidente y retorna el ID generado por SQLite.

        Args:
            incident_data: Diccionario que debe contener exactamente las
                claves ``title``, ``description``, ``location``,
                ``incident_date``, ``created_at``, ``category``,
                ``priority`` y ``classification_explanation``.

        Returns:
            El ``lastrowid`` generado por SQLite (entero positivo).
        """
        database_path = current_app.config["DATABASE_PATH"]

        sql = """
            INSERT INTO incidents (
                title,
                description,
                location,
                incident_date,
                created_at,
                category,
                priority,
                classification_explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            incident_data["title"],
            incident_data["description"],
            incident_data["location"],
            incident_data["incident_date"],
            incident_data["created_at"],
            incident_data["category"],
            incident_data["priority"],
            incident_data["classification_explanation"],
        )

        with closing(get_db_connection(database_path)) as connection:
            cursor = connection.execute(sql, params)
            connection.commit()
            return cursor.lastrowid
