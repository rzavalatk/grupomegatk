from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


_CASE_TRANSITION_TOKEN = object()


class ODentalAcademicCase(models.Model):
    _name = "odental.academic.case"
    _description = "Caso clínico académico O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "access_start desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    rotation_id = fields.Many2one(
        "odental.academic.rotation", required=True, ondelete="restrict", index=True, tracking=True
    )
    period_id = fields.Many2one(related="rotation_id.period_id", store=True, index=True)
    program_id = fields.Many2one(related="rotation_id.program_id", store=True, index=True)
    organization_id = fields.Many2one(
        related="rotation_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, tracking=True
    )
    patient_display_name = fields.Char(
        related="patient_id.name", store=True, string="Paciente asignado"
    )
    patient_reference = fields.Char(
        related="patient_id.reference", store=True, string="Referencia del paciente"
    )
    student_user_id = fields.Many2one(
        "res.users", required=True, ondelete="restrict", index=True, tracking=True
    )
    student_number = fields.Char(string="Número de estudiante", tracking=True)
    supervisor_user_id = fields.Many2one(
        "res.users", required=True, ondelete="restrict", index=True, tracking=True
    )
    supervisor_professional_id = fields.Many2one(
        "odental.professional", required=True, ondelete="restrict", tracking=True
    )
    access_start = fields.Date(required=True, tracking=True)
    access_end = fields.Date(required=True, tracking=True, index=True)
    reason_for_care = fields.Text(string="Motivo y alcance asignado")
    relevant_alerts = fields.Text(
        string="Alertas necesarias para esta atención",
        help="Incluya solo información clínicamente necesaria para el caso asignado.",
    )
    instructions = fields.Text(string="Instrucciones del supervisor")
    submission_ids = fields.One2many(
        "odental.academic.submission", "case_id", string="Trabajos clínicos"
    )
    submission_count = fields.Integer(compute="_compute_counts")
    approved_count = fields.Integer(compute="_compute_counts")
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("active", "Asignado"),
            ("completed", "Finalizado"),
            ("revoked", "Revocado"),
            ("expired", "Vencido"),
        ],
        required=True,
        default="draft",
        readonly=True,
        tracking=True,
        index=True,
    )
    completed_at = fields.Datetime(readonly=True, copy=False)
    completed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    revocation_reason = fields.Text(string="Motivo de revocación")

    @api.depends("submission_ids", "submission_ids.state")
    def _compute_counts(self):
        for case in self:
            case.submission_count = len(case.submission_ids)
            case.approved_count = len(
                case.submission_ids.filtered(lambda item: item.state in {"approved", "applied"})
            )

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            values["name"] = self.env["ir.sequence"].next_by_code(
                "odental.academic.case"
            ) or "Nuevo"
            values["state"] = "draft"
            values.pop("completed_at", None)
            values.pop("completed_by_id", None)
        return super().create(vals_list)

    def write(self, vals):
        controlled = {"state", "completed_at", "completed_by_id"}
        if (
            controlled.intersection(vals)
            and self.env.context.get("odental_academic_case_transition")
            is not _CASE_TRANSITION_TOKEN
        ):
            raise UserError("Utilice las acciones controladas del caso académico.")
        if any(case.state != "draft" for case in self) and {
            "rotation_id",
            "patient_id",
            "student_user_id",
            "supervisor_user_id",
            "supervisor_professional_id",
            "access_start",
            "access_end",
        }.intersection(vals):
            raise UserError("La asignación activa no puede alterarse; revoque y cree otra.")
        return super().write(vals)

    def unlink(self):
        if any(case.state != "draft" or case.submission_ids for case in self):
            raise UserError("Solo puede eliminar un caso en borrador sin trabajos clínicos.")
        return super().unlink()

    def _transition(self, values):
        return self.with_context(
            odental_academic_case_transition=_CASE_TRANSITION_TOKEN
        ).write(values)

    @api.constrains(
        "rotation_id",
        "patient_id",
        "student_user_id",
        "supervisor_user_id",
        "supervisor_professional_id",
        "access_start",
        "access_end",
    )
    def _check_assignment(self):
        student_group = self.env.ref("odental_academic.group_odental_academic_student")
        supervisor_group = self.env.ref("odental_academic.group_odental_academic_supervisor")
        for case in self:
            if case.patient_id.organization_id != case.organization_id:
                raise ValidationError("El paciente pertenece a otra organización.")
            if case.student_user_id not in case.rotation_id.student_user_ids:
                raise ValidationError("El estudiante no está inscrito en la rotación.")
            if student_group not in case.student_user_id.groups_id:
                raise ValidationError("El usuario asignado no posee el perfil de estudiante.")
            if case.supervisor_user_id not in case.rotation_id.supervisor_user_ids:
                raise ValidationError("El docente no supervisa esta rotación.")
            if supervisor_group not in case.supervisor_user_id.groups_id:
                raise ValidationError("El usuario asignado no posee el perfil de supervisor.")
            if case.supervisor_professional_id.user_id != case.supervisor_user_id:
                raise ValidationError("El perfil profesional no corresponde al docente asignado.")
            if case.organization_id not in case.supervisor_professional_id.organization_ids:
                raise ValidationError("El supervisor no pertenece a la institución.")
            if case.access_end < case.access_start:
                raise ValidationError("La fecha final no puede ser anterior a la inicial.")
            if (
                case.access_start < case.rotation_id.date_start
                or case.access_end > case.rotation_id.date_end
            ):
                raise ValidationError("El acceso debe estar dentro de las fechas de la rotación.")

    def _check_supervisor(self):
        for case in self:
            if self.env.user.has_group("odental_academic.group_odental_academic_manager"):
                continue
            if (
                not self.env.user.has_group(
                    "odental_academic.group_odental_academic_supervisor"
                )
                or self.env.user not in case.rotation_id.supervisor_user_ids
            ):
                raise AccessError("Solo un supervisor asignado puede administrar este caso.")

    def _audit(self, event_type, summary, submission=False, content_hash=False):
        self.ensure_one()
        return self.env["odental.academic.audit"]._record(
            self,
            event_type,
            summary,
            submission=submission,
            content_hash=content_hash,
        )

    def action_activate(self):
        today = fields.Date.context_today(self)
        for case in self:
            case._check_supervisor()
            if case.state != "draft" or case.rotation_id.state != "active":
                raise UserError("El caso y su rotación deben estar listos para activarse.")
            if case.access_end < today:
                raise ValidationError("No puede activar un acceso que ya venció.")
            case._transition({"state": "active"})
            case._audit("case_activated", f"Caso asignado al estudiante: {case.name}")

    def action_complete(self):
        for case in self:
            case._check_supervisor()
            if case.state != "active":
                raise UserError("Solo un caso activo puede finalizarse.")
            if case.submission_ids.filtered(
                lambda item: item.state in {"submitted", "approved"}
            ):
                raise ValidationError("Revise o aplique primero todos los trabajos pendientes.")
            case._transition(
                {
                    "state": "completed",
                    "completed_at": fields.Datetime.now(),
                    "completed_by_id": self.env.user.id,
                }
            )
            case._audit("case_completed", f"Caso académico finalizado: {case.name}")

    def action_revoke(self):
        for case in self:
            case._check_supervisor()
            if case.state not in {"draft", "active"}:
                raise UserError("Este acceso ya fue finalizado.")
            if not (case.revocation_reason or "").strip():
                raise ValidationError("Indique el motivo de revocación.")
            case._transition(
                {
                    "state": "revoked",
                    "completed_at": fields.Datetime.now(),
                    "completed_by_id": self.env.user.id,
                }
            )
            case._audit("case_revoked", f"Acceso académico revocado: {case.name}")

    @api.model
    def _cron_expire_access(self):
        today = fields.Date.context_today(self)
        expired = self.sudo().search([("state", "=", "active"), ("access_end", "<", today)])
        for case in expired:
            case.with_context(
                odental_academic_case_transition=_CASE_TRANSITION_TOKEN
            ).write(
                {
                    "state": "expired",
                    "completed_at": fields.Datetime.now(),
                }
            )
            self.env["odental.academic.audit"]._record(
                case, "access_expired", f"Acceso académico vencido: {case.name}"
            )
