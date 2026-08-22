"""Pruebas unitarias para RuleBasedIncidentClassifier.

Cubre los casos indicados en tasks.md (Tarea 2) y los criterios de
aceptación del Requisito 2 de requirements.md.

Patrón: AAA (Arrange, Act, Assert).
"""

import unittest.mock as mock

import pytest

from app.classifier.rule_based_incident_classifier import (
    RuleBasedIncidentClassifier,
    CATEGORY_RULES,
    PRIORITY_RULES,
)

# Conjunto de valores válidos (extraído de requirements.md / design.md)
VALID_CATEGORIES = {
    "Seguridad de la Información",
    "Seguridad Física",
    "Hardware",
    "Software",
    "Red/Conectividad",
    "Cuenta/Usuario",
    "Por revisar",
}
VALID_PRIORITIES = {"Baja", "Media", "Alta"}


@pytest.fixture
def classifier() -> RuleBasedIncidentClassifier:
    """Instancia limpia del clasificador para cada prueba."""
    return RuleBasedIncidentClassifier()


# ---------------------------------------------------------------------------
# test_classify_known_category
# Req. 2.1, 2.5 — palabra clave reconocida → categoría correcta
# ---------------------------------------------------------------------------

class TestClassifyKnownCategory:
    def test_phishing_maps_to_seguridad_informacion(self, classifier):
        # Arrange
        title = "Correo de phishing detectado"
        description = ""

        # Act
        category, priority, explanation = classifier.classify(title, description)

        # Assert
        assert category == "Seguridad de la Información"

    def test_ransomware_maps_to_seguridad_informacion(self, classifier):
        # Arrange — solo ransomware, sin palabras de otras categorías
        title = "Ransomware detectado en el sistema"
        description = "Se encontró cifrado malicioso en los archivos"

        # Act
        category, priority, explanation = classifier.classify(title, description)

        # Assert
        assert category == "Seguridad de la Información"

    def test_servidor_maps_to_hardware(self, classifier):
        # Arrange
        title = "Fallo en servidor de producción"
        description = "El servidor dejó de responder"

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Hardware"

    def test_vpn_maps_to_red_conectividad(self, classifier):
        # Arrange
        title = "Problemas con VPN corporativa"
        description = ""

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Red/Conectividad"

    def test_usuario_maps_to_cuenta_usuario(self, classifier):
        # Arrange
        title = "Cuenta de usuario bloqueada"
        description = "No se puede autenticar el usuario en el sistema"

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Cuenta/Usuario"

    def test_robo_maps_to_seguridad_fisica(self, classifier):
        # Arrange — "robo" sin "equipo" para evitar activar Hardware
        title = "Robo ocurrido en las instalaciones"
        description = ""

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Seguridad Física"

    def test_bug_maps_to_software(self, classifier):
        # Arrange
        title = "Bug crítico en el módulo de facturación"
        description = ""

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Software"


# ---------------------------------------------------------------------------
# test_classify_high_priority_keywords
# Req. 2.2 — palabras clave de alta urgencia → prioridad Alta
# ---------------------------------------------------------------------------

class TestClassifyHighPriorityKeywords:
    def test_ransomware_yields_alta_priority(self, classifier):
        # Arrange
        title = "Ransomware detectado"
        description = ""

        # Act
        _category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert priority == "Alta"

    def test_servicio_caido_yields_alta_priority(self, classifier):
        # Arrange — "bug" provee categoría inequívoca (Software); "servicio caido"
        # activa prioridad Alta de forma independiente
        title = "Bug crítico con servicio caido en producción"
        description = ""

        # Act
        _category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert priority == "Alta"

    def test_fuga_de_datos_yields_alta_priority(self, classifier):
        # Arrange
        title = "Fuga de datos detectada"
        description = ""

        # Act
        _category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert priority == "Alta"

    def test_intrusion_yields_alta_priority(self, classifier):
        # Arrange
        title = "Intrusión física en sala de servidores"
        description = ""

        # Act
        _category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert priority == "Alta"


# ---------------------------------------------------------------------------
# test_classify_no_keywords
# Req. 2.6 — sin palabras clave → Por revisar / Media / explicación manual
# ---------------------------------------------------------------------------

