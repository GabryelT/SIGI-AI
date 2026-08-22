# Requirements Document

## Introduction

SIGI-AI (Sistema Inteligente de Gestión de Incidentes) es una aplicación académica destinada a centralizar y estructurar el registro y la consulta de incidentes tecnológicos, de seguridad de la información y de seguridad física dentro de una organización.

El problema actual radica en que los incidentes se registran de forma dispersa, lo que dificulta su clasificación, priorización y consulta posterior. SIGI-AI resuelve esto mediante tres capacidades esenciales: registro estructurado de incidentes, clasificación automática basada en reglas y palabras clave, y consulta filtrada del historial.

El actor principal es el **Oficial de Seguridad de la Información**, quien es responsable de registrar, revisar y hacer seguimiento de los incidentes reportados en la organización.

Este documento cubre únicamente el alcance del MVP, compuesto por exactamente tres requisitos funcionales.

---

## Glossary

- **SIGI-AI**: Sistema Inteligente de Gestión de Incidentes. Sistema sujeto de los requisitos de este documento.
- **Sistema_Experto**: Módulo de clasificación automática basado en reglas y palabras clave, responsable de asignar categoría, prioridad y explicación a cada incidente registrado.
- **Oficial_de_Seguridad**: Actor principal del sistema. Usuario que registra y consulta incidentes.
- **Incidente**: Evento registrado con título, descripción, ubicación u origen, y fecha, que representa una anomalía tecnológica o de seguridad.
- **Categoría**: Clasificación temática del incidente. Valores válidos: `Seguridad de la Información`, `Seguridad Física`, `Hardware`, `Software`, `Red/Conectividad`, `Cuenta/Usuario`, `Por revisar`.
- **Prioridad**: Nivel de urgencia asignado al incidente. Valores válidos: `Baja`, `Media`, `Alta`.
- **Explicación_de_Clasificación**: Texto breve generado por el Sistema_Experto que describe el motivo por el cual se asignó la categoría y la prioridad correspondiente.
- **Campos_Obligatorios**: Título, descripción, ubicación u origen, y fecha del incidente.
- **Filtro**: Criterio de búsqueda aplicado sobre el listado de incidentes. Valores admitidos: categoría, prioridad, o ambos simultáneamente.

---

## Requirements

---

### Requisito 1: Registrar un incidente

**Historia de usuario:**
Como Oficial de Seguridad de la Información, quiero registrar un incidente proporcionando su título, descripción, ubicación u origen y fecha, para que quede almacenado de forma estructurada y pueda ser clasificado y consultado posteriormente.

**Prioridad:** Must Have

#### Criterios de aceptación

**Casos correctos (flujo exitoso):**

1. WHEN el Oficial_de_Seguridad envía un formulario de registro con todos los Campos_Obligatorios completos y válidos, THE SIGI-AI SHALL almacenar el incidente y retornar una confirmación de registro exitoso que incluya el identificador único asignado al incidente.

2. WHEN el Oficial_de_Seguridad registra un incidente con todos los Campos_Obligatorios, THE SIGI-AI SHALL invocar al Sistema_Experto para clasificar el incidente de forma inmediata, antes de retornar la confirmación al usuario.

3. WHEN el SIGI-AI almacena un incidente, THE SIGI-AI SHALL registrar la fecha y hora exacta de creación del registro de forma automática, independientemente del valor de fecha del incidente provisto por el Oficial_de_Seguridad.

**Casos de error (validación de campos obligatorios):**

4. IF el Oficial_de_Seguridad envía el formulario de registro con el campo título vacío o ausente, THEN THE SIGI-AI SHALL rechazar el registro y retornar un mensaje de error que indique que el título es obligatorio.

5. IF el Oficial_de_Seguridad envía el formulario de registro con el campo descripción vacío o ausente, THEN THE SIGI-AI SHALL rechazar el registro y retornar un mensaje de error que indique que la descripción es obligatoria.

6. IF el Oficial_de_Seguridad envía el formulario de registro con el campo ubicación u origen vacío o ausente, THEN THE SIGI-AI SHALL rechazar el registro y retornar un mensaje de error que indique que la ubicación u origen es obligatoria.

7. IF el Oficial_de_Seguridad envía el formulario de registro con el campo fecha vacío, ausente o con un formato no válido, THEN THE SIGI-AI SHALL rechazar el registro y retornar un mensaje de error que indique que la fecha es obligatoria y debe tener el formato AAAA-MM-DD.

8. IF el Oficial_de_Seguridad envía el formulario de registro con dos o más Campos_Obligatorios vacíos o ausentes, THEN THE SIGI-AI SHALL rechazar el registro y retornar la lista completa de mensajes de error correspondientes a todos los campos faltantes.

---

### Requisito 2: Clasificar automáticamente el incidente

**Historia de usuario:**
Como Oficial de Seguridad de la Información, quiero que el sistema clasifique automáticamente cada incidente registrado asignándole una categoría, una prioridad y una explicación breve, para reducir el tiempo de análisis manual y asegurar una priorización consistente.

**Prioridad:** Must Have

#### Criterios de aceptación

**Casos correctos (clasificación exitosa):**

