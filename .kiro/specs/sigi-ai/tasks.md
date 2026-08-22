# Implementation Plan: SIGI-AI

## Overview

Plan de implementación incremental para el MVP de SIGI-AI. El proyecto usa Python + Flask con arquitectura monolítica modular por capas, SQLite como motor de persistencia y Jinja2 para plantillas. Las tareas están organizadas de forma secuencial: cada una construye sobre la anterior y todas las ramas se integran a `main` mediante Pull Requests independientes.

---

## Tasks

- [ ] 1. Preparar Git y la estructura base del proyecto

  **Rama recomendada:** `chore/project-foundation`

  - [ ] 1.1 Inicializar el repositorio Git y configurar la rama de trabajo con el siguiente orden exacto:
    ```
    git init
    git branch -M main
    git commit --allow-empty -m "chore: initialize repository"
    git switch -c chore/project-foundation
    ```
  - [ ] 1.2 Crear `.gitignore` con las exclusiones definidas en design.md: `instance/*.db`, `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `*.pyo`, `.pytest_cache/`, `*.egg-info/`, `dist/`, `build/`
  - [ ] 1.3 Crear `requirements.txt` con versiones exactas: `Flask==3.1.1` y `pytest==8.3.5`
  - [ ] 1.4 Crear la estructura completa de carpetas según la sección "Project Structure" de design.md: `app/`, `app/blueprints/incidents/`, `app/services/`, `app/validators/`, `app/classifier/`, `app/repositories/`, `app/templates/incidents/`, `app/templates/errors/`, `app/static/css/`, `tests/unit/`, `tests/integration/`, `instance/`
  - [ ] 1.5 Crear todos los archivos `__init__.py` vacíos necesarios: `app/services/__init__.py`, `app/validators/__init__.py`, `app/classifier/__init__.py`, `app/repositories/__init__.py`
  - [ ] 1.6 Crear `app/config.py` con clase `Config` que exponga `DATABASE_PATH` (ruta a `instance/sigi_ai.db`), `SECRET_KEY` (leída de variable de entorno `SECRET_KEY` con fallback documentado para desarrollo) y `DEBUG = False`
  - [ ] 1.7 Crear `app/schema.sql` con el script `CREATE TABLE IF NOT EXISTS incidents (...)` exactamente como se define en la sección "Data Models" de design.md, con las 9 columnas: `id`, `title`, `description`, `location`, `incident_date`, `created_at`, `category`, `priority`, `classification_explanation`
  - [ ] 1.8 Crear `app/database.py` con `get_db_connection()` (con `row_factory = sqlite3.Row`) e `init_db(app)` que lee y ejecuta `schema.sql`
  - [ ] 1.9 Definir `incidents_bp = Blueprint("incidents", __name__)` en `app/blueprints/incidents/__init__.py`; importar `routes` después de crear el Blueprint para evitar importación circular
  - [ ] 1.10 Crear `app/blueprints/incidents/routes.py` con una ruta `GET /` temporal que retorne el texto `"SIGI-AI en construcción"` — esta ruta será reemplazada en Task 4 por la redirección a `/incidents`
  - [ ] 1.11 Implementar `create_app(test_config: dict | None = None)` en `app/__init__.py` con Application Factory pattern:
    - Cargar `Config` por defecto
    - Si `test_config` fue proporcionado, aplicar `app.config.update(test_config)` antes de inicializar SQLite
    - Registrar el blueprint `incidents_bp`
    - Llamar a `init_db(app)` como último paso
  - [ ] 1.12 Crear `run.py` como punto de entrada: importar `create_app`, instanciar la app con `app = create_app()` y llamar `app.run()`
  - [ ] 1.13 Verificar que `python run.py` arranca la aplicación sin errores, que `instance/sigi_ai.db` se crea con la tabla `incidents` y que `http://127.0.0.1:5000` responde con `"SIGI-AI en construcción"`

  **Requisitos que valida:** Base técnica para todos los requisitos del MVP (Requisitos 1, 2 y 3)

  **Resultado esperado:** El proyecto arranca con `python run.py`, la tabla `incidents` existe en SQLite, el servidor responde en `http://127.0.0.1:5000` y `create_app` acepta configuración de prueba mediante `test_config`

  **Comando de verificación:**
  ```
  python run.py
  ```

  **Commit sugerido:** `chore: initialize project structure, git config and Flask Application Factory`

