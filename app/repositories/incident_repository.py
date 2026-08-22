"""Repositorio de incidentes: encapsula todo el acceso a SQLite.

Usa exclusivamente sentencias SQL parametrizadas con marcadores ``?``
para prevenir inyección SQL.
"""

from contextlib import closing

from flask import current_app

from app.database import get_db_connection


class IncidentRepository:
    """Acceso a datos de la tabla ``incidents``."""

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
