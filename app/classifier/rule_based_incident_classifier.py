"""Clasificador determinista de incidentes basado en reglas y palabras clave.

Implementa el Sistema_Experto del diseño: asigna categoría, prioridad y
explicación de forma reproducible a partir del título y la descripción
de un incidente.
"""

import re
import unicodedata


# ---------------------------------------------------------------------------
# Reglas de categorización
# ---------------------------------------------------------------------------

CATEGORY_RULES: dict[str, list[str]] = {
    "Seguridad de la Información": [
        "contrasena",
        "cifrado",
        "phishing",
        "malware",
        "acceso no autorizado",
        "fuga de datos",
        "ransomware",
        "vulnerabilidad",
        "credenciales",
        "brecha",
    ],
    "Seguridad Física": [
        "acceso fisico",
        "intrusion",
        "robo",
        "camara",
        "vigilancia",
        "instalacion",
        "cerradura",
        "perimetro",
        "guardia",
    ],
    "Hardware": [
        "disco duro",
        "memoria ram",
        "servidor",
        "impresora",
        "pantalla",
        "teclado",
        "fuente de poder",
        "componente",
        "dispositivo fisico",
    ],
    "Software": [
        "aplicacion",
        "error de software",
        "actualizacion",
        "parche",
        "instalacion de software",
        "fallo del sistema",
        "bug",
        "crash",
        "programa",
    ],
    "Red/Conectividad": [
        "red",
        "internet",
        "vpn",
        "firewall",
        "latencia",
        "ancho de banda",
        "switch",
        "router",
        "conectividad",
        "ip",
    ],
    "Cuenta/Usuario": [
        "usuario",
        "cuenta",
        "bloqueo de cuenta",
        "acceso denegado",
        "permiso",
        "rol",
        "sesion",
        "autenticacion",
        "directorio activo",
    ],
}

# ---------------------------------------------------------------------------
# Reglas de prioridad
# ---------------------------------------------------------------------------

PRIORITY_RULES: dict[str, list[str]] = {
    "Alta": [
        "malware",
        "ransomware",
        "phishing",
        "acceso no autorizado",
        "fuga de datos",
        "intrusion",
        "robo",
        "incendio",
        "servicio caido",
        "interrupcion total",
        "sistema critico",
    ],
    "Media": [
        "afectacion parcial",
        "degradacion",
        "bloqueo",
        "funcionamiento intermitente",
        "lentitud",
        "error intermitente",
        "acceso limitado",
        "servicio degradado",
    ],
    "Baja": [
        "consulta",
        "solicitud",
        "revision menor",
        "ajuste",
        "mejora menor",
        "afectacion menor",
        "informativo",
    ],
}

# Orden de precedencia para resolución de prioridad (mayor impacto primero)
_PRIORITY_ORDER: list[str] = ["Alta", "Media", "Baja"]


def _normalize(text: str) -> str:
    """Convierte a minúsculas y elimina acentos/diacríticos.

    Aplica NFD (descomposición canónica) para separar la letra base del
    diacrítico y luego filtra los caracteres de categoría Unicode 'Mn'
    (marcas de combinación no espaciadas).
    """
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def _build_pattern(keyword: str) -> re.Pattern:
    """Compila una expresión regular de límite de palabra para una clave.

    Para frases de múltiples tokens (p. ej. "acceso no autorizado") se usan
    límites de palabra al inicio y al final del grupo completo, de modo que
    la frase no pueda aparecer como subcadena de otra palabra.
    """
    escaped = re.escape(keyword)
    return re.compile(r"\b" + escaped + r"\b")


