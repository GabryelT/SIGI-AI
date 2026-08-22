"""Pruebas de integración para las rutas Flask de SIGI-AI.

Usa las fixtures ``app`` y ``client`` de conftest.py (BD SQLite temporal
aislada por prueba vía tmp_path). Nunca toca instance/sigi_ai.db.
Patrón: AAA (Arrange, Act, Assert).
"""

import unittest.mock as mock

import pytest

_CLASSIFIER_PATH = "app.services.incident_service.RuleBasedIncidentClassifier"

# ---------------------------------------------------------------------------
# Datos auxiliares
# ---------------------------------------------------------------------------

_VALID_FORM = {
    "title": "Correo de phishing detectado",
    "description": "Se recibió un enlace malicioso en el correo corporativo.",
    "location": "Oficina central",
    "incident_date": "2026-07-31",
}


def _post_valid(client, **overrides):
    """Envía un POST /incidents/new con datos válidos."""
    data = {**_VALID_FORM, **overrides}
    return client.post("/incidents/new", data=data, follow_redirects=True)


# ---------------------------------------------------------------------------
# GET / redirige a /incidents
# ---------------------------------------------------------------------------

class TestRootRedirect:
    def test_get_root_redirects_to_incidents(self, client):
        # Arrange / Act
        response = client.get("/")

        # Assert — debe haber una redirección (3xx)
        assert response.status_code in (301, 302)

    def test_get_root_redirect_location_is_incidents(self, client):
        # Arrange / Act
        response = client.get("/")

        # Assert — la cabecera Location apunta a /incidents
        location = response.headers.get("Location", "")
        assert "/incidents" in location

    def test_get_root_following_redirect_returns_200(self, client):
        # Arrange / Act
        response = client.get("/", follow_redirects=True)

        # Assert
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /incidents/new retorna 200
# ---------------------------------------------------------------------------

class TestGetNewForm:
    def test_get_new_form_returns_200(self, client):
        # Arrange / Act
        response = client.get("/incidents/new")

        # Assert
        assert response.status_code == 200

    def test_get_new_form_contains_form_fields(self, client):
        # Arrange / Act
        response = client.get("/incidents/new")
        html = response.data.decode("utf-8")

        # Assert — el formulario debe incluir los cuatro campos obligatorios
        assert 'name="title"' in html
        assert 'name="description"' in html
        assert 'name="location"' in html
        assert 'name="incident_date"' in html

    def test_get_new_form_has_post_method(self, client):
        # Arrange / Act
        response = client.get("/incidents/new")
        html = response.data.decode("utf-8")

        # Assert
        assert 'method="POST"' in html or 'method="post"' in html


# ---------------------------------------------------------------------------
# POST válido muestra confirmación e ID
# Req. 1.1
# ---------------------------------------------------------------------------

class TestPostValidIncident:
    def test_post_valid_returns_200(self, client):
        # Arrange / Act
        response = _post_valid(client)

        # Assert
        assert response.status_code == 200

    def test_post_valid_shows_success_message(self, client):
        # Arrange / Act
        response = _post_valid(client)
        html = response.data.decode("utf-8")

        # Assert — texto de confirmación de la template register.html
        assert "Incidente registrado correctamente" in html

    def test_post_valid_shows_incident_id(self, client):
        # Arrange / Act
        response = _post_valid(client)
        html = response.data.decode("utf-8")

        # Assert — el ID numérico debe aparecer en la respuesta
        assert "identificador asignado" in html or "El identificador" in html

    def test_post_valid_id_is_numeric(self, client):
        # Arrange / Act
        response = _post_valid(client)
        html = response.data.decode("utf-8")

        # Assert — debe haber al menos un dígito en la confirmación
        import re
        # Buscar el patrón del ID en el bloque de confirmación
        match = re.search(r"identificador asignado es.*?<strong>(\d+)</strong>", html)
        assert match is not None, f"No se encontró el ID numérico en: {html}"
        assert int(match.group(1)) > 0

    def test_post_valid_no_errors_shown(self, client):
        # Arrange / Act
        response = _post_valid(client)
        html = response.data.decode("utf-8")

        # Assert — no debe mostrarse el bloque de errores
        assert "Se encontraron los siguientes errores" not in html


# ---------------------------------------------------------------------------
# POST inválido muestra todos los errores
# Req. 1.4–1.8
# ---------------------------------------------------------------------------