class TestClassifyNoKeywords:
    def test_empty_strings_return_por_revisar(self, classifier):
        # Arrange
        title = ""
        description = ""

        # Act
        category, priority, explanation = classifier.classify(title, description)

        # Assert
        assert category == "Por revisar"
        assert priority == "Media"
        assert explanation  # no vacía

    def test_unrecognized_text_returns_por_revisar(self, classifier):
        # Arrange
        title = "Algo extraño pasó ayer"
        description = "No sabemos qué fue exactamente"

        # Act
        category, priority, explanation = classifier.classify(title, description)

        # Assert
        assert category == "Por revisar"
        assert priority == "Media"

    def test_no_keywords_explanation_mentions_manual_review(self, classifier):
        # Arrange
        title = "Situación desconocida"
        description = "Sin detalles adicionales"

        # Act
        _category, _priority, explanation = classifier.classify(title, description)

        # Assert — la explicación debe mencionar revisión manual
        lower = explanation.lower()
        assert "revisión" in lower or "revision" in lower or "manual" in lower

    def test_no_keywords_explanation_word_count_in_range(self, classifier):
        # Arrange
        title = ""
        description = ""

        # Act
        _category, _priority, explanation = classifier.classify(title, description)

        # Assert — entre 10 y 100 palabras (Req. 2.3)
        word_count = len(explanation.split())
        assert 10 <= word_count <= 100, (
            f"Explicación fuera de rango: {word_count} palabras → '{explanation}'"
        )


# ---------------------------------------------------------------------------
# test_classify_tie_returns_review
# Req. 2.8 — empate entre categorías → Por revisar / Media / explica ambigüedad
# ---------------------------------------------------------------------------

class TestClassifyTieReturnsReview:
    def test_tie_between_two_categories_returns_por_revisar(self, classifier):
        """Fuerza un empate entre Seguridad de la Información y Red/Conectividad
        usando exactamente una palabra clave de cada categoría."""
        # Arrange — "phishing" (Seg. Info.) y "vpn" (Red/Conectividad): 1-1
        title = "phishing detectado en vpn"
        description = ""

        # Act
        category, priority, explanation = classifier.classify(title, description)

        # Assert
        assert category == "Por revisar"
        assert priority == "Media"

    def test_tie_explanation_mentions_ambiguity(self, classifier):
        # Arrange
        title = "phishing detectado en vpn"
        description = ""

        # Act
        _category, _priority, explanation = classifier.classify(title, description)

        # Assert
        lower = explanation.lower()
        assert "ambig" in lower or "empate" in lower or "categorías" in lower or "categorias" in lower

    def test_tie_explanation_word_count_in_range(self, classifier):
        # Arrange
        title = "phishing detectado en vpn"
        description = ""

        # Act
        _category, _priority, explanation = classifier.classify(title, description)

        # Assert
        word_count = len(explanation.split())
        assert 10 <= word_count <= 100, (
            f"Explicación fuera de rango: {word_count} palabras → '{explanation}'"
        )


# ---------------------------------------------------------------------------
# test_keyword_boundary_no_false_match
# Req. 2.5 — límites de palabra: "ip" no coincide dentro de "equipo"
# ---------------------------------------------------------------------------

class TestKeywordBoundaryNoFalseMatch:
    def test_ip_not_matched_inside_equipo(self, classifier):
        """'equipo' no debe activar la clave 'ip' de Red/Conectividad."""
        # Arrange
        title = "revisión de equipo de cómputo"
        description = ""

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert — no debe clasificar como Red/Conectividad por falso positivo
        assert category != "Red/Conectividad", (
            "La clave 'ip' no debe coincidir dentro de 'equipo'"
        )

    def test_ip_not_matched_inside_equipo_de_computo(self, classifier):
        """Versión sin tilde — misma garantía."""
        # Arrange
        title = "equipo de computo sin conexion"
        description = "el equipo no enciende"

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert — Red/Conectividad no debe ganar solo por "ip" dentro de "equipo"
        # ("sin conexion" no es una clave exacta, "conectividad" sí lo es)
        # En este caso no hay clave de red válida → Por revisar o Hardware
        assert category != "Red/Conectividad"

    def test_ip_alone_does_match_red_conectividad(self, classifier):
        """La clave 'ip' como palabra completa sí debe coincidir."""
        # Arrange
        title = "conflicto de IP en la red"
        description = ""

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Red/Conectividad"

    def test_aplicacion_not_matched_inside_aplicaciones(self, classifier):
        """'aplicacion' no debe coincidir como subcadena de 'aplicaciones'.
        Con \\b, 'aplicacion\\b' no coincide dentro de 'aplicaciones' porque
        la 'e' siguiente no es un límite de palabra.
        Para esta entrada no hay ninguna clave exacta de categoría → Por revisar."""
        # Arrange
        title = "revisión de las aplicaciones instaladas"
        description = ""

        # Act
        result1 = classifier.classify(title, description)
        result2 = classifier.classify(title, description)
        category = result1[0]

        # Assert — reproducible y sin falso positivo de Software
        assert result1 == result2, "El clasificador debe ser reproducible"
        assert category == "Por revisar", (
            "'aplicaciones' no debe activar la clave exacta 'aplicacion'"
        )


# ---------------------------------------------------------------------------
# test_priority_independent_of_category
# Req. 2.2 — prioridad determinada de forma independiente a la categoría
# ---------------------------------------------------------------------------

