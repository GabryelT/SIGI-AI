from flask import Blueprint

# Definir el Blueprint antes de importar las rutas para evitar importación circular
incidents_bp = Blueprint("incidents", __name__)

from app.blueprints.incidents import routes  # noqa: E402, F401