- [ ] 2. Implementar el clasificador inteligente

  **Rama recomendada:** `feature/rule-classifier`

  - [ ] 2.1 Crear `app/classifier/rule_based_incident_classifier.py` con la clase `RuleBasedIncidentClassifier`
  - [ ] 2.2 Implementar función de normalización de texto usando `unicodedata.normalize("NFD", text)` con filtrado de caracteres de categoría `Mn` y conversión a minúsculas
  - [ ] 2.3 Definir `CATEGORY_RULES` con las 6 categorías y sus listas de palabras clave tal como se especifican en design.md: `Seguridad de la Información`, `Seguridad Física`, `Hardware`, `Software`, `Red/Conectividad`, `Cuenta/Usuario`
  - [ ] 2.4 Definir `PRIORITY_RULES` con los 3 niveles (`Alta`, `Media`, `Baja`) y sus palabras clave de riesgo e impacto tal como se especifican en design.md
  - [ ] 2.5 Pre-normalizar todas las palabras clave de `CATEGORY_RULES` y `PRIORITY_RULES` en tiempo de inicialización de la clase
  - [ ] 2.6 Implementar la función de conteo de coincidencias usando expresiones regulares compiladas con límites de palabra `\b` para evaluar palabras completas y frases; cada palabra clave distinta cuenta como máximo una vez
  - [ ] 2.7 Verificar que `"ip"` NO coincide dentro de `"equipo"` — límites de palabra correctamente aplicados
  - [ ] 2.8 Implementar el algoritmo de determinación de categoría: calcular `category_scores`, obtener `max_cat_score`, detectar empates; si `max_cat_score == 0` o hay empate → retornar `("Por revisar", "Media", explicación)`
    - _Requirements: 2.1, 2.5, 2.6, 2.8_
  - [ ] 2.9 Implementar el algoritmo de determinación de prioridad de forma **independiente**: evaluar `PRIORITY_RULES` sobre el mismo texto, aplicar regla de mayor impacto (`Alta` > `Media` > `Baja`), usar `Media` si no hay coincidencias
    - _Requirements: 2.2_
  - [ ] 2.10 Implementar la generación de `Explicación_de_Clasificación`: texto entre 10 y 100 palabras que mencione la categoría, la prioridad y las palabras clave detectadas; en casos de fallback describir la razón (sin coincidencias, ambigüedad o error técnico)
    - _Requirements: 2.3, 2.6, 2.8_
  - [ ] 2.11 Verificar manualmente que `classify("ransomware detectado en servidor", "")` retorna categoría `Seguridad de la Información`, prioridad `Alta`
  - [ ] 2.12 Verificar manualmente que `classify("revisión de equipo de cómputo", "")` no clasifica la palabra `"ip"` dentro de `"equipo"`

  **Requisitos que valida:** Requisito 2 (criterios de aceptación 2.1–2.6, 2.8)

  **Resultado esperado:** El clasificador asigna correctamente categoría y prioridad de forma independiente, maneja empates y ausencia de coincidencias con `Por revisar` / `Media`, y no produce falsos positivos por límites de palabra

  **Comando de verificación:**
  ```
  python -c "from app.classifier.rule_based_incident_classifier import RuleBasedIncidentClassifier; c = RuleBasedIncidentClassifier(); print(c.classify('ransomware en red', 'acceso no autorizado detectado'))"
  ```

  **Commit sugerido:** `feat: implement RuleBasedIncidentClassifier with independent category and priority rules`

