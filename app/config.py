import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    # Base de datos SQLite — la carpeta instance/ está excluida del repositorio
    DATABASE_PATH: str = os.path.join(BASE_DIR, "instance", "sigi_ai.db")

    # Clave secreta para firmar sesiones Flask.
    # En producción, establecer la variable de entorno SECRET_KEY.
    # El valor de fallback solo debe usarse en desarrollo local.
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # El modo de depuración está desactivado por defecto.
    # Solo habilitar explícitamente en entornos de desarrollo local.
    DEBUG: bool = False
