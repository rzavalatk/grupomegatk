from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


_PERIOD_TRANSITION_TOKEN = object()
_ROTATION_TRANSITION_TOKEN = object()


class ODentalAcademicProgram(models.Model):
    _name = "odental.academic.program"
    _description = "Programa académico O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "organization_id, name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, index=True, tracking=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True, tracking=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    active = fields.Boolean(default=True)
    coordinator_user_id = fields.Many2one("res.users", string="Coordinador", tracking=True)
    period_ids = fields.One2many("odental.academic.period", "program_id", string="Períodos")
    notes = fields.Text()

    _sql_constraints = [
        (
            "academic_program_code_unique",
            "unique(organization_id, code)",
            "El código del programa debe ser único dentro de la institución.",
        )
    ]

    @api.constrains("organization_id")
    def _check_institution_type(self):
        for program in self:
            if program.organization_id.organization_type not in {"university", "institution"}:
                raise ValidationError(
                    "Los programas académicos solo pueden pertenecer a una universidad o institución."
                )


class ODentalAcademicPeriod(models.Model):
    _name = "odental.academic.period"
    _description = "Período académico O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(required=True, tracking=True)
    program_id = fields.Many2one(
        "odental.academic.program", required=True, ondelete="restrict", index=True
    )
    organization_id = fields.Many2one(
        related="program_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    date_start = fields.Date(required=True, tracking=True)
    date_end = fields.Date(required=True, tracking=True)
    rotation_ids = fields.One2many("odental.academic.rotation", "period_id", string="Rotaciones")
    state = fields.Selection(
        [("draft", "Borrador"), ("active", "Activo"), ("closed", "Cerrado")],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for period in self:
            if period.date_end < period.date_start:
                raise ValidationError("La fecha final no puede ser anterior a la fecha inicial.")

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            values["state"] = "draft"
        return super().create(vals_list)

    def write(self, vals):
        if (
            "state" in vals
            and self.env.context.get("odental_academic_period_transition")
            is not _PERIOD_TRANSITION_TOKEN
        ):
            raise UserError("Utilice las acciones controladas del período académico.")
        return super().write(vals)

    def _transition(self, values):
        return self.with_context(
            odental_academic_period_transition=_PERIOD_TRANSITION_TOKEN
        ).write(values)

    def action_activate(self):
        for period in self:
            if period.state != "draft":
                raise UserError("Solo un período en borrador puede activarse.")
            period._transition({"state": "active"})

    def action_close(self):
        for period in self:
            if period.state != "active":
                raise UserError("Solo un período activo puede cerrarse.")
            if period.rotation_ids.filtered(lambda rotation: rotation.state == "active"):
                raise ValidationError("Cierre primero las rotaciones activas del período.")
            period._transition({"state": "closed"})


class ODentalAcademicRotation(models.Model):
    _name = "odental.academic.rotation"
    _description = "Rotación clínica O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, name"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, index=True, tracking=True)
    period_id = fields.Many2one(
        "odental.academic.period", required=True, ondelete="restrict", index=True
    )
    program_id = fields.Many2one(related="period_id.program_id", store=True, index=True)
    organization_id = fields.Many2one(
        related="period_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    date_start = fields.Date(required=True, tracking=True)
    date_end = fields.Date(required=True, tracking=True)
    service_area = fields.Char(string="Área o servicio", tracking=True)
    student_user_ids = fields.Many2many(
        "res.users",
        "odental_academic_rotation_student_rel",
        "rotation_id",
        "user_id",
        string="Estudiantes",
    )
    supervisor_user_ids = fields.Many2many(
        "res.users",
        "odental_academic_rotation_supervisor_rel",
        "rotation_id",
        "user_id",
        string="Docentes supervisores",
    )
    case_ids = fields.One2many("odental.academic.case", "rotation_id", string="Casos")
    state = fields.Selection(
        [("draft", "Borrador"), ("active", "Activa"), ("closed", "Cerrada")],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    _sql_constraints = [
        (
            "academic_rotation_code_unique",
            "unique(period_id, code)",
            "El código de la rotación debe ser único dentro del período.",
        )
    ]

    @api.constrains("date_start", "date_end", "period_id")
    def _check_dates(self):
        for rotation in self:
            if rotation.date_end < rotation.date_start:
                raise ValidationError("La fecha final no puede ser anterior a la fecha inicial.")
            if (
                rotation.date_start < rotation.period_id.date_start
                or rotation.date_end > rotation.period_id.date_end
            ):
                raise ValidationError("La rotación debe estar contenida dentro del período académico.")

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            values["state"] = "draft"
        return super().create(vals_list)

    def write(self, vals):
        if (
            "state" in vals
            and self.env.context.get("odental_academic_rotation_transition")
            is not _ROTATION_TRANSITION_TOKEN
        ):
            raise UserError("Utilice las acciones controladas de la rotación.")
        return super().write(vals)

    def _transition(self, values):
        return self.with_context(
            odental_academic_rotation_transition=_ROTATION_TRANSITION_TOKEN
        ).write(values)

    @api.constrains("student_user_ids", "supervisor_user_ids")
    def _check_participants(self):
        student_group = self.env.ref("odental_academic.group_odental_academic_student")
        supervisor_group = self.env.ref("odental_academic.group_odental_academic_supervisor")
        for rotation in self:
            if any(student_group not in user.groups_id for user in rotation.student_user_ids):
                raise ValidationError("Todos los estudiantes deben tener el perfil académico aislado.")
            if any(
                supervisor_group not in user.groups_id
                for user in rotation.supervisor_user_ids
            ):
                raise ValidationError("Todos los supervisores deben tener el perfil docente.")

    def action_activate(self):
        for rotation in self:
            if rotation.state != "draft" or rotation.period_id.state != "active":
                raise UserError("Active primero el período y mantenga la rotación en borrador.")
            if not rotation.student_user_ids or not rotation.supervisor_user_ids:
                raise ValidationError("Asigne al menos un estudiante y un supervisor.")
            rotation._transition({"state": "active"})

    def action_close(self):
        for rotation in self:
            if rotation.state != "active":
                raise UserError("Solo una rotación activa puede cerrarse.")
            pending = rotation.case_ids.filtered(
                lambda case: case.state == "active"
                or case.submission_ids.filtered(
                    lambda item: item.state in {"submitted", "approved"}
                )
            )
            if pending:
                raise ValidationError("Finalice los casos y revisiones pendientes antes de cerrar.")
            rotation._transition({"state": "closed"})