- [ ] 3. Implementar el registro de incidentes

  **Rama recomendada:** `feature/incident-registration`

  - [ ] 3.1 Crear `app/validators/incident_validator.py` con la función `validate_incident_data(data: dict) -> tuple[bool, list[str]]`
    - _Requirements: 1.4, 1.5, 1.6, 1.7, 1.8_
  - [ ] 3.2 Implementar validación de `title`: rechazar si está vacío o compuesto solo de espacios en blanco
    - _Requirements: 1.4_
  - [ ] 3.3 Implementar validación de `description`: rechazar si está vacío o compuesto solo de espacios en blanco
    - _Requirements: 1.5_
  - [ ] 3.4 Implementar validación de `location`: rechazar si está vacío o compuesto solo de espacios en blanco
    - _Requirements: 1.6_
  - [ ] 3.5 Implementar validación de `incident_date`: rechazar si está vacío o no cumple el formato `AAAA-MM-DD` (verificar con `datetime.strptime(value, "%Y-%m-%d")`)
    - _Requirements: 1.7_
  - [ ] 3.6 Verificar que la función acumula todos los errores antes de retornar — si hay tres campos inválidos, retorna los tres mensajes en una sola llamada
    - _Requirements: 1.8_
  - [ ] 3.7 Crear `app/repositories/incident_repository.py` con la clase `IncidentRepository` y el método `save(incident_data: dict) -> int`
  - [ ] 3.8 Implementar `save()` usando la siguiente sentencia SQL parametrizada con exactamente 8 columnas y 8 marcadores (el campo `id` no se incluye porque SQLite lo genera automáticamente con AUTOINCREMENT):
    ```sql
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
    ```
    Retornar `cursor.lastrowid` como ID generado.
    - _Requirements: 1.1_
  - [ ] 3.9 Crear `app/services/incident_service.py` con la clase `IncidentService` y el método `register_incident(data: dict) -> dict`
  - [ ] 3.10 Implementar `register_incident()` según el flujo de design.md: invocar validador → si inválido retornar errores → invocar clasificador en `try/except Exception` con fallback → agregar `created_at = datetime.now(timezone.utc).isoformat()` → invocar `IncidentRepository.save()` → retornar `{"success": True, "id": id_generado}`
    - _Requirements: 1.1, 1.2, 1.3, 2.4, 2.7_
  - [ ] 3.11 Implementar ruta `GET /incidents/new` en `app/blueprints/incidents/routes.py` que renderice `register.html` con el formulario vacío
  - [ ] 3.12 Implementar ruta `POST /incidents/new` que reciba `request.form`, delegue en `IncidentService.register_incident()` y renderice `register.html` con confirmación o lista de errores según el resultado
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 1.7, 1.8_
  - [ ] 3.13 Crear `app/templates/base.html` con estructura HTML5, bloque `{% block title %}`, bloque `{% block content %}` y enlace al CSS
  - [ ] 3.14 Crear `app/templates/incidents/register.html` extendiendo `base.html` con: formulario POST con campos `title`, `description`, `location`, `incident_date`; visualización de la lista de errores de validación cuando existan; mensaje de confirmación con el ID del incidente cuando el registro sea exitoso; todos los textos en español
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 1.7, 1.8_
  - [ ] 3.15 Crear `app/static/css/styles.css` con estilos base (se completa en Task 6)
  - [ ] 3.16 Verificar el flujo completo: acceder a `GET /incidents/new`, enviar formulario vacío (deben aparecer mensajes de error), enviar formulario completo (debe aparecer confirmación con ID)

  **Requisitos que valida:** Requisito 1 (criterios 1.1–1.8) y Requisito 2 (criterios 2.4, 2.7)

  **Resultado esperado:** El formulario de registro valida campos, invoca el clasificador, persiste el incidente y muestra confirmación con ID; los errores se muestran en español por campo

  **Comando de verificación:**
  ```
  python run.py
  ```
  Navegar a `http://127.0.0.1:5000/incidents/new`

  **Commit sugerido:** `feat: implement incident registration with validation, classification and persistence`

