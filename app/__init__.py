from flask import Flask

from app.config import Config
from app.database import init_db


def create_app(test_config: dict | None = None) -> Flask:
    """Application Factory de SIGI-AI.

    Args:
        test_config: Diccionario opcional con parámetros de configuración para
                     pruebas (p. ej. DATABASE_PATH apuntando a un archivo temporal).
                     Si se proporciona, sobreescribe los valores de Config antes
                     de inicializar la base de datos.

    Returns:
        Instancia configurada de Flask lista para usar.
    """
    app = Flask(__name__, instance_relative_config=False)

    # 1. Cargar la configuración por defecto
    app.config.from_object(Config)

    # 2. Aplicar configuración de prueba si fue proporcionada
    if test_config is not None:
        app.config.update(test_config)

    # 3. Registrar el Blueprint de incidentes
    from app.blueprints.incidents import incidents_bp
    app.register_blueprint(incidents_bp)

    # 4. Inicializar la base de datos (crea la tabla si no existe)
    init_db(app)

    return app
