import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from ..services.parser import parse_command


_SESSION_TRANSITION_TOKEN = object()


class ODentalAISession(models.Model):
    _name = "odental.ai.session"
    _description = "Sesión del asistente IA O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(default="Nueva", readonly=True, copy=False, index=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True, tracking=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    patient_id = fields.Many2one(
        "odental.patient", ondelete="restrict", index=True, tracking=True
    )
    professional_id = fields.Many2one(
        "odental.professional", required=True, ondelete="restrict", index=True, tracking=True
    )
    appointment_id = fields.Many2one(
        "odental.appointment", string="Cita de contexto", ondelete="restrict", index=True
    )
    odontogram_id = fields.Many2one(
        "odental.odontogram", string="Odontograma borrador", ondelete="restrict"
    )
    service_id = fields.Many2one("odental.service", ondelete="restrict")
    site_id = fields.Many2one("odental.site", ondelete="restrict")
    resource_ids = fields.Many2many(
        "odental.resource",
        "odental_ai_session_resource_rel",
        "session_id",
        "resource_id",
        string="Recursos para agendar",
    )
    input_source = fields.Selection(
        [("typed", "Texto"), ("voice", "Voz"), ("structured", "Integración controlada")],
        required=True,
        default="typed",
    )
    language_code = fields.Char(required=True, default="es-HN")
    command_text = fields.Text(string="Instrucción o transcripción", required=True)
    engine = fields.Selection(
        [("rules", "Analizador clínico controlado")], required=True, default="rules", readonly=True
    )
    warning_text = fields.Text(readonly=True, copy=False)
    input_hash = fields.Char(readonly=True, copy=False, index=True)
    proposal_hash = fields.Char(readonly=True, copy=False, index=True)
    execution_hash = fields.Char(readonly=True, copy=False, index=True)
    action_ids = fields.One2many(
        "odental.ai.action", "session_id", string="Acciones propuestas", readonly=True
    )
    audit_ids = fields.One2many(
        "odental.ai.audit", "session_id", string="Auditoría", readonly=True
    )
    action_count = fields.Integer(compute="_compute_action_counts")
    reversible_action_count = fields.Integer(compute="_compute_action_counts")
    audit_count = fields.Integer(compute="_compute_action_counts")
    state = fields.Selection(
        [
            ("captured", "Capturada"),
            ("analyzed", "Analizada"),
            ("confirmed", "Confirmada"),
            ("executed", "Ejecutada"),
            ("undone", "Deshecha"),
            ("cancelled", "Cancelada"),
        ],
        required=True,
        default="captured",
        tracking=True,
        index=True,
    )
    confirmed_at = fields.Datetime(readonly=True, copy=False)
    confirmed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    executed_at = fields.Datetime(readonly=True, copy=False)
    executed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    undone_at = fields.Datetime(readonly=True, copy=False)
    undone_by_id = fields.Many2one("res.users", readonly=True, copy=False)

    @api.depends("action_ids", "action_ids.undo_supported", "audit_ids")
    def _compute_action_counts(self):
        for session in self:
            session.action_count = len(session.action_ids)
            session.reversible_action_count = len(
                session.action_ids.filtered("undo_supported")
            )
            session.audit_count = len(session.audit_ids)

    @staticmethod
    def _digest(payload):
        if not isinstance(payload, str):
            payload = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nueva") == "Nueva":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.ai.session"
                ) or "Nueva"
        sessions = super().create(vals_list)
        for session in sessions:
            session._audit("captured", f"Instrucción capturada: {session.name}")
        return sessions

    def write(self, vals):
        controlled = {
            "state",
            "warning_text",
            "input_hash",
            "proposal_hash",
            "execution_hash",
            "confirmed_at",
            "confirmed_by_id",
            "executed_at",
            "executed_by_id",
            "undone_at",
            "undone_by_id",
        }
        if (
            controlled.intersection(vals)
            and self.env.context.get("odental_ai_transition") is not _SESSION_TRANSITION_TOKEN
        ):
            raise UserError("Utilice las acciones controladas de la sesión de IA.")
        editable = {
            "organization_id",
            "patient_id",
            "professional_id",
            "appointment_id",
            "odontogram_id",
            "service_id",
            "site_id",
            "resource_ids",
            "input_source",
            "language_code",
            "command_text",
        }
        if editable.intersection(vals) and any(session.state != "captured" for session in self):
            raise UserError("La instrucción confirmada no se puede alterar; cree una sesión nueva.")
        return super().write(vals)

    def unlink(self):
        raise UserError("Las sesiones de IA se conservan como evidencia de auditoría.")

    @api.constrains(
        "organization_id",
        "patient_id",
        "professional_id",
        "appointment_id",
        "odontogram_id",
        "service_id",
        "site_id",
        "resource_ids",
    )
    def _check_context_relations(self):
        for session in self:
            organization = session.organization_id
            if session.patient_id and session.patient_id.organization_id != organization:
                raise ValidationError("El paciente corresponde a otra organización.")
            if session.professional_id and organization not in session.professional_id.organization_ids:
                raise ValidationError("El profesional no pertenece a la organización.")
            if session.appointment_id:
                if session.appointment_id.organization_id != organization:
                    raise ValidationError("La cita corresponde a otra organización.")
                if session.patient_id and session.appointment_id.patient_id != session.patient_id:
                    raise ValidationError("La cita corresponde a otro paciente.")
                if session.professional_id and session.appointment_id.professional_id != session.professional_id:
                    raise ValidationError("La cita corresponde a otro profesional.")
            if session.odontogram_id:
                if session.odontogram_id.organization_id != organization:
                    raise ValidationError("El odontograma corresponde a otra organización.")
                if session.odontogram_id.state != "draft":
                    raise ValidationError("La IA solo puede trabajar sobre odontogramas en borrador.")
                if session.patient_id and session.odontogram_id.patient_id != session.patient_id:
                    raise ValidationError("El odontograma corresponde a otro paciente.")
            if session.service_id and session.service_id.organization_id != organization:
                raise ValidationError("El servicio corresponde a otra organización.")
            if session.site_id and not session.site_id.is_available_to(organization):
                raise ValidationError("La sede no está disponible para la organización.")
            if session.resource_ids and not session.site_id:
                raise ValidationError("Seleccione una sede para los recursos indicados.")
            if any(resource.site_id != session.site_id for resource in session.resource_ids):
                raise ValidationError("Los recursos deben pertenecer a la sede seleccionada.")
            if any(not resource.is_available_to(organization) for resource in session.resource_ids):
                raise ValidationError("Uno o más recursos no están disponibles.")

    def _audit(self, event_type, summary, action=False, content_hash=False):
        self.ensure_one()
        return self.env["odental.ai.audit"]._record_event(
            self,
            event_type,
            summary,
            action=action,
            content_hash=content_hash,
        )

    def _transition(self, values):
        return self.with_context(
            odental_ai_transition=_SESSION_TRANSITION_TOKEN
        ).write(values)

    def _check_confirming_user(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_professional"):
            raise AccessError("Solo un profesional autorizado puede confirmar acciones de IA.")
        if self.env.user.has_group("odental_core.group_odental_manager"):
            return
        if self.professional_id.user_id != self.env.user:
            raise AccessError("No puede confirmar acciones clínicas por otro profesional.")

    def action_analyze(self):
        for session in self:
            if session.state != "captured":
                raise UserError("Solo una instrucción recién capturada puede analizarse.")
            if not (session.command_text or "").strip():
                raise ValidationError("Ingrese o dicte una instrucción.")
            action_values, warnings = parse_command(session)
            if not action_values:
                raise ValidationError(
                    "No se encontró ninguna instrucción compatible. Revise el formato indicado."
                )
            actions = self.env["odental.ai.action"]._create_from_analysis(
                [dict(values, session_id=session.id) for values in action_values]
            )
            for action in actions:
                action._validate_ready()
            proposal = [action._canonical_payload() for action in actions.sorted("sequence")]
            input_hash = session._digest((session.command_text or "").strip())
            proposal_hash = session._digest(proposal)
            session._transition(
                {
                    "state": "analyzed",
                    "warning_text": "\n".join(warnings) if warnings else False,
                    "input_hash": input_hash,
                    "proposal_hash": proposal_hash,
                }
            )
            session._audit(
                "analyzed", f"Propuesta analizada: {session.name}", content_hash=proposal_hash
            )

    def action_confirm(self):
        for session in self:
            if session.state != "analyzed":
                raise UserError("La propuesta debe estar analizada antes de confirmarla.")
            session._check_confirming_user()
            if session.warning_text:
                raise ValidationError(
                    "Existen líneas no interpretadas. Cancele esta sesión y dicte una instrucción nueva."
                )
            if not session.action_ids:
                raise ValidationError("La sesión no contiene acciones para confirmar.")
            for action in session.action_ids:
                action._validate_ready()
            session._transition(
                {
                    "state": "confirmed",
                    "confirmed_at": fields.Datetime.now(),
                    "confirmed_by_id": self.env.user.id,
                }
            )
            session._audit(
                "confirmed",
                f"Propuesta confirmada por {self.env.user.display_name}: {session.name}",
                content_hash=session.proposal_hash,
            )

    def action_execute(self):
        for session in self:
            if session.state != "confirmed":
                raise UserError("Confirme la propuesta antes de ejecutarla.")
            session._check_confirming_user()
            for action in session.action_ids.sorted("sequence"):
                action._execute()
                session._audit(
                    "executed",
                    f"Acción ejecutada: {action.preview}",
                    action=action,
                    content_hash=action.result_hash,
                )
            execution = [action._execution_payload() for action in session.action_ids.sorted("sequence")]
            execution_hash = session._digest(execution)
            session._transition(
                {
                    "state": "executed",
                    "executed_at": fields.Datetime.now(),
                    "executed_by_id": self.env.user.id,
                    "execution_hash": execution_hash,
                }
            )
            session._log_clinical_event("ai_session_executed", "Sesión de IA ejecutada")

    def action_undo(self):
        for session in self:
            if session.state != "executed":
                raise UserError("Solo una sesión ejecutada puede deshacerse.")
            session._check_confirming_user()
            if any(not action.undo_supported for action in session.action_ids):
                raise ValidationError(
                    "La sesión contiene acciones con efectos posteriores y no puede deshacerse automáticamente."
                )
            for action in session.action_ids.sorted("sequence", reverse=True):
                action._undo()
                session._audit(
                    "undone",
                    f"Acción deshecha: {action.preview}",
                    action=action,
                    content_hash=action.result_hash,
                )
            session._transition(
                {
                    "state": "undone",
                    "undone_at": fields.Datetime.now(),
                    "undone_by_id": self.env.user.id,
                }
            )
            session._log_clinical_event("ai_session_undone", "Sesión de IA deshecha")

    def action_cancel(self):
        for session in self:
            if session.state not in {"captured", "analyzed", "confirmed"}:
                raise UserError("Esta sesión ya no puede cancelarse.")
            session._transition({"state": "cancelled"})
            session._audit("cancelled", f"Sesión cancelada: {session.name}")

    def action_view_audit(self):
        self.ensure_one()
        return {
            "name": "Auditoría de IA",
            "type": "ir.actions.act_window",
            "res_model": "odental.ai.audit",
            "view_mode": "list,form",
            "domain": [("session_id", "=", self.id)],
        }

    def _log_clinical_event(self, event_type, label):
        self.ensure_one()
        if not self.patient_id:
            return
        record = self.env["odental.clinical.record"].search(
            [("patient_id", "=", self.patient_id.id)], limit=1
        )
        if record:
            record._log_event(
                event_type,
                f"{label}: {self.name}",
                self.execution_hash,
                source_record=self,
            )