- [ ] 4. Implementar consulta y filtros

  **Rama recomendada:** `feature/incident-list`

  - [ ] 4.1 Agregar método `find_all(category: str | None, priority: str | None) -> list[dict]` a `IncidentRepository`
  - [ ] 4.2 Implementar validación de dominio en `find_all()`: si `category` no pertenece al conjunto válido de 7 categorías → lanzar `ValueError` con mensaje descriptivo; si `priority` no pertenece a `{Baja, Media, Alta}` → lanzar `ValueError`
    - _Requirements: 3.7_
  - [ ] 4.3 Implementar construcción dinámica de cláusula `WHERE` según los filtros presentes, usando parámetros `?`
    - _Requirements: 3.2, 3.3, 3.4_
  - [ ] 4.4 Implementar `SELECT * FROM incidents ORDER BY created_at DESC, id DESC`
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [ ] 4.5 Convertir cada `sqlite3.Row` a `dict(row)` antes de retornar la lista
    - _Requirements: 3.5_
  - [ ] 4.6 Agregar método `get_incidents(category: str | None, priority: str | None) -> dict` a `IncidentService`
  - [ ] 4.7 Implementar `get_incidents()`: invocar `find_all()` en `try/except ValueError`; si `ValueError` → retornar `{"error": mensaje}`; si lista vacía sin filtros → retornar mensaje `"No hay incidentes registrados."`; si lista vacía con filtros → retornar mensaje `"No se encontraron incidentes con los criterios seleccionados."`; si hay resultados → retornar `{"incidents": lista, "message": None}`
    - _Requirements: 3.6, 3.7, 3.8_
  - [ ] 4.8 Reemplazar la ruta temporal `GET /` por la redirección definitiva a `/incidents` en `app/blueprints/incidents/routes.py`
  - [ ] 4.9 Implementar ruta `GET /incidents` en el blueprint: leer parámetros `category` y `priority` de `request.args`, delegar en `IncidentService.get_incidents()` y renderizar `list.html`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_
  - [ ] 4.10 Crear `app/templates/incidents/list.html` extendiendo `base.html` con: formulario de filtros con selectores de categoría y prioridad (valores del Glosario); tabla o listado de incidentes con los 9 campos definidos en design.md (`id`, `title`, `description`, `location`, `incident_date`, `created_at`, `category`, `priority`, `classification_explanation`); mensaje cuando la lista esté vacía; mensaje de error cuando el filtro sea inválido; todos los textos en español
    - _Requirements: 3.5, 3.6, 3.7, 3.8_
  - [ ] 4.11 Verificar que el listado sin filtros muestra todos los incidentes de más reciente a más antiguo
  - [ ] 4.12 Verificar que el filtro por categoría retorna únicamente incidentes de esa categoría
  - [ ] 4.13 Verificar que el filtro combinado retorna únicamente incidentes que cumplen ambas condiciones
  - [ ] 4.14 Verificar que un filtro inválido (`?category=Invalida`) muestra el mensaje de error con los valores permitidos

  **Requisitos que valida:** Requisito 3 (criterios 3.1–3.8)

  **Resultado esperado:** El listado muestra todos los incidentes ordenados correctamente; los filtros funcionan de forma individual y combinada; los filtros inválidos muestran error descriptivo en español

  **Comando de verificación:**
  ```
  python run.py
  ```
  Navegar a `http://127.0.0.1:5000/incidents` y probar los filtros

  **Commit sugerido:** `feat: implement incident list with category and priority filters ordered by created_at DESC`