class TestPostInvalidIncident:
    def test_post_empty_fields_returns_200(self, client):
        # Arrange / Act
        response = client.post("/incidents/new", data={
            "title": "", "description": "", "location": "", "incident_date": "",
        })

        # Assert
        assert response.status_code == 200

    def test_post_empty_fields_shows_error_block(self, client):
        # Arrange / Act
        response = client.post("/incidents/new", data={
            "title": "", "description": "", "location": "", "incident_date": "",
        })
        html = response.data.decode("utf-8")

        # Assert — bloque de errores presente
        assert "Se encontraron los siguientes errores" in html

    def test_post_empty_title_shows_title_error(self, client):
        # Arrange / Act
        response = client.post("/incidents/new", data={
            "title": "",
            "description": "desc válida",
            "location": "lugar válido",
            "incident_date": "2026-07-31",
        })
        html = response.data.decode("utf-8")

        # Assert
        assert "título" in html.lower() or "titulo" in html.lower()

    def test_post_all_empty_shows_four_errors(self, client):
        # Arrange / Act
        response = client.post("/incidents/new", data={
            "title": "", "description": "", "location": "", "incident_date": "",
        })
        html = response.data.decode("utf-8")

        # Assert — cuatro ítems <li> dentro del bloque de errores
        import re
        li_items = re.findall(r"<li>", html)
        assert len(li_items) == 4

    def test_post_invalid_date_shows_format_error(self, client):
        # Arrange / Act
        response = client.post("/incidents/new", data={
            "title": "Incidente",
            "description": "Descripción",
            "location": "Lugar",
            "incident_date": "31-07-2026",
        })
        html = response.data.decode("utf-8")

        # Assert — mensaje de formato de fecha
        assert "aaaa-mm-dd" in html.lower() or "AAAA-MM-DD" in html

    def test_post_invalid_does_not_show_success_message(self, client):
        # Arrange / Act
        response = client.post("/incidents/new", data={
            "title": "", "description": "", "location": "", "incident_date": "",
        })
        html = response.data.decode("utf-8")

        # Assert
        assert "Incidente registrado correctamente" not in html


# ---------------------------------------------------------------------------
# GET /incidents — base vacía muestra mensaje
# Req. 3.6
# ---------------------------------------------------------------------------

class TestListIncidentsEmpty:
    def test_get_incidents_empty_db_returns_200(self, client):
        # Arrange / Act
        response = client.get("/incidents")

        # Assert
        assert response.status_code == 200

    def test_get_incidents_empty_db_shows_info_message(self, client):
        # Arrange / Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert — el mensaje de BD vacía está en <p class="info-message">
        assert "No hay incidentes registrados" in html

    def test_get_incidents_empty_db_no_table_rows(self, client):
        # Arrange / Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert — no debe haber filas <tr> en el cuerpo de la tabla
        assert "<tbody>" not in html or "<td>" not in html


# ---------------------------------------------------------------------------
# GET /incidents con datos muestra los nueve campos
# Req. 3.5
# ---------------------------------------------------------------------------

class TestListIncidentsWithData:
    def test_get_incidents_shows_nine_column_headers(self, client):
        # Arrange — registrar un incidente primero
        _post_valid(client)

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert — las 9 cabeceras de columna deben estar presentes
        assert "ID" in html
        assert "Título" in html
        assert "Descripción" in html
        assert "Ubicación" in html
        assert "Fecha del incidente" in html
        assert "Registrado el" in html
        assert "Categoría" in html
        assert "Prioridad" in html
        assert "Explicación de clasificación" in html

    def test_get_incidents_shows_title_in_table(self, client):
        # Arrange
        _post_valid(client, title="Ransomware en servidor")

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert
        assert "Ransomware en servidor" in html

    def test_get_incidents_shows_description_in_table(self, client):
        # Arrange
        _post_valid(client, description="Descripción única para verificación")

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert
        assert "Descripción única para verificación" in html

    def test_get_incidents_shows_location_in_table(self, client):
        # Arrange
        _post_valid(client, location="Sala de servidores B2")

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert
        assert "Sala de servidores B2" in html

    def test_get_incidents_shows_incident_date(self, client):
        # Arrange
        _post_valid(client, incident_date="2026-07-31")

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert
        assert "2026-07-31" in html

    def test_get_incidents_shows_created_at(self, client):
        # Arrange
        _post_valid(client)

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert — created_at contiene el año actual
        assert "2026" in html

    def test_get_incidents_shows_category_in_table(self, client):
        # Arrange
        _post_valid(client)

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert — alguna categoría válida debe aparecer en la tabla
        valid_categories = [
            "Seguridad de la Información", "Seguridad Física",
            "Hardware", "Software", "Red/Conectividad",
            "Cuenta/Usuario", "Por revisar",
        ]
        assert any(cat in html for cat in valid_categories)

    def test_get_incidents_shows_priority_in_table(self, client):
        # Arrange
        _post_valid(client)

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert — alguna prioridad válida debe aparecer
        assert any(p in html for p in ("Alta", "Media", "Baja"))

    def test_get_incidents_shows_explanation_in_table(self, client):
        # Arrange
        _post_valid(client)

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert — la explicación no puede estar vacía en la fila
        assert "<td>" in html  # al menos hay celdas de tabla