1. WHEN el SIGI-AI invoca al Sistema_Experto con los datos de un incidente recién registrado, THE Sistema_Experto SHALL asignar exactamente una Categoría al incidente, cuyo valor debe pertenecer al conjunto: `Seguridad de la Información`, `Seguridad Física`, `Hardware`, `Software`, `Red/Conectividad`, `Cuenta/Usuario` o `Por revisar`.

2. WHEN el SIGI-AI invoca al Sistema_Experto con los datos de un incidente recién registrado, THE Sistema_Experto SHALL asignar exactamente una Prioridad al incidente, cuyo valor debe pertenecer al conjunto: `Baja`, `Media` o `Alta`.

3. WHEN el SIGI-AI invoca al Sistema_Experto con los datos de un incidente recién registrado, THE Sistema_Experto SHALL generar una Explicación_de_Clasificación en texto, de entre 10 y 100 palabras, que describa el motivo por el cual se asignó la categoría y la prioridad determinadas.

4. WHEN el Sistema_Experto completa la clasificación de un incidente, THE SIGI-AI SHALL almacenar la Categoría, la Prioridad y la Explicación_de_Clasificación como atributos del incidente correspondiente.

5. WHEN el título o la descripción del incidente contiene palabras clave asociadas a una regla del Sistema_Experto, THE Sistema_Experto SHALL aplicar la regla de mayor coincidencia para determinar la categoría resultante.

**Casos de error (incidente no clasificable o ambiguo):**

6. IF el título y la descripción del incidente no contienen palabras clave reconocidas por ninguna regla del Sistema_Experto, THEN THE Sistema_Experto SHALL asignar la categoría `Por revisar`, la prioridad `Media` y una Explicación_de_Clasificación que indique que no fue posible determinar la categoría de forma automática y que se requiere revisión manual del Oficial de Seguridad.

7. IF el Sistema_Experto produce un error interno durante la clasificación, THEN THE SIGI-AI SHALL conservar el incidente con categoría `Por revisar`, prioridad `Media` y una Explicación_de_Clasificación que indique que la clasificación automática no estuvo disponible, sin interrumpir el flujo de registro.

8. IF dos o más categorías obtienen la misma coincidencia máxima de palabras clave durante la clasificación, THEN THE Sistema_Experto SHALL asignar la categoría `Por revisar`, la prioridad `Media` y una Explicación_de_Clasificación que indique que existe ambigüedad entre las categorías empatadas y que se requiere revisión manual del Oficial de Seguridad.

---

### Requisito 3: Consultar los incidentes registrados

**Historia de usuario:**
Como Oficial de Seguridad de la Información, quiero consultar el listado de todos los incidentes registrados, ordenados del más reciente al más antiguo, y poder filtrarlos por categoría y/o prioridad, para localizar rápidamente los incidentes que requieren atención.

**Prioridad:** Must Have

#### Criterios de aceptación

**Casos correctos (consulta y filtrado):**

1. WHEN el Oficial_de_Seguridad solicita el listado de incidentes sin aplicar ningún Filtro, THE SIGI-AI SHALL retornar todos los incidentes almacenados ordenados por fecha de creación del registro de forma descendente (del más reciente al más antiguo).

2. WHEN el Oficial_de_Seguridad solicita el listado de incidentes aplicando un Filtro por Categoría, THE SIGI-AI SHALL retornar únicamente los incidentes cuya Categoría coincida exactamente con el valor del Filtro, ordenados por fecha de creación del registro de forma descendente.

3. WHEN el Oficial_de_Seguridad solicita el listado de incidentes aplicando un Filtro por Prioridad, THE SIGI-AI SHALL retornar únicamente los incidentes cuya Prioridad coincida exactamente con el valor del Filtro, ordenados por fecha de creación del registro de forma descendente.

4. WHEN el Oficial_de_Seguridad solicita el listado de incidentes aplicando simultáneamente un Filtro por Categoría y un Filtro por Prioridad, THE SIGI-AI SHALL retornar únicamente los incidentes que satisfagan ambas condiciones de forma simultánea, ordenados por fecha de creación del registro de forma descendente.

5. WHEN el SIGI-AI retorna el listado de incidentes, THE SIGI-AI SHALL incluir para cada incidente: identificador único, título, descripción, ubicación u origen, fecha del incidente, fecha de creación del registro, Categoría, Prioridad y Explicación_de_Clasificación.

**Casos de error (sin resultados o filtro inválido):**

6. IF el Oficial_de_Seguridad solicita el listado de incidentes y no existen incidentes almacenados, THEN THE SIGI-AI SHALL retornar una lista vacía acompañada de un mensaje que indique que no hay incidentes registrados.

7. IF el Oficial_de_Seguridad aplica un Filtro por Categoría o Prioridad con un valor que no pertenece al conjunto de valores válidos definido en el Glosario, THEN THE SIGI-AI SHALL rechazar la solicitud y retornar un mensaje de error que indique los valores de Filtro permitidos.

8. IF el Oficial_de_Seguridad aplica un Filtro válido y ningún incidente almacenado satisface las condiciones del Filtro, THEN THE SIGI-AI SHALL retornar una lista vacía acompañada de un mensaje que indique que no se encontraron incidentes con los criterios seleccionados.