- [ ] 5. Implementar pruebas

  **Rama recomendada:** `test/software-tests`

  - [ ] 5.1 Crear `tests/conftest.py` con fixtures compartidos usando `tmp_path` de Pytest para aislamiento completo:
    ```python
    @pytest.fixture
    def app(tmp_path):
        test_database = tmp_path / "test_sigi_ai.db"
        application = create_app({
            "TESTING": True,
            "DATABASE_PATH": str(test_database),
            "SECRET_KEY": "test-secret"
        })
        yield application

    @pytest.fixture
    def client(app):
        return app.test_client()
    ```
    Cada prueba trabaja con un archivo de BD temporal independiente, creado y eliminado automáticamente por Pytest. No usar `DATABASE = ":memory:"`.
  - [ ] 5.2 Crear `tests/unit/test_validator.py` con las pruebas del validador (patrón AAA):
    - `test_valid_data_returns_true`: datos completos y válidos → retorna `(True, [])`
    - `test_empty_title_returns_error`: título vacío → retorna error específico para `title`
    - `test_whitespace_only_fields_rejected`: campos con solo espacios → retorna errores correspondientes
    - `test_invalid_date_format_rejected`: fecha `"31-07-2025"` → retorna error de formato
    - `test_multiple_invalid_fields`: tres campos inválidos → retorna tres mensajes de error
    - _Requirements: 1.4, 1.5, 1.6, 1.7, 1.8_
  - [ ] 5.3 Crear `tests/unit/test_classifier.py` con las pruebas del clasificador (patrón AAA):
    - `test_classify_known_category`: título con `"phishing"` → categoría `Seguridad de la Información`
    - `test_classify_high_priority_keywords`: texto con `"ransomware"` → prioridad `Alta`
    - `test_classify_no_keywords`: sin palabras clave → `("Por revisar", "Media", ...)`
    - `test_classify_tie_returns_review`: texto con igual coincidencia en dos categorías → `("Por revisar", "Media", ...)`
    - `test_keyword_boundary_no_false_match`: `"equipo de computo"` no debe coincidir con la clave `"ip"`
    - `test_priority_independent_of_category`: incidente de Hardware con `"servicio caido"` → prioridad `Alta`
    - `test_explanation_not_empty`: la explicación generada nunca es cadena vacía
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 2.8_
  - [ ] 5.4 Crear `tests/unit/test_repository.py` con las pruebas del repositorio (patrón AAA), usando la fixture `app` con BD temporal:
    - `test_save_returns_positive_id`: `save()` retorna entero positivo
    - `test_find_all_ordered_desc`: dos incidentes → el más reciente aparece primero
    - `test_filter_by_category`: `find_all(category="Hardware", priority=None)` retorna solo incidentes Hardware
    - `test_filter_by_priority`: `find_all(category=None, priority="Alta")` retorna solo incidentes de prioridad Alta
    - `test_filter_combined`: filtro por categoría y prioridad → solo incidentes que cumplen ambos
    - `test_empty_db_returns_empty_list`: BD vacía → lista vacía
    - `test_invalid_category_raises_value_error`: categoría `"Invalida"` → lanza `ValueError`
    - _Requirements: 1.1, 3.1, 3.2, 3.3, 3.4, 3.6, 3.7_
  - [ ] 5.5 Crear `tests/unit/test_service.py` con las pruebas del servicio usando un doble (mock) del clasificador (patrón AAA):
    - `test_register_valid_incident`: datos válidos → `{"success": True, "id": N}`
    - `test_register_missing_fields_returns_errors`: campos faltantes → `{"success": False, "errors": [...]}`
    - `test_classifier_error_fallback`: clasificador lanza excepción → incidente guardado con `Por revisar` / `Media`
    - `test_get_incidents_returns_list`: BD con incidentes → lista no vacía
    - `test_get_incidents_invalid_filter`: filtro inválido → `{"error": mensaje}`
    - _Requirements: 1.1, 1.4, 1.8, 2.7, 3.6, 3.7_
  - [ ] 5.6 Crear `tests/integration/test_routes.py` con las pruebas de rutas Flask end-to-end (patrón AAA), usando la fixture `client`:
    - `test_get_new_form_renders_200`: `GET /incidents/new` → HTTP 200
    - `test_post_valid_incident_success`: `POST /incidents/new` con datos válidos → HTTP 200 con confirmación
    - `test_post_missing_fields_returns_errors`: `POST` con campos faltantes → HTTP 200 con mensajes de error en español
    - `test_get_incidents_no_filter`: `GET /incidents` → HTTP 200 con listado
    - `test_get_incidents_with_valid_filter`: `GET /incidents?category=Hardware` → HTTP 200
    - `test_get_incidents_invalid_filter`: `GET /incidents?category=Invalida` → HTTP 200 con mensaje de error
    - `test_get_incidents_empty_db`: `GET /incidents` con BD vacía → HTTP 200 con mensaje de lista vacía
    - _Requirements: 1.1, 1.4, 1.8, 3.1, 3.2, 3.6, 3.7, 3.8_
  - [ ] 5.7 Ejecutar la suite completa y verificar que todas las pruebas pasan

  **Requisitos que valida:** Requisitos 1, 2 y 3 (trazabilidad completa según design.md)

  **Resultado esperado:** Todas las pruebas pasan sin errores; cada prueba usa una BD temporal aislada y eliminable automáticamente; cobertura de los tres requisitos del MVP

  **Comando de verificación:**
  ```
  pytest tests/ -v
  ```

  **Commit sugerido:** `test: add unit and integration tests for validator, classifier, repository, service and routes`

