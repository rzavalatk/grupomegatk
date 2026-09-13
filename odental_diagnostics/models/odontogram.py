import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


TOOTH_SURFACES = [
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
]

TOOTH_CONDITIONS = [
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
]


class ODentalOdontogram(models.Model):
    _name = "odental.odontogram"
    _description = "Odontograma O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "chart_datetime desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    clinical_record_id = fields.Many2one(
        "odental.clinical.record", required=True, ondelete="restrict", index=True
    )
    patient_id = fields.Many2one(
        related="clinical_record_id.patient_id", store=True, index=True
    )
    organization_id = fields.Many2one(
        related="clinical_record_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    professional_id = fields.Many2one(
        "odental.professional", required=True, ondelete="restrict", index=True, tracking=True
    )
    encounter_id = fields.Many2one(
        "odental.clinical.encounter", string="Evolución relacionada", ondelete="set null"
    )
    chart_datetime = fields.Datetime(
        string="Fecha y hora", required=True, default=fields.Datetime.now, index=True
    )
    dentition = fields.Selection(
        [
            ("permanent", "Permanente"),
            ("primary", "Temporal"),
            ("mixed", "Mixta"),
        ],
        required=True,
        default="permanent",
        tracking=True,
    )
    summary = fields.Text(string="Resumen clínico", tracking=True)
    finding_ids = fields.One2many(
        "odental.odontogram.finding", "odontogram_id", string="Hallazgos", copy=True
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("signed", "Firmado"),
            ("amended", "Rectificado"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )
    signed_at = fields.Datetime(readonly=True)
    signed_by_user_id = fields.Many2one("res.users", readonly=True)
    content_hash = fields.Char(string="Huella digital", readonly=True, copy=False, index=True)
    version = fields.Integer(required=True, default=1, readonly=True, copy=False)
    previous_version_id = fields.Many2one(
        "odental.odontogram", readonly=True, copy=False, ondelete="restrict"
    )
    amendment_ids = fields.One2many(
        "odental.odontogram", "previous_version_id", string="Rectificaciones"
    )
    amendment_reason = fields.Text(string="Motivo de rectificación", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.odontogram"
                ) or "Nuevo"
        odontograms = super().create(vals_list)
        for odontogram in odontograms:
            odontogram.clinical_record_id._log_event(
                "odontogram_created",
                f"Odontograma creado: {odontogram.name}",
                source_record=odontogram,
            )
        return odontograms

    @api.constrains("clinical_record_id", "professional_id", "encounter_id")
    def _check_relations(self):
        for odontogram in self:
            if odontogram.organization_id not in odontogram.professional_id.organization_ids:
                raise ValidationError("El profesional no pertenece a la organización del expediente.")
            if odontogram.encounter_id:
                if odontogram.encounter_id.clinical_record_id != odontogram.clinical_record_id:
                    raise ValidationError("La evolución corresponde a otro expediente.")
                if odontogram.encounter_id.professional_id != odontogram.professional_id:
                    raise ValidationError("La evolución corresponde a otro profesional.")

    @api.constrains("dentition")
    def _check_chart_dentition(self):
        for odontogram in self:
            incompatible = odontogram.finding_ids.filtered(
                lambda finding: odontogram.dentition != "mixed"
                and finding.tooth_id.dentition != odontogram.dentition
            )
            if incompatible:
                raise ValidationError(
                    "Existen piezas que no corresponden a la dentición seleccionada."
                )

    def _hash_payload(self):
        self.ensure_one()
        findings = [
            {
                "tooth": finding.tooth_id.code,
                "surface": finding.surface,
                "condition": finding.condition,
                "status": finding.status,
                "notes": finding.notes or "",
            }
            for finding in self.finding_ids.sorted(
                key=lambda item: (item.tooth_id.code, item.surface, item.condition, item.id)
            )
        ]
        payload = {
            "record": self.clinical_record_id.id,
            "patient": self.patient_id.id,
            "professional": self.professional_id.id,
            "datetime": fields.Datetime.to_string(self.chart_datetime),
            "dentition": self.dentition,
            "summary": self.summary or "",
            "version": self.version,
            "findings": findings,
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def write(self, vals):
        protected_fields = {
            "clinical_record_id",
            "professional_id",
            "encounter_id",
            "chart_datetime",
            "dentition",
            "summary",
            "finding_ids",
            "version",
            "previous_version_id",
            "amendment_reason",
            "signed_at",
            "signed_by_user_id",
            "content_hash",
        }
        if not self.env.context.get("allow_odontogram_transition"):
            for odontogram in self:
                if vals.get("state") in ("signed", "amended"):
                    raise UserError("Utilice las acciones de firma o rectificación.")
                if (
                    odontogram.state in ("signed", "amended")
                    and vals.get("state")
                    and vals["state"] != odontogram.state
                ):
                    raise UserError("El estado de un odontograma firmado no puede revertirse.")
                if odontogram.state in ("signed", "amended") and protected_fields.intersection(vals):
                    raise UserError(
                        "Un odontograma firmado no puede modificarse. Cree una rectificación."
                    )
        return super().write(vals)

    def unlink(self):
        if any(odontogram.state in ("signed", "amended") for odontogram in self):
            raise UserError("Un odontograma firmado o rectificado no puede eliminarse.")
        return super().unlink()

    def action_sign(self):
        for odontogram in self:
            if odontogram.state != "draft":
                raise UserError("Solo los odontogramas en borrador pueden firmarse.")
            if odontogram.previous_version_id and not odontogram.amendment_reason:
                raise ValidationError("Debe indicar el motivo de la rectificación.")
            odontogram._check_chart_dentition()
            content_hash = odontogram._hash_payload()
            odontogram.with_context(allow_odontogram_transition=True).write(
                {
                    "state": "signed",
                    "signed_at": fields.Datetime.now(),
                    "signed_by_user_id": self.env.user.id,
                    "content_hash": content_hash,
                }
            )
            odontogram.clinical_record_id._log_event(
                "odontogram_signed",
                f"Odontograma firmado: {odontogram.name}, versión {odontogram.version}",
                content_hash,
                source_record=odontogram,
            )

    def action_create_amendment(self):
        self.ensure_one()
        if self.state != "signed":
            raise UserError("Solo un odontograma firmado puede rectificarse.")
        findings = [
            (
                0,
                0,
                {
                    "tooth_id": finding.tooth_id.id,
                    "surface": finding.surface,
                    "condition": finding.condition,
                    "status": finding.status,
                    "notes": finding.notes,
                },
            )
            for finding in self.finding_ids
        ]
        amendment = self.create(
            {
                "clinical_record_id": self.clinical_record_id.id,
                "professional_id": self.professional_id.id,
                "encounter_id": self.encounter_id.id,
                "chart_datetime": fields.Datetime.now(),
                "dentition": self.dentition,
                "summary": self.summary,
                "finding_ids": findings,
                "version": self.version + 1,
                "previous_version_id": self.id,
            }
        )
        self.with_context(allow_odontogram_transition=True).write({"state": "amended"})
        self.clinical_record_id._log_event(
            "odontogram_amended",
            f"Rectificación creada para {self.name}: versión {amendment.version}",
            source_record=amendment,
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.odontogram",
            "res_id": amendment.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_cancel(self):
        self.filtered(lambda chart: chart.state == "draft").write({"state": "cancelled"})


class ODentalOdontogramFinding(models.Model):
    _name = "odental.odontogram.finding"
    _description = "Hallazgo de odontograma O Dental"
    _order = "tooth_id, surface, condition"

    odontogram_id = fields.Many2one(
        "odental.odontogram", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(
        related="odontogram_id.organization_id", store=True, index=True
    )
    patient_id = fields.Many2one(related="odontogram_id.patient_id", store=True, index=True)
    tooth_id = fields.Many2one("odental.tooth", required=True, ondelete="restrict", index=True)
    surface = fields.Selection(TOOTH_SURFACES, required=True, default="whole", index=True)
    condition = fields.Selection(TOOTH_CONDITIONS, required=True, index=True)
    status = fields.Selection(
        [
            ("existing", "Existente"),
            ("planned", "Planificado"),
            ("completed", "Realizado"),
            ("monitor", "En observación"),
        ],
        required=True,
        default="existing",
        index=True,
    )
    notes = fields.Char()

    _sql_constraints = [
        (
            "finding_unique",
            "unique(odontogram_id, tooth_id, surface, condition, status)",
            "Este hallazgo ya está registrado en la misma pieza y superficie.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        charts = self.env["odental.odontogram"].browse(
            [vals.get("odontogram_id") for vals in vals_list if vals.get("odontogram_id")]
        )
        if any(chart.state != "draft" for chart in charts):
            raise UserError("No se pueden agregar hallazgos a un odontograma firmado.")
        return super().create(vals_list)

    def write(self, vals):
        if any(finding.odontogram_id.state != "draft" for finding in self):
            raise UserError("No se pueden modificar hallazgos de un odontograma firmado.")
        if vals.get("odontogram_id"):
            target = self.env["odental.odontogram"].browse(vals["odontogram_id"])
            if target.state != "draft":
                raise UserError("No se pueden mover hallazgos a un odontograma firmado.")
        return super().write(vals)

    def unlink(self):
        if any(finding.odontogram_id.state != "draft" for finding in self):
            raise UserError("No se pueden eliminar hallazgos de un odontograma firmado.")
        return super().unlink()

    @api.constrains("odontogram_id", "tooth_id")
    def _check_dentition(self):
        for finding in self:
            if (
                finding.odontogram_id.dentition != "mixed"
                and finding.tooth_id.dentition != finding.odontogram_id.dentition
            ):
                raise ValidationError("La pieza no corresponde a la dentición seleccionada.")
