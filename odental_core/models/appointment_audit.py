from odoo import fields, models


class ODentalAppointmentAudit(models.Model):
    _name = "odental.appointment.audit"
    _description = "Historial de cambios de agenda O Dental"
    _order = "changed_at desc, id desc"

    appointment_id = fields.Many2one(
        "odental.appointment", string="Cita", ondelete="set null", readonly=True, index=True
    )
    appointment_reference = fields.Char(string="Referencia de cita", required=True, readonly=True)
    organization_id = fields.Many2one(
        "odental.organization", string="Organización", required=True,
        ondelete="restrict", readonly=True, index=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía", required=True, readonly=True, index=True
    )
    professional_id = fields.Many2one(
        "odental.professional", string="Profesional", ondelete="set null", readonly=True
    )
    actor_user_id = fields.Many2one(
        "res.users", string="Modificado por", ondelete="set null", readonly=True
    )
    source = fields.Selection(
        [("odoo", "O Dental"), ("todoist", "Todoist")],
        string="Origen", required=True, readonly=True,
    )
    event = fields.Selection(
        [("created", "Creación"), ("changed", "Cambio"),
         ("cancelled", "Cancelación"), ("deleted", "Eliminación")],
        string="Acción", required=True, readonly=True,
    )
    changed_at = fields.Datetime(string="Fecha y hora", required=True, readonly=True)
    old_values = fields.Json(string="Valores anteriores", readonly=True)
    new_values = fields.Json(string="Valores nuevos", readonly=True)
