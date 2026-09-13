from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ODentalClinicalCollection(models.Model):
    _name = "odental.clinical.collection"
    _description = "Cobro clínico O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    cash_session_id = fields.Many2one(
        "odental.cash.session", string="Sesión de caja", required=True, ondelete="restrict", index=True
    )
    organization_id = fields.Many2one(
        related="cash_session_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="cash_session_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, tracking=True
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Factura",
        required=True,
        ondelete="restrict",
        domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('company_id', '=', company_id)]",
        tracking=True,
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Diario de pago",
        required=True,
        ondelete="restrict",
        domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]",
    )
    payment_channel = fields.Selection(
        [
            ("cash", "Efectivo"),
            ("card", "Tarjeta"),
            ("transfer", "Transferencia"),
            ("mobile_wallet", "Billetera móvil"),
            ("other", "Otro"),
        ],
        required=True,
        default="cash",
        tracking=True,
    )
    affects_cash = fields.Boolean(
        string="Afecta efectivo físico", default=True, help="Incluye este cobro en el arqueo de caja."
    )
    amount = fields.Monetary(required=True, tracking=True)
    memo = fields.Char(string="Referencia / comprobante")
    account_payment_id = fields.Many2one(
        "account.payment", string="Pago contable", readonly=True, copy=False, ondelete="restrict"
    )
    received_at = fields.Datetime(readonly=True, copy=False)
    received_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    cancellation_reason = fields.Text(copy=False)
    state = fields.Selection(
        [("draft", "Pendiente"), ("registered", "Registrado"), ("cancelled", "Cancelado")],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.clinical.collection"
                ) or "Nuevo"
        return super().create(vals_list)

    @api.onchange("payment_channel")
    def _onchange_payment_channel(self):
        for collection in self:
            collection.affects_cash = collection.payment_channel == "cash"

    @api.onchange("invoice_id")
    def _onchange_invoice_id(self):
        for collection in self:
            if collection.invoice_id:
                collection.amount = collection.invoice_id.amount_residual
                collection.patient_id = collection.invoice_id.odental_patient_id

    @api.constrains("amount")
    def _check_amount(self):
        for collection in self:
            if collection.amount <= 0:
                raise ValidationError("El importe del cobro debe ser mayor que cero.")

    @api.constrains("cash_session_id", "patient_id", "invoice_id", "journal_id", "amount")
    def _check_scope(self):
        for collection in self:
            if collection.cash_session_id.state != "open" and collection.state == "draft":
                raise ValidationError("Solo puede registrar cobros en una caja abierta.")
            if collection.patient_id.organization_id != collection.organization_id:
                raise ValidationError("El paciente pertenece a otra organización.")
            if collection.invoice_id.company_id != collection.company_id:
                raise ValidationError("La factura pertenece a otra compañía.")
            if collection.invoice_id.state != "posted":
                raise ValidationError("Solo puede cobrar una factura publicada.")
            if collection.invoice_id.payment_state in {"paid", "reversed"}:
                raise ValidationError("La factura ya no tiene saldo cobrable.")
            if collection.amount > collection.invoice_id.amount_residual:
                raise ValidationError("El cobro no puede superar el saldo pendiente de la factura.")
            if collection.invoice_id.odental_patient_id and collection.invoice_id.odental_patient_id != collection.patient_id:
                raise ValidationError("El paciente no corresponde a la factura seleccionada.")
            if collection.journal_id.company_id != collection.company_id:
                raise ValidationError("El diario de pago pertenece a otra compañía.")
            if collection.journal_id.type not in {"bank", "cash"}:
                raise ValidationError("Seleccione un diario de banco o efectivo.")

    def write(self, vals):
        if not self.env.context.get("allow_collection_transition"):
            if "state" in vals:
                raise UserError("Utilice las acciones del cobro para cambiar su estado.")
            protected = {
                "cash_session_id",
                "patient_id",
                "invoice_id",
                "journal_id",
                "payment_channel",
                "affects_cash",
                "amount",
                "account_payment_id",
            }
            if protected.intersection(vals) and any(item.state != "draft" for item in self):
                raise UserError("Un cobro registrado o cancelado no puede modificarse.")
        return super().write(vals)

    def unlink(self):
        if any(item.state != "draft" for item in self):
            raise UserError("Solo se pueden eliminar cobros pendientes.")
        return super().unlink()

    def action_register_payment(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError("Este cobro ya fue procesado.")
        self._check_scope()
        return {
            "name": "Registrar pago",
            "type": "ir.actions.act_window",
            "res_model": "account.payment.register",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "account.move",
                "active_ids": self.invoice_id.ids,
                "default_amount": self.amount,
                "default_journal_id": self.journal_id.id,
                "default_communication": self.memo or self.name,
                "default_odental_collection_id": self.id,
            },
        }

    def _link_payment(self, payment):
        self.ensure_one()
        if payment.company_id != self.company_id:
            raise ValidationError("El pago generado pertenece a otra compañía.")
        self.with_context(allow_collection_transition=True).write(
            {
                "state": "registered",
                "account_payment_id": payment.id,
                "received_at": fields.Datetime.now(),
                "received_by_id": self.env.user.id,
            }
        )
        if self.invoice_id.odental_treatment_plan_id:
            self.invoice_id.odental_treatment_plan_id.clinical_record_id._log_event(
                "payment_registered",
                f"Cobro {self.name} registrado por {self.amount} {self.currency_id.name}",
                source_record=self.invoice_id.odental_treatment_plan_id,
            )

    def action_cancel(self):
        for collection in self:
            if collection.state != "draft":
                raise UserError("Solo un cobro pendiente puede cancelarse.")
            if not collection.cancellation_reason:
                raise ValidationError("Indique el motivo de cancelación.")
            collection.with_context(allow_collection_transition=True).write(
                {"state": "cancelled"}
            )