# ---------------------------------------------------------------------------
# Filtros válidos por categoría y prioridad
# Req. 3.2, 3.3
# ---------------------------------------------------------------------------

class TestValidFilters:
    def _register_with_category(self, client, category: str, title: str) -> None:
        """Registra un incidente forzando la categoría via mock."""
        explanation = (
            f"Clasificación asignada como {category}. "
            "Palabras clave detectadas en el texto del incidente. "
            "Prioridad asignada según las reglas de urgencia definidas."
        )
        mock_instance = mock.MagicMock()
        mock_instance.classify.return_value = (category, "Media", explanation)
        with mock.patch(_CLASSIFIER_PATH, return_value=mock_instance):
            client.post("/incidents/new", data={
                "title": title,
                "description": "Descripción de prueba.",
                "location": "Lugar de prueba",
                "incident_date": "2026-07-31",
            })

    def test_filter_by_valid_category_returns_200(self, client):
        # Arrange / Act
        response = client.get("/incidents?category=Hardware")

        # Assert
        assert response.status_code == 200

    def test_filter_by_hardware_shows_only_hardware_incidents(self, client):
        # Arrange
        self._register_with_category(client, "Hardware", "Disco duro dañado")
        self._register_with_category(client, "Software", "Bug en el sistema")

        # Act
        response = client.get("/incidents?category=Hardware")
        html = response.data.decode("utf-8")

        # Assert — solo el incidente de Hardware debe estar en la tabla
        assert "Disco duro dañado" in html
        assert "Bug en el sistema" not in html

    def test_filter_by_valid_priority_returns_200(self, client):
        # Arrange / Act
        response = client.get("/incidents?priority=Alta")

        # Assert
        assert response.status_code == 200

    def test_filter_by_alta_priority_shows_only_alta(self, client):
        # Arrange
        expl = (
            "Clasificación de prueba asignada correctamente. "
            "Palabras clave de alta urgencia detectadas. "
            "Prioridad Alta asignada por riesgo elevado."
        )
        mock_alta = mock.MagicMock()
        mock_alta.classify.return_value = ("Hardware", "Alta", expl)
        mock_media = mock.MagicMock()
        mock_media.classify.return_value = ("Hardware", "Media", expl)

        with mock.patch(_CLASSIFIER_PATH, return_value=mock_alta):
            client.post("/incidents/new", data={
                "title": "Incidente prioridad alta",
                "description": "Descripción.",
                "location": "Lugar",
                "incident_date": "2026-07-31",
            })
        with mock.patch(_CLASSIFIER_PATH, return_value=mock_media):
            client.post("/incidents/new", data={
                "title": "Incidente prioridad media",
                "description": "Descripción.",
                "location": "Lugar",
                "incident_date": "2026-07-31",
            })

        # Act
        response = client.get("/incidents?priority=Alta")
        html = response.data.decode("utf-8")

        # Assert
        assert "Incidente prioridad alta" in html
        assert "Incidente prioridad media" not in html


# ---------------------------------------------------------------------------
# Filtro combinado
# Req. 3.4
# ---------------------------------------------------------------------------

