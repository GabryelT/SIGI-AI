"""Rutas del blueprint de incidentes.

Responsabilidad exclusiva: recibir la solicitud HTTP, delegar en
IncidentService y renderizar la respuesta. Sin lógica de negocio.
"""

from flask import redirect, render_template, request, url_for

from app.blueprints.incidents import incidents_bp
from app.services.incident_service import IncidentService


@incidents_bp.route("/")
def index():
    """Redirige la raíz al listado de incidentes."""
    return redirect(url_for("incidents.list_incidents"))


@incidents_bp.route("/incidents")
def list_incidents():
    """Muestra el listado de incidentes con filtros opcionales."""
    # Convertir cadenas vacías a None antes de enviar al servicio
    category = request.args.get("category", "").strip() or None
    priority = request.args.get("priority", "").strip() or None

    service = IncidentService()
    result = service.get_incidents(category=category, priority=priority)

    return render_template(
        "incidents/list.html",
        incidents=result.get("incidents", []),
        message=result.get("message"),
        error=result.get("error"),
        selected_category=category,
        selected_priority=priority,
    )


@incidents_bp.route("/incidents/new", methods=["GET"])
def new_incident_form():
    """Muestra el formulario vacío de registro de incidentes."""
    return render_template("incidents/register.html")


@incidents_bp.route("/incidents/new", methods=["POST"])
def create_incident():
    """Recibe el formulario, delega en el servicio y muestra el resultado.

    Si el registro es exitoso muestra confirmación con el ID generado.
    Si hay errores de validación re-renderiza el formulario conservando
    los valores ingresados por el usuario.
    """
    form_data = request.form.to_dict(flat=True)

    service = IncidentService()
    result = service.register_incident(form_data)

    if result.get("success"):
        return render_template(
            "incidents/register.html",
            incident_id=result["id"],
        )

    return render_template(
        "incidents/register.html",
        errors=result.get("errors", []),
        form_data=form_data,
    )