class TestPriorityIndependentOfCategory:
    def test_hardware_incident_with_servicio_caido_yields_alta(self, classifier):
        """Incidente de Hardware cuya descripción contiene 'servicio caído'
        debe obtener prioridad Alta aunque la categoría sea Hardware."""
        # Arrange
        title = "Fallo en servidor central"
        description = "Servicio caído, todos los usuarios afectados"

        # Act
        category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Hardware"
        assert priority == "Alta"

    def test_software_incident_with_lentitud_yields_media(self, classifier):
        """Incidente de Software con 'lentitud' debe obtener prioridad Media."""
        # Arrange
        title = "Bug en la aplicación de reportes"
        description = "lentitud al generar los reportes mensuales"

        # Act
        category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Software"
        assert priority == "Media"

    def test_hardware_incident_no_priority_kw_yields_media_default(self, classifier):
        """Incidente de Hardware sin palabras clave de prioridad → Media por defecto."""
        # Arrange
        title = "Pantalla con píxeles dañados"
        description = "La pantalla del equipo tiene píxeles muertos en la esquina"

        # Act
        category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Hardware"
        assert priority == "Media"

    def test_red_incident_with_consulta_yields_baja(self, classifier):
        """Incidente de Red con 'consulta' debe obtener prioridad Baja."""
        # Arrange
        title = "Consulta sobre configuración de router"
        description = "Solicitud de información sobre la ip del router"

        # Act
        category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Red/Conectividad"
        assert priority == "Baja"

    def test_priority_alta_overrides_baja_when_both_present(self, classifier):
        """Si el texto contiene claves de Alta y Baja, debe ganar Alta."""
        # Arrange
        title = "Consulta urgente: ransomware detectado"
        description = ""

        # Act
        _category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert priority == "Alta"


# ---------------------------------------------------------------------------
# test_explanation_not_empty
# Req. 2.3 — la explicación nunca es cadena vacía, siempre 10-100 palabras
# ---------------------------------------------------------------------------

class TestExplanationNotEmpty:
    @pytest.mark.parametrize("title,description", [
        ("phishing detectado", ""),
        ("ransomware en servidor", "acceso no autorizado"),
        ("", ""),
        ("texto sin keywords", "descripción cualquiera"),
        ("phishing vpn", ""),          # caso de empate
        ("Pantalla rota", "La pantalla del equipo no enciende"),
    ])
    def test_explanation_is_never_empty(self, classifier, title, description):
        # Act
        _category, _priority, explanation = classifier.classify(title, description)

        # Assert
        assert isinstance(explanation, str)
        assert len(explanation.strip()) > 0

    @pytest.mark.parametrize("title,description", [
        ("phishing detectado", ""),
        ("ransomware en servidor", "acceso no autorizado"),
        ("", ""),
        ("texto sin keywords", "descripción cualquiera"),
        ("phishing vpn", ""),
        ("Pantalla rota", "La pantalla del equipo no enciende"),
    ])
    def test_explanation_word_count_between_10_and_100(self, classifier, title, description):
        # Act
        _category, _priority, explanation = classifier.classify(title, description)

        # Assert
        word_count = len(explanation.split())
        assert 10 <= word_count <= 100, (
            f"Explicación fuera de rango ({word_count} palabras) para "
            f"title='{title}', desc='{description}': '{explanation}'"
        )


# ---------------------------------------------------------------------------
# Normalización de tildes y mayúsculas
# Req. 2.2 (normalización) — misma clave con/sin tilde y en mayúsculas
# ---------------------------------------------------------------------------

class TestNormalization:
    def test_uppercase_title_classified_correctly(self, classifier):
        """Título en mayúsculas debe clasificarse igual que en minúsculas."""
        # Arrange
        title_lower = "phishing detectado en correo"
        title_upper = "PHISHING DETECTADO EN CORREO"

        # Act
        cat_lower, pri_lower, _exp = classifier.classify(title_lower, "")
        cat_upper, pri_upper, _exp = classifier.classify(title_upper, "")

        # Assert
        assert cat_lower == cat_upper
        assert pri_lower == pri_upper

    def test_accented_keyword_matches(self, classifier):
        """'contraseña' (con tilde) debe coincidir con la clave 'contrasena'."""
        # Arrange — sin "robo" para evitar activar Seguridad Física y producir empate
        title = "Contraseña de administrador comprometida"
        description = ""

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Seguridad de la Información"

    def test_mixed_case_and_accents(self, classifier):
        """Combinación de mayúsculas y tildes debe normalizarse correctamente."""
        # Arrange — sin "red" ni "vpn" para evitar empate con Red/Conectividad
        title = "PHÍSHING detectado en correo corporativo"
        description = ""

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Seguridad de la Información"

    def test_keyword_with_accent_in_description(self, classifier):
        """'autenticación' (con tilde) en descripción debe activar Cuenta/Usuario."""
        # Arrange
        title = "Fallo de inicio de sesión"
        description = "Error en autenticación de usuarios del directorio activo"

        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category == "Cuenta/Usuario"

    def test_same_input_always_same_output(self, classifier):
        """La clasificación es reproducible: misma entrada → misma salida."""
        # Arrange
        title = "ransomware detectado en servidor"
        description = "acceso no autorizado al sistema"

        # Act
        result_1 = classifier.classify(title, description)
        result_2 = classifier.classify(title, description)
        result_3 = classifier.classify(title, description)

        # Assert
        assert result_1 == result_2 == result_3