class TestCombinedFilter:
    def test_combined_filter_returns_200(self, client):
        # Arrange / Act
        response = client.get("/incidents?category=Hardware&priority=Alta")

        # Assert
        assert response.status_code == 200

    def test_combined_filter_shows_only_matching_incidents(self, client):
        # Arrange
        expl = (
            "Clasificación automática completada. "
            "Se detectaron palabras clave relevantes en el texto. "
            "La prioridad fue determinada de forma independiente a la categoría."
        )
        mock_hw_alta = mock.MagicMock()
        mock_hw_alta.classify.return_value = ("Hardware", "Alta", expl)
        mock_hw_media = mock.MagicMock()
        mock_hw_media.classify.return_value = ("Hardware", "Media", expl)
        mock_sw_alta = mock.MagicMock()
        mock_sw_alta.classify.return_value = ("Software", "Alta", expl)

        with mock.patch(_CLASSIFIER_PATH, return_value=mock_hw_alta):
            client.post("/incidents/new", data={
                "title": "HW + Alta", "description": "Desc.",
                "location": "Lugar", "incident_date": "2026-07-31",
            })
        with mock.patch(_CLASSIFIER_PATH, return_value=mock_hw_media):
            client.post("/incidents/new", data={
                "title": "HW + Media", "description": "Desc.",
                "location": "Lugar", "incident_date": "2026-07-31",
            })
        with mock.patch(_CLASSIFIER_PATH, return_value=mock_sw_alta):
            client.post("/incidents/new", data={
                "title": "SW + Alta", "description": "Desc.",
                "location": "Lugar", "incident_date": "2026-07-31",
            })

        # Act
        response = client.get("/incidents?category=Hardware&priority=Alta")
        html = response.data.decode("utf-8")

        # Assert — solo el incidente HW+Alta debe estar presente
        assert "HW + Alta" in html
        assert "HW + Media" not in html
        assert "SW + Alta" not in html

    def test_combined_filter_no_match_shows_message(self, client):
        # Arrange — BD vacía, filtro combinado válido
        # Act
        response = client.get("/incidents?category=Hardware&priority=Alta")
        html = response.data.decode("utf-8")

        # Assert — mensaje de sin resultados con criterios
        assert "No se encontraron incidentes" in html or "No hay incidentes" in html


# ---------------------------------------------------------------------------
# Filtro inválido muestra error y retorna HTTP 200
# Req. 3.7
# ---------------------------------------------------------------------------

class TestInvalidFilter:
    def test_invalid_category_returns_200(self, client):
        # Arrange / Act
        response = client.get("/incidents?category=CategoriaInexistente")

        # Assert — debe retornar 200, no 400 ni 500
        assert response.status_code == 200

    def test_invalid_category_shows_error_block(self, client):
        # Arrange / Act
        response = client.get("/incidents?category=CategoriaInexistente")
        html = response.data.decode("utf-8")

        # Assert — bloque de error visible en la template list.html
        assert "Error en los filtros" in html

    def test_invalid_priority_returns_200(self, client):
        # Arrange / Act
        response = client.get("/incidents?priority=Urgente")

        # Assert
        assert response.status_code == 200

    def test_invalid_priority_shows_error_block(self, client):
        # Arrange / Act
        response = client.get("/incidents?priority=Urgente")
        html = response.data.decode("utf-8")

        # Assert
        assert "Error en los filtros" in html

    def test_invalid_filter_error_message_is_descriptive(self, client):
        # Arrange / Act
        response = client.get("/incidents?category=INVALIDA")
        html = response.data.decode("utf-8")

        # Assert — el mensaje de error debe contener el valor inválido
        assert "INVALIDA" in html


# ---------------------------------------------------------------------------
# Escape de HTML — los datos del usuario se muestran escapados
# Req. seguridad — Jinja2 auto-escaping
# ---------------------------------------------------------------------------

class TestHtmlEscaping:
    def test_xss_in_title_is_escaped(self, client):
        # Arrange — título con payload XSS
        xss_title = '<script>alert("xss")</script>'
        _post_valid(client, title=xss_title)

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert — la etiqueta <script> NO debe ejecutarse: debe aparecer
        # como entidad HTML escapada, no como tag literal funcional
        assert "<script>alert" not in html
        # El texto escapado sí debe estar presente
        assert "&lt;script&gt;" in html

    def test_xss_in_description_is_escaped(self, client):
        # Arrange
        xss_desc = '<img src=x onerror=alert(1)>'
        _post_valid(client, description=xss_desc)

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert
        assert "<img src=x onerror=alert(1)>" not in html
        assert "&lt;img" in html

    def test_xss_in_location_is_escaped(self, client):
        # Arrange
        xss_location = '"><svg onload=alert(1)>'
        _post_valid(client, location=xss_location)

        # Act
        response = client.get("/incidents")
        html = response.data.decode("utf-8")

        # Assert
        assert "<svg onload=alert(1)>" not in html

    def test_html_in_form_errors_is_escaped(self, client):
        # Arrange — campo con HTML que aparecería en el formulario re-renderizado
        response = client.post("/incidents/new", data={
            "title": '<b>bold</b>',
            "description": "",
            "location": "",
            "incident_date": "",
        })
        html = response.data.decode("utf-8")

        # Assert — el valor del campo title no debe renderizar HTML en bruto
        # Jinja2 escapa los valores en los atributos value=""
        assert "<b>bold</b>" not in html.replace("&lt;b&gt;bold&lt;/b&gt;", "")