- [ ] 6. Completar la interfaz y revisión de seguridad

  **Rama recomendada:** `feature/ui-and-security`

  - [ ] 6.1 Crear `app/templates/errors/404.html` extendiendo `base.html` con mensaje amigable en español para errores 404 (página no encontrada), sin exponer información técnica interna
  - [ ] 6.2 Crear `app/templates/errors/500.html` extendiendo `base.html` con mensaje amigable en español para errores 500 (error interno del servidor), sin exponer trazas técnicas
  - [ ] 6.3 Registrar los manejadores de error HTTP 404 y 500 en `create_app()` dentro de `app/__init__.py`, que rendericen `errors/404.html` y `errors/500.html` respectivamente
  - [ ] 6.4 Completar `app/templates/base.html` con navegación principal (enlaces a "Registrar incidente" y "Consultar incidentes"), estructura semántica HTML5 accesible y enlace al CSS
  - [ ] 6.5 Completar `app/static/css/styles.css` con estilos responsivos: tipografía legible, formularios accesibles, tabla de incidentes adaptable a pantalla, colores de prioridad diferenciados (rojo para Alta, amarillo para Media, verde para Baja), mensajes de error visibles; interfaz completamente en español
  - [ ] 6.6 Revisar `register.html` y `list.html`: verificar que todos los textos, etiquetas, mensajes de error y confirmación están en español; verificar que los valores de los campos se conservan al re-renderizar con errores
  - [ ] 6.7 Verificar seguridad — SQL parametrizado: revisar que todas las sentencias SQL en `IncidentRepository` usan marcadores `?` y no concatenación de strings
  - [ ] 6.8 Verificar seguridad — escape Jinja2: confirmar que ninguna plantilla usa `| safe` en datos provenientes del usuario
  - [ ] 6.9 Verificar seguridad — `DEBUG`: confirmar que `app/config.py` tiene `DEBUG = False` por defecto y que `run.py` no sobreescribe este valor en producción
  - [ ] 6.10 Verificar seguridad — `SECRET_KEY`: confirmar que se carga desde variable de entorno `SECRET_KEY` y que el fallback de desarrollo está claramente documentado con comentario
  - [ ] 6.11 Ejecutar la suite de pruebas completa y confirmar que todo pasa después de los cambios de interfaz y seguridad

  **Requisitos que valida:** Calidad y seguridad transversal a los tres requisitos

  **Resultado esperado:** Las plantillas de error 404 y 500 están creadas y registradas; la interfaz es funcional, responsiva y completamente en español; todas las medidas de seguridad del design.md están implementadas y verificadas; todas las pruebas siguen pasando

  **Comando de verificación:**
  ```
  pytest tests/ -v
  ```

  **Commit sugerido:** `feat: complete UI templates, error pages, responsive CSS and security review`

