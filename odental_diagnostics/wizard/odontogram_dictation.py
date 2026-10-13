import re
import unicodedata

from odoo import fields, models
from odoo.exceptions import UserError, ValidationError

from ..models.odontogram import TOOTH_CONDITIONS, TOOTH_SURFACES


def _normalize(value):
    value = unicodedata.normalize("NFKD", value or "")
    return " ".join("".join(char for char in value if not unicodedata.combining(char)).lower().split())


SURFACE_WORDS = {
    "whole": ("pieza completa", "toda la pieza"),
    "occlusal": ("oclusal",), "incisal": ("incisal",),
    "mesial": ("mesial",), "distal": ("distal",),
    "buccal": ("vestibular", "bucal"), "lingual": ("lingual",),
    "palatal": ("palatina", "palatino"), "cervical": ("cervical",),
    "root": ("raiz", "radicular"),
}
CONDITION_WORDS = {
    "healthy": ("sana", "sano"), "caries": ("caries",),
    "restoration": ("restauracion",),
    "temporary_restoration": ("restauracion temporal",),
    "missing": ("ausente",), "unerupted": ("no erupcionada", "no erupcionado"),
    "crown": ("corona",), "bridge_abutment": ("pilar de puente",),
    "pontic": ("pontico",), "implant": ("implante",),
    "root_canal": ("endodoncia", "tratamiento endodontico"),
    "extraction_indicated": ("extraccion indicada",),
    "fracture": ("fractura", "fracturada", "fracturado"),
    "mobility": ("movilidad",), "sealant": ("sellante",),
    "prosthesis": ("protesis",),
}
STATUS_WORDS = {
    "planned": ("planificado", "planificada", "pendiente"),
    "completed": ("realizado", "realizada", "completado", "completada"),
    "monitor": ("en observacion", "vigilar"),
    "existing": ("existente", "actual"),
}


def _matches(text, vocabulary):
    return {key for key, words in vocabulary.items()
            if any(re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text) for word in words)}


class ODentalOdontogramDictation(models.TransientModel):
    _name = "odental.odontogram.dictation"
    _description = "Revisión del dictado de un hallazgo dental"

    chart_id = fields.Many2one("odental.odontogram", required=True, readonly=True)
    transcript = fields.Text(string="Dictado", required=True)
    tooth_id = fields.Many2one("odental.tooth", string="Pieza propuesta")
    surface = fields.Selection(TOOTH_SURFACES, string="Superficie propuesta")
    condition = fields.Selection(TOOTH_CONDITIONS, string="Condición propuesta")
    status = fields.Selection([
        ("existing", "Existente"), ("planned", "Planificado"),
        ("completed", "Realizado"), ("monitor", "En observación"),
    ], string="Estado propuesto")
    notes = fields.Char(string="Detalle clínico")
    interpretation_message = fields.Text(string="Revisión", readonly=True)

    def _check_chart(self):
        self.ensure_one()
        self.chart_id.check_access_rights("write")
        self.chart_id.check_access_rule("write")
        if self.chart_id.state != "draft":
            raise UserError("Solo se pueden registrar hallazgos en un odontograma en borrador.")

    def action_interpret(self):
        self.ensure_one()
        self._check_chart()
        text = _normalize(self.transcript)
        if not text:
            raise ValidationError("Dicte o escriba el hallazgo antes de interpretarlo.")
        teeth = self.env["odental.tooth"].search([])
        codes = set(re.findall(r"\b(?:pieza|diente|fdi)\s*(\d[1-8])\b", text))
        names = {tooth.code for tooth in teeth if _normalize(tooth.name) in text}
        codes |= names
        surfaces = _matches(text, SURFACE_WORDS)
        conditions = _matches(text, CONDITION_WORDS)
        statuses = _matches(text, STATUS_WORDS)
        # Specific terms can include a shorter generic term (e.g. restauración temporal).
        if "temporary_restoration" in conditions:
            conditions.discard("restoration")
        warnings = []
        for label, choices in (("pieza", codes), ("superficie", surfaces),
                               ("condición", conditions), ("estado", statuses)):
            if len(choices) != 1:
                warnings.append(f"Revise {label}: {'no identificado' if not choices else 'varios valores'}.")
        tooth = teeth.filtered(lambda item: item.code in codes) if len(codes) == 1 else teeth.browse()
        if tooth and self.chart_id.dentition != "mixed" and tooth.dentition != self.chart_id.dentition:
            warnings.append("La pieza no corresponde a la dentición del odontograma.")
            tooth = teeth.browse()
        detail = re.search(r"\b(?:detalle|nota|observacion)\s*[:,-]?\s*(.+)$", self.transcript, re.I)
        self.write({
            "tooth_id": tooth.id if len(tooth) == 1 else False,
            "surface": next(iter(surfaces)) if len(surfaces) == 1 else False,
            "condition": next(iter(conditions)) if len(conditions) == 1 else False,
            "status": next(iter(statuses)) if len(statuses) == 1 else False,
            "notes": detail.group(1).strip()[:255] if detail else False,
            "interpretation_message": " ".join(warnings) or "Revise las propuestas antes de guardar.",
        })
        return {
            "type": "ir.actions.act_window", "res_model": self._name,
            "res_id": self.id, "view_mode": "form", "target": "new",
        }

    def action_apply(self):
        self.ensure_one()
        self._check_chart()
        if not self.tooth_id or not self.surface or not self.condition or not self.status:
            raise ValidationError("Revise y complete pieza, superficie, condición y estado.")
        finding = self.env["odental.odontogram.finding"].create({
            "odontogram_id": self.chart_id.id, "tooth_id": self.tooth_id.id,
            "surface": self.surface, "condition": self.condition,
            "status": self.status, "notes": self.notes,
        })
        self.chart_id.clinical_record_id._log_event(
            "dictation_applied", f"Dictado revisado para hallazgo #{finding.id}",
            source_record=self.chart_id,
        )
        return {"type": "ir.actions.act_window_close"}
