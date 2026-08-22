"""Rutas del blueprint de incidentes.

Responsabilidad exclusiva: recibir la solicitud HTTP, delegar en
IncidentService y renderizar la respuesta. Sin lógica de negocio.
"""

from flask import render_template, request

from app.blueprints.incidents import incidents_bp
from app.services.incident_service import IncidentService


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
