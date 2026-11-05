from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ODentalSpecialty(models.Model):
    _name = "odental.specialty"
    _description = "Especialidad o área de práctica clínica"
    _order = "name"

    name = fields.Char(string="Especialidad o área de práctica", required=True, index=True)
    active = fields.Boolean(string="Activa", default=True)
    company_id = fields.Many2one(
        "res.company", string="Compañía",
        default=lambda self: self.env.company, index=True,
        help="Vacío para una especialidad estándar disponible en todas las clínicas.",
    )

    @api.constrains("name", "company_id")
    def _check_unique_name(self):
        for specialty in self:
            normalized = (specialty.name or "").strip().casefold()
            if not normalized:
                raise ValidationError(_("Indique el nombre de la especialidad."))
            candidates = self.with_context(active_test=False).search([
                ("id", "!=", specialty.id),
                ("company_id", "=", specialty.company_id.id or False),
            ])
            if any((item.name or "").strip().casefold() == normalized for item in candidates):
                raise ValidationError(_("Ya existe esta especialidad en el catálogo."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get("company_id", self.env.company.id)
            if not company_id and not (self.env.is_superuser() or self.env.user.has_group("odental_core.group_odental_admin")):
                raise AccessError(_("Solo el administrador O Dental puede crear especialidades globales."))
            if company_id and company_id not in self.env.companies.ids:
                raise AccessError(_("Seleccione una compañía autorizada."))
        return super().create(vals_list)

    def write(self, vals):
        if "company_id" in vals:
            raise AccessError(_("No se puede trasladar una especialidad entre compañías."))
        if not (self.env.is_superuser() or self.env.user.has_group("odental_core.group_odental_admin")):
            if any(not item.company_id for item in self):
                raise AccessError(_("Las especialidades estándar son de solo lectura."))
        return super().write(vals)

    def unlink(self):
        if self.env["odental.professional"].sudo().search_count([
            ("specialty_ids", "in", self.ids)
        ]):
            raise ValidationError(_("Archive la especialidad; ya está asignada a un profesional."))
        if not (self.env.is_superuser() or self.env.user.has_group("odental_core.group_odental_admin")):
            if any(not item.company_id for item in self):
                raise AccessError(_("Las especialidades estándar no se pueden eliminar."))
        return super().unlink()
