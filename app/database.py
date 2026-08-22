import os
import sqlite3
from contextlib import closing

from flask import Flask


def get_db_connection(database_path: str) -> sqlite3.Connection:
    """Abre y retorna una conexión SQLite con row_factory configurado.

    Las filas retornadas son accesibles por nombre de columna y convertibles
    a diccionario mediante dict(row).
    """
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(app: Flask) -> None:
    """Crea la tabla incidents si no existe, leyendo app/schema.sql.

    Se llama una sola vez al arrancar la aplicación desde create_app().
    contextlib.closing garantiza el cierre explícito de la conexión
    independientemente del resultado de executescript.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    database_path = app.config["DATABASE_PATH"]

    # Garantizar que la carpeta instance/ exista antes de crear el archivo .db
    os.makedirs(os.path.dirname(database_path), exist_ok=True)

    with open(schema_path, encoding="utf-8") as schema_file:
        sql = schema_file.read()

    with closing(get_db_connection(database_path)) as connection:
        connection.executescript(sql)
