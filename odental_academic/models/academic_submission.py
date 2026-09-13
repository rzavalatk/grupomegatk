import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


SUBMISSION_TYPES = [
    ("clinical_note", "Nota clínica"),
    ("procedure_note", "Procedimiento realizado"),
    ("odontogram_finding", "Hallazgo de odontograma"),
]

_SUBMISSION_TRANSITION_TOKEN = object()
_REVISION_CREATE_TOKEN = object()


class ODentalAcademicSubmission(models.Model):
    _name = "odental.academic.submission"
    _description = "Trabajo clínico académico O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "submitted_at desc, create_date desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    case_id = fields.Many2one(
        "odental.academic.case", required=True, ondelete="restrict", index=True, tracking=True
    )
    rotation_id = fields.Many2one(related="case_id.rotation_id", store=True, index=True)
    organization_id = fields.Many2one(
        related="case_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    student_user_id = fields.Many2one(
        related="case_id.student_user_id", store=True, index=True
    )
    supervisor_user_id = fields.Many2one(
        related="case_id.supervisor_user_id", store=True, index=True
    )
    patient_display_name = fields.Char(
        related="case_id.patient_display_name", store=True, string="Paciente asignado"
    )
    submission_type = fields.Selection(
        SUBMISSION_TYPES, required=True, default="clinical_note", tracking=True, index=True
    )
    content = fields.Text(string="Contenido clínico", required=True, tracking=True)
    procedure_code = fields.Char(string="Código del procedimiento", tracking=True)
    procedure_name = fields.Char(string="Procedimiento o competencia", tracking=True)
    tooth_code = fields.Char(string="Pieza FDI", tracking=True)
    surface = fields.Selection(
        [
            ("whole", "Pieza completa"),
            ("occlusal", "Oclusal"),
            ("incisal", "Incisal"),
            ("mesial", "Mesial"),
            ("distal", "Distal"),
            ("buccal", "Vestibular"),
            ("lingual", "Lingual"),
            ("palatal", "Palatina"),
            ("cervical", "Cervical"),
            ("root", "Raíz"),
        ],
        tracking=True,
    )
    condition = fields.Selection(
        [
            ("healthy", "Sana"),
            ("caries", "Caries"),
            ("restoration", "Restauración"),
            ("temporary_restoration", "Restauración temporal"),
            ("missing", "Ausente"),
            ("unerupted", "No erupcionada"),
            ("crown", "Corona"),
            ("bridge_abutment", "Pilar de puente"),
            ("pontic", "Póntico"),
            ("implant", "Implante"),
            ("root_canal", "Tratamiento endodóntico"),
            ("extraction_indicated", "Extracción indicada"),
            ("fracture", "Fractura"),
            ("mobility", "Movilidad"),
            ("sealant", "Sellante"),
            ("prosthesis", "Prótesis"),
            ("other", "Otro"),
        ],
        tracking=True,
    )
    finding_status = fields.Selection(
        [
            ("existing", "Existente"),
            ("planned", "Planificado"),
            ("completed", "Realizado"),
            ("monitor", "En observación"),
        ],
        string="Estado del hallazgo",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Borrador del estudiante"),
            ("submitted", "En revisión docente"),
            ("approved", "Aprobado"),
            ("rejected", "Devuelto para corrección"),
            ("applied", "Incorporado como borrador"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="draft",
        readonly=True,
        tracking=True,
        index=True,
    )
    submitted_at = fields.Datetime(readonly=True, copy=False)
    submitted_hash = fields.Char(readonly=True, copy=False, index=True)
    supervisor_comments = fields.Text(string="Retroalimentación docente")
    supervisor_score = fields.Float(string="Calificación", help="Escala de 0 a 100.")
    competency = fields.Selection(
        [
            ("not_observed", "No observado"),
            ("developing", "En desarrollo"),
            ("competent", "Competente"),
            ("outstanding", "Sobresaliente"),
        ],
        default="not_observed",
        string="Nivel de competencia",
    )
    reviewed_at = fields.Datetime(readonly=True, copy=False)
    reviewed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    approval_hash = fields.Char(readonly=True, copy=False, index=True)
    target_model = fields.Char(readonly=True, copy=False)
    target_res_id = fields.Integer(readonly=True, copy=False)
    applied_at = fields.Datetime(readonly=True, copy=False)
    previous_submission_id = fields.Many2one(
        "odental.academic.submission", readonly=True, copy=False, ondelete="restrict"
    )
    revision_ids = fields.One2many(
        "odental.academic.submission", "previous_submission_id", string="Correcciones"
    )
    submission_count = fields.Integer(string="Cantidad", default=1, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        is_student = self.env.user.has_group(
            "odental_academic.group_odental_academic_student"
        )
        if not is_student:
            raise AccessError("Solo el estudiante asignado puede crear trabajo clínico.")
        for values in vals_list:
            case = self.env["odental.academic.case"].browse(values.get("case_id")).exists()
            if not case:
                raise ValidationError("Seleccione un caso académico autorizado.")
            if case.student_user_id != self.env.user:
                raise AccessError("No puede registrar trabajo en el caso de otro estudiante.")
            case._check_student_access()
            if (
                values.get("previous_submission_id")
                and self.env.context.get("odental_academic_revision_create")
                is not _REVISION_CREATE_TOKEN
            ):
                raise AccessError("Las correcciones solo se crean desde el trabajo rechazado.")
            values["name"] = self.env["ir.sequence"].next_by_code(
                "odental.academic.submission"
            ) or "Nuevo"
            values["state"] = "draft"
            for field_name in (
                "submitted_at",
                "submitted_hash",
                "supervisor_comments",
                "supervisor_score",
                "competency",
                "reviewed_at",
                "reviewed_by_id",
                "approval_hash",
                "target_model",
                "target_res_id",
                "applied_at",
            ):
                values.pop(field_name, None)
        return super().create(vals_list)

    def write(self, vals):
        controlled = {
            "state",
            "submitted_at",
            "submitted_hash",
            "reviewed_at",
            "reviewed_by_id",
            "approval_hash",
            "target_model",
            "target_res_id",
            "applied_at",
        }
        if (
            controlled.intersection(vals)
            and self.env.context.get("odental_academic_submission_transition")
            is not _SUBMISSION_TRANSITION_TOKEN
        ):
            raise UserError("Utilice las acciones controladas del trabajo académico.")

        clinical_fields = {
            "case_id",
            "submission_type",
            "content",
            "procedure_code",
            "procedure_name",
            "tooth_code",
            "surface",
            "condition",
            "finding_status",
            "previous_submission_id",
        }
        if clinical_fields.intersection(vals):
            if not self.env.user.has_group(
                "odental_academic.group_odental_academic_student"
            ):
                raise AccessError("El supervisor no puede alterar el trabajo del estudiante.")
            if "previous_submission_id" in vals:
                raise AccessError("La relación entre correcciones es inmutable.")
            target_case = False
            if vals.get("case_id"):
                target_case = self.env["odental.academic.case"].browse(
                    vals["case_id"]
                ).exists()
                if not target_case:
                    raise ValidationError("El caso académico no existe.")
                target_case._check_student_access()
            for submission in self:
                if submission.state != "draft":
                    raise UserError("Un trabajo enviado es inmutable; cree una corrección.")
                if submission.student_user_id != self.env.user:
                    raise AccessError("No puede editar el trabajo de otro estudiante.")

        review_fields = {"supervisor_comments", "supervisor_score", "competency"}
        if review_fields.intersection(vals):
            for submission in self:
                submission.case_id._check_supervisor()
                if submission.state != "submitted":
                    raise UserError("La evaluación docente requiere un trabajo enviado.")
        return super().write(vals)

    def unlink(self):
        for submission in self:
            if submission.state != "draft":
                raise UserError("Solo puede eliminar un borrador que todavía no fue enviado.")
            if (
                self.env.user.has_group("odental_academic.group_odental_academic_student")
                and submission.student_user_id != self.env.user
            ):
                raise AccessError("No puede eliminar el trabajo de otro estudiante.")
        return super().unlink()

    def _transition(self, values):
        return self.with_context(
            odental_academic_submission_transition=_SUBMISSION_TRANSITION_TOKEN
        ).write(values)

    @api.constrains("supervisor_score")
    def _check_score(self):
        for submission in self:
            if not 0 <= submission.supervisor_score <= 100:
                raise ValidationError("La calificación debe estar entre 0 y 100.")

    @api.constrains("submission_type", "tooth_code", "surface", "condition", "finding_status")
    def _check_odontogram_fields(self):
        for submission in self:
            if submission.submission_type != "odontogram_finding":
                continue
            if not all(
                [
                    submission.tooth_code,
                    submission.surface,
                    submission.condition,
                    submission.finding_status,
                ]
            ):
                raise ValidationError("Complete todos los campos del hallazgo odontológico.")
            if not self.env["odental.tooth"].sudo().search_count(
                [("code", "=", submission.tooth_code)], limit=1
            ):
                raise ValidationError("La pieza FDI indicada no existe.")

    def _payload(self):
        self.ensure_one()
        return {
            "case": self.case_id.id,
            "student": self.student_user_id.id,
            "type": self.submission_type,
            "content": self.content or "",
            "procedure_code": self.procedure_code or "",
            "procedure_name": self.procedure_name or "",
            "tooth_code": self.tooth_code or "",
            "surface": self.surface or "",
            "condition": self.condition or "",
            "finding_status": self.finding_status or "",
            "previous_submission": self.previous_submission_id.id,
        }

    @staticmethod
    def _hash(payload):
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _check_student(self):
        for submission in self:
            if (
                not self.env.user.has_group(
                    "odental_academic.group_odental_academic_student"
                )
                or submission.student_user_id != self.env.user
            ):
                raise AccessError("Solo el estudiante asignado puede enviar este trabajo.")
            submission.case_id._check_student_access()

    def action_submit(self):
        for submission in self:
            submission._check_student()
            if submission.state != "draft":
                raise UserError("Solo un borrador puede enviarse a revisión.")
            submission._check_odontogram_fields()
            content_hash = submission._hash(submission._payload())
            submission._transition(
                {
                    "state": "submitted",
                    "submitted_at": fields.Datetime.now(),
                    "submitted_hash": content_hash,
                }
            )
            submission.case_id._audit(
                "submission_submitted",
                f"Trabajo enviado a revisión: {submission.name}",
                submission=submission,
                content_hash=content_hash,
            )

    def action_approve(self):
        for submission in self:
            submission.case_id._check_supervisor()
            if submission.state != "submitted":
                raise UserError("Solo un trabajo enviado puede aprobarse.")
            if submission._hash(submission._payload()) != submission.submitted_hash:
                raise ValidationError("El contenido cambió después del envío y no puede aprobarse.")
            approval_hash = submission._hash(
                {
                    "submitted_hash": submission.submitted_hash,
                    "reviewer": self.env.user.id,
                    "comments": submission.supervisor_comments or "",
                    "score": submission.supervisor_score,
                    "competency": submission.competency,
                }
            )
            submission._transition(
                {
                    "state": "approved",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                    "approval_hash": approval_hash,
                }
            )
            submission.case_id._audit(
                "submission_approved",
                f"Trabajo aprobado por el supervisor: {submission.name}",
                submission=submission,
                content_hash=approval_hash,
            )

    def action_reject(self):
        for submission in self:
            submission.case_id._check_supervisor()
            if submission.state != "submitted":
                raise UserError("Solo un trabajo enviado puede devolverse.")
            if not (submission.supervisor_comments or "").strip():
                raise ValidationError("Explique al estudiante qué debe corregir.")
            submission._transition(
                {
                    "state": "rejected",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )
            submission.case_id._audit(
                "submission_rejected",
                f"Trabajo devuelto para corrección: {submission.name}",
                submission=submission,
                content_hash=submission.submitted_hash,
            )

    def action_apply(self):
        for submission in self:
            submission.case_id._check_supervisor()
            if submission.state != "approved":
                raise UserError("El trabajo debe estar aprobado antes de incorporarlo.")
            case = submission.case_id
            clinical_record = self.env["odental.clinical.record"].search(
                [("patient_id", "=", case.patient_id.id), ("state", "=", "active")],
                limit=1,
            )
            if not clinical_record:
                raise ValidationError("El paciente no tiene un expediente clínico activo.")

            if submission.submission_type in {"clinical_note", "procedure_note"}:
                values = {
                    "clinical_record_id": clinical_record.id,
                    "professional_id": case.supervisor_professional_id.id,
                }
                target_field = (
                    "clinical_findings"
                    if submission.submission_type == "clinical_note"
                    else "procedures_performed"
                )
                values[target_field] = submission.content
                target = self.env["odental.clinical.encounter"].create(values)
            else:
                odontogram = self.env["odental.odontogram"].search(
                    [
                        ("clinical_record_id", "=", clinical_record.id),
                        ("professional_id", "=", case.supervisor_professional_id.id),
                        ("state", "=", "draft"),
                    ],
                    order="chart_datetime desc, id desc",
                    limit=1,
                )
                if not odontogram:
                    odontogram = self.env["odental.odontogram"].create(
                        {
                            "clinical_record_id": clinical_record.id,
                            "professional_id": case.supervisor_professional_id.id,
                            "dentition": "mixed",
                            "summary": f"Borrador supervisado del caso académico {case.name}.",
                        }
                    )
                tooth = self.env["odental.tooth"].search(
                    [("code", "=", submission.tooth_code)], limit=1
                )
                target = self.env["odental.odontogram.finding"].create(
                    {
                        "odontogram_id": odontogram.id,
                        "tooth_id": tooth.id,
                        "surface": submission.surface,
                        "condition": submission.condition,
                        "status": submission.finding_status,
                        "notes": submission.content,
                    }
                )

            submission._transition(
                {
                    "state": "applied",
                    "target_model": target._name,
                    "target_res_id": target.id,
                    "applied_at": fields.Datetime.now(),
                }
            )
            case._audit(
                "submission_applied",
                f"Trabajo incorporado como borrador clínico: {submission.name}",
                submission=submission,
                content_hash=submission.approval_hash,
            )

    def action_create_revision(self):
        self.ensure_one()
        self._check_student()
        if self.state != "rejected":
            raise UserError("Solo un trabajo devuelto puede corregirse.")
        revision = self.with_context(
            odental_academic_revision_create=_REVISION_CREATE_TOKEN
        ).create(
            {
                "case_id": self.case_id.id,
                "submission_type": self.submission_type,
                "content": self.content,
                "procedure_code": self.procedure_code,
                "procedure_name": self.procedure_name,
                "tooth_code": self.tooth_code,
                "surface": self.surface,
                "condition": self.condition,
                "finding_status": self.finding_status,
                "previous_submission_id": self.id,
            }
        )
        self.case_id._audit(
            "submission_revised",
            f"Corrección creada desde {self.name}: {revision.name}",
            submission=revision,
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.academic.submission",
            "res_id": revision.id,
            "view_mode": "form",
            "target": "current",
        }


class ODentalAcademicCaseStudentAccess(models.Model):
    _inherit = "odental.academic.case"

    def _check_student_access(self):
        today = fields.Date.context_today(self)
        for case in self:
            if case.student_user_id != self.env.user:
                raise AccessError("Este caso está asignado a otro estudiante.")
            if case.state != "active" or not (case.access_start <= today <= case.access_end):
                raise AccessError("El acceso académico no está activo o ya venció.")