class RuleBasedIncidentClassifier:
    """Clasificador determinista basado en reglas y palabras clave.

    La misma entrada siempre produce la misma salida (reproducible).

    Uso::

        classifier = RuleBasedIncidentClassifier()
        category, priority, explanation = classifier.classify(title, description)
    """

    def __init__(self) -> None:
        # Pre-normalizar palabras clave y compilar patrones en tiempo de
        # inicialización para evitar trabajo redundante en cada llamada.
        self._category_patterns: dict[str, list[tuple[str, re.Pattern]]] = {
            category: [
                (_normalize(kw), _build_pattern(_normalize(kw)))
                for kw in keywords
            ]
            for category, keywords in CATEGORY_RULES.items()
        }

        self._priority_patterns: dict[str, list[tuple[str, re.Pattern]]] = {
            level: [
                (_normalize(kw), _build_pattern(_normalize(kw)))
                for kw in keywords
            ]
            for level, keywords in PRIORITY_RULES.items()
        }

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------

    def classify(self, title: str, description: str) -> tuple[str, str, str]:
        """Clasifica un incidente y retorna (categoría, prioridad, explicación).

        Args:
            title: Título del incidente.
            description: Descripción del incidente.

        Returns:
            Tupla ``(category, priority, explanation)`` con valores del conjunto
            válido definido en requirements.md.  Nunca lanza excepción: si
            ocurre un error interno inesperado, retorna los valores de fallback.
        """
        try:
            return self._classify_internal(title, description)
        except Exception:
            explanation = (
                "La clasificación automática no estuvo disponible debido a un "
                "error interno. Se asigna la categoría Por revisar con prioridad "
                "Media. Se requiere revisión manual por parte del Oficial de "
                "Seguridad para determinar la categoría y prioridad correctas."
            )
            return ("Por revisar", "Media", explanation)

    # ------------------------------------------------------------------
    # Implementación interna
    # ------------------------------------------------------------------

    def _classify_internal(self, title: str, description: str) -> tuple[str, str, str]:
        """Lógica principal del clasificador (puede lanzar excepciones)."""
        text = _normalize(f"{title} {description}")

        # ----------------------------------------------------------------
        # Paso 1: determinar categoría
        # ----------------------------------------------------------------
        category_scores: dict[str, int] = {}
        category_matched_kws: dict[str, list[str]] = {}

        for category, kw_patterns in self._category_patterns.items():
            matched = [kw for kw, pattern in kw_patterns if pattern.search(text)]
            category_scores[category] = len(matched)
            category_matched_kws[category] = matched

        max_cat_score = max(category_scores.values())

        # Sin coincidencias → Por revisar
        if max_cat_score == 0:
            explanation = (
                "No se detectaron palabras clave reconocidas en el título ni en "
                "la descripción del incidente. No fue posible determinar la "
                "categoría de forma automática. Se requiere revisión manual por "
                "parte del Oficial de Seguridad."
            )
            return ("Por revisar", "Media", explanation)

        # Empate entre categorías → Por revisar
        top_categories = [
            cat for cat, score in category_scores.items() if score == max_cat_score
        ]
        if len(top_categories) > 1:
            names = ", ".join(top_categories)
            explanation = (
                f"Existe ambigüedad entre las categorías: {names}. "
                "Todas obtuvieron la misma cantidad de palabras clave coincidentes. "
                "No es posible determinar automáticamente la categoría correcta. "
                "Se requiere revisión manual por parte del Oficial de Seguridad."
            )
            return ("Por revisar", "Media", explanation)

        category = top_categories[0]
        matched_keywords = category_matched_kws[category]

        # ----------------------------------------------------------------
        # Paso 2: determinar prioridad de forma independiente
        # ----------------------------------------------------------------
        priority = self._determine_priority(text)

        # ----------------------------------------------------------------
        # Paso 3: generar explicación
        # ----------------------------------------------------------------
        kw_list = ", ".join(matched_keywords) if matched_keywords else "ninguna"
        explanation = (
            f"El incidente fue clasificado en la categoría {category} con "
            f"prioridad {priority}. "
            f"Palabras clave detectadas: {kw_list}. "
            "La prioridad fue determinada de forma independiente a partir del "
            "nivel de riesgo e impacto indicado en el texto del incidente."
        )
        return (category, priority, explanation)

    def _determine_priority(self, normalized_text: str) -> str:
        """Determina la prioridad aplicando mayor impacto (Alta > Media > Baja).

        Si no hay coincidencias en ningún nivel retorna 'Media' por defecto.
        """
        priority_scores: dict[str, int] = {
            level: sum(
                1 for _kw, pattern in kw_patterns
                if pattern.search(normalized_text)
            )
            for level, kw_patterns in self._priority_patterns.items()
        }

        # Aplicar regla de mayor impacto
        for level in _PRIORITY_ORDER:
            if priority_scores.get(level, 0) > 0:
                return level

        # Sin coincidencias → Media por defecto
        return "Media"