# ---------------------------------------------------------------------------
# Manejo de error interno
# Req. 2.7 — si el clasificador lanza excepción interna → fallback sin propagar
# ---------------------------------------------------------------------------

class TestInternalErrorHandling:
    def test_internal_exception_returns_por_revisar(self, classifier):
        """Si _classify_internal lanza una excepción, classify() retorna fallback."""
        # Arrange — parchear el método interno para simular fallo inesperado
        with mock.patch.object(
            classifier, "_classify_internal", side_effect=RuntimeError("fallo simulado")
        ):
            # Act
            category, priority, explanation = classifier.classify("cualquier texto", "")

        # Assert
        assert category == "Por revisar"
        assert priority == "Media"
        assert isinstance(explanation, str)
        assert len(explanation.strip()) > 0

    def test_internal_exception_explanation_not_empty(self, classifier):
        """La explicación de fallback tiene entre 10 y 100 palabras."""
        # Arrange
        with mock.patch.object(
            classifier, "_classify_internal", side_effect=Exception("error interno")
        ):
            # Act
            _category, _priority, explanation = classifier.classify("texto", "desc")

        # Assert
        word_count = len(explanation.split())
        assert 10 <= word_count <= 100, (
            f"Explicación de error fuera de rango: {word_count} palabras → '{explanation}'"
        )

    def test_internal_exception_does_not_propagate(self, classifier):
        """classify() nunca debe propagar excepciones al llamador."""
        # Arrange
        with mock.patch.object(
            classifier, "_classify_internal", side_effect=ValueError("algo raro")
        ):
            # Act & Assert — no debe lanzar excepción
            try:
                result = classifier.classify("texto", "desc")
            except Exception as exc:
                pytest.fail(f"classify() propagó una excepción inesperada: {exc}")

            assert isinstance(result, tuple)
            assert len(result) == 3


# ---------------------------------------------------------------------------
# Invariante: la salida siempre tiene valores del conjunto válido (Req. 2.1/2.2)
# ---------------------------------------------------------------------------

class TestOutputAlwaysValid:
    @pytest.mark.parametrize("title,description", [
        ("phishing en correo electrónico", ""),
        ("ransomware", "acceso no autorizado"),
        ("fallo de pantalla", "la pantalla no enciende"),
        ("bug en la aplicación", "crash al abrir el programa"),
        ("problemas de red", "latencia muy alta en vpn"),
        ("usuario bloqueado", "no puede iniciar sesión"),
        ("robo de equipo", "intrusión física"),
        ("", ""),
        ("xyzzy gibberish texto sin sentido", "nada relevante aquí"),
        ("phishing vpn", ""),   # empate → Por revisar
    ])
    def test_category_always_in_valid_set(self, classifier, title, description):
        # Act
        category, _priority, _explanation = classifier.classify(title, description)

        # Assert
        assert category in VALID_CATEGORIES, (
            f"Categoría inválida '{category}' para title='{title}'"
        )

    @pytest.mark.parametrize("title,description", [
        ("phishing en correo electrónico", ""),
        ("ransomware", "acceso no autorizado"),
        ("fallo de pantalla", "la pantalla no enciende"),
        ("bug en la aplicación", "crash al abrir el programa"),
        ("problemas de red", "latencia muy alta en vpn"),
        ("usuario bloqueado", "no puede iniciar sesión"),
        ("robo de equipo", "intrusión física"),
        ("", ""),
        ("xyzzy gibberish texto sin sentido", "nada relevante aquí"),
        ("phishing vpn", ""),
    ])
    def test_priority_always_in_valid_set(self, classifier, title, description):
        # Act
        _category, priority, _explanation = classifier.classify(title, description)

        # Assert
        assert priority in VALID_PRIORITIES, (
            f"Prioridad inválida '{priority}' para title='{title}'"
        )

    @pytest.mark.parametrize("title,description", [
        ("phishing en correo electrónico", ""),
        ("ransomware", "acceso no autorizado"),
        ("", ""),
    ])
    def test_result_is_three_element_tuple(self, classifier, title, description):
        # Act
        result = classifier.classify(title, description)

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(isinstance(e, str) for e in result)