- [ ] 7. Documentación y entrega

  **Rama recomendada:** `docs/readme`

  - [ ] 7.1 Crear `README.md` con las siguientes secciones en español:
    - **Descripción del problema:** contexto y justificación de SIGI-AI
    - **Requisitos del sistema:** Python 3.10+, pip, navegador web
    - **Arquitectura:** descripción de las capas y el patrón Application Factory; incluir el diagrama Mermaid de arquitectura de design.md
    - **Instalación:** pasos para clonar el repositorio, crear entorno virtual, instalar dependencias con `pip install -r requirements.txt`
    - **Configuración:** instrucciones para establecer `SECRET_KEY` como variable de entorno
    - **Ejecución:** comando `python run.py` y URL de acceso `http://127.0.0.1:5000`
    - **Pruebas:** comando `pytest tests/ -v` y descripción breve de la cobertura
    - **Uso del sistema:** descripción de las tres funcionalidades del MVP con descripción de las pantallas
    - **Uso de Kiro:** sección que documente cómo se usó Kiro IDE para generar `requirements.md`, `design.md` y `tasks.md`; mencionar el workflow Spec-Driven Development
  - [ ] 7.2 Incluir el diagrama de secuencia de registro y clasificación de design.md en el README
  - [ ] 7.3 Documentar la estrategia de ramas utilizada: `chore/project-foundation`, `feature/rule-classifier`, `feature/incident-registration`, `feature/incident-list`, `test/software-tests`, `feature/ui-and-security`, `docs/readme`
  - [ ] 7.4 Documentar el proceso de Pull Requests hacia `main` en GitHub: una PR por rama, con título descriptivo y descripción que incluya los requisitos validados
  - [ ] 7.5 Preparar evidencias para la entrega académica: capturas de pantalla del listado de ramas en GitHub, capturas de las PRs fusionadas, salida de `pytest tests/ -v` con todas las pruebas pasando
  - [ ] 7.6 Ejecutar `pytest tests/ -v` final para confirmar que la suite completa pasa antes de la entrega
  - [ ] 7.7 Crear la PR de `docs/readme` hacia `main` en GitHub y hacer merge

  **Requisitos que valida:** Entregable académico completo

  **Resultado esperado:** `README.md` completo, evidencias de control de versiones en GitHub preparadas, suite de pruebas pasando al 100%, proyecto listo para entrega

  **Comando de verificación:**
  ```
  pytest tests/ -v
  ```

  **Commit sugerido:** `docs: add README with problem description, architecture, installation and Kiro workflow`

---

## Notes

- Las tareas son estrictamente secuenciales; cada una depende de la anterior
- Todos los cambios se integran a `main` mediante Pull Requests en GitHub — no se hace push directo a `main`
- Cada tarea corresponde a una rama independiente: `chore/project-foundation`, `feature/rule-classifier`, `feature/incident-registration`, `feature/incident-list`, `test/software-tests`, `feature/ui-and-security`, `docs/readme`
- El alcance del MVP cubre exactamente tres requisitos funcionales: Registrar, Clasificar y Consultar
- No están incluidos en el alcance: autenticación, edición/eliminación de incidentes, notificaciones, dashboard estadístico, Docker ni servicios externos

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12", "1.13"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10", "2.11", "2.12"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15", "3.16"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "4.10", "4.11", "4.12", "4.13", "4.14"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7"] },
    { "id": 5, "tasks": ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8", "6.9", "6.10", "6.11"] },
    { "id": 6, "tasks": ["7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "7.7"] }
  ]
}
```
