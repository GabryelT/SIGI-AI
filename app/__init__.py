from flask import Flask, render_template

from app.config import Config
from app.database import init_db


def create_app(test_config: dict | None = None) -> Flask:
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__, instance_relative_config=False)

    app.config.from_object(Config)

    if test_config is not None:
        app.config.update(test_config)

    from app.blueprints.incidents import incidents_bp

    app.register_blueprint(incidents_bp)
    init_db(app)

    @app.errorhandler(404)
    def page_not_found(_error):
        """Muestra una página amigable cuando una ruta no existe."""
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(_error):
        """Muestra una página amigable ante un error interno."""
        return render_template("errors/500.html"), 500

    return app