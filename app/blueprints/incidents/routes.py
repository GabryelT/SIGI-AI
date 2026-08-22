from app.blueprints.incidents import incidents_bp


@incidents_bp.route("/")
def index():
    """Ruta temporal — será reemplazada en Task 4 por una redirección a /incidents."""
    return "SIGI-AI en construcción"
