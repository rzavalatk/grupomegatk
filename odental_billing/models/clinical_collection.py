from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalClinicalCollection(models.Model):
    _name = "odental.clinical.collection"
    _description = "Cobro clínico O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(string="Número de cobro", default="Nuevo", readonly=True, copy=False, index=True)
    cash_session_id = fields.Many2one(
        "odental.cash.session", string="Sesión de caja", required=True, ondelete="restrict", index=True
    )
    organization_id = fields.Many2one(
        related="cash_session_id.organization_id", string="Organización", store=True, index=True
    )
    company_id = fields.Many2one(related="cash_session_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    patient_id = fields.Many2one(
        "odental.patient", string="Paciente", required=True, ondelete="restrict", index=True, tracking=True
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
        string="Canal de pago", required=True,
        default="cash",
        tracking=True,
    )
    affects_cash = fields.Boolean(
        string="Afecta efectivo físico", default=True, help="Incluye este cobro en el arqueo de caja."
    )
    amount = fields.Monetary(string="Importe", required=True, tracking=True)
    memo = fields.Char(string="Referencia / comprobante")
    account_payment_id = fields.Many2one(
        "account.payment", string="Pago contable", readonly=True, copy=False, ondelete="restrict"
    )
    received_at = fields.Datetime(string="Recibido el", readonly=True, copy=False)
    received_by_id = fields.Many2one("res.users", string="Recibido por", readonly=True, copy=False)
    cancellation_reason = fields.Text(string="Motivo de cancelación", copy=False)
    state = fields.Selection(
        [("draft", "Pendiente"), ("registered", "Registrado"), ("cancelled", "Cancelado")],
        required=True,
        string="Estado", default="draft",
        tracking=True,
        index=True,
    )

    partial_payment_reason = fields.Text(string="Motivo del abono parcial", tracking=True)
    partial_approved_by_id = fields.Many2one("res.users", string="Abono autorizado por", readonly=True, copy=False, tracking=True)
    partial_approved_at = fields.Datetime(string="Autorizado el", readonly=True, copy=False)
    partial_approved_amount = fields.Monetary(string="Importe autorizado", readonly=True, copy=False)
    partial_approved_balance = fields.Monetary(string="Saldo al autorizar", readonly=True, copy=False)

    def _system_fields(self):
        return {"account_payment_id", "received_at", "received_by_id", "partial_approved_by_id",
                "partial_approved_at", "partial_approved_amount", "partial_approved_balance"}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("state", self.env.context.get("default_state", "draft")) != "draft":
                raise UserError("Los cobros se crean pendientes y se registran mediante su pago contable.")
            if any(vals.get(key, self.env.context.get("default_" + key)) for key in self._system_fields()):
                raise UserError("Las referencias de pago y autorización no se ingresan manualmente.")
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

    @api.constrains("payment_channel", "affects_cash", "journal_id")
    def _check_cash_channel(self):
        for collection in self:
            if collection.affects_cash != (collection.payment_channel == "cash"):
                raise ValidationError("El canal Efectivo debe afectar el efectivo físico; los demás canales no.")
            if collection.payment_channel == "cash" and collection.journal_id.type != "cash":
                raise ValidationError("Un cobro en efectivo requiere un diario de efectivo.")

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
            if not collection.invoice_id.odental_is_clinical or collection.invoice_id.odental_patient_id != collection.patient_id:
                raise ValidationError("Seleccione una factura clínica del paciente indicado.")
            if collection.invoice_id.currency_id != collection.currency_id:
                raise ValidationError("La factura y la caja deben utilizar la misma moneda.")
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
        if {"state"}.union(self._system_fields()).intersection(vals):
            raise UserError("Utilice las acciones del cobro para cambiar su estado o autorización.")
        protected = {"cash_session_id", "patient_id", "invoice_id", "journal_id", "payment_channel",
                     "affects_cash", "amount", "memo", "partial_payment_reason", "cancellation_reason"}
        if protected.intersection(vals) and any(item.state != "draft" for item in self):
            raise UserError("Un cobro registrado o cancelado no puede modificarse.")
        values = dict(vals)
        if protected.intersection(vals):
            values.update(partial_approved_by_id=False, partial_approved_at=False,
                          partial_approved_amount=0, partial_approved_balance=0)
        return super().write(values)

    def action_authorize_partial(self):
        for collection in self:
            if self.env.user != collection.organization_id.owner_user_id:
                raise AccessError("Solo el responsable de la organización puede autorizar un abono parcial.")
            if self.env.user == collection.cash_session_id.cashier_id:
                raise AccessError("La autorización requiere una persona distinta del cajero.")
            if collection.state != "draft":
                raise UserError("Solo puede autorizar un cobro pendiente.")
            collection._check_scope()
            if collection.currency_id.compare_amounts(collection.amount, collection.invoice_id.amount_residual) >= 0:
                raise ValidationError("Este cobro no es un abono parcial.")
            if not (collection.partial_payment_reason or "").strip():
                raise ValidationError("Registre el motivo del abono parcial.")
            super(ODentalClinicalCollection, collection).write({
                "partial_approved_by_id": self.env.user.id, "partial_approved_at": fields.Datetime.now(),
                "partial_approved_amount": collection.amount,
                "partial_approved_balance": collection.invoice_id.amount_residual,
            })

    def _check_partial_authorization(self):
        self.ensure_one()
        balance = self.invoice_id.amount_residual
        if self.currency_id.compare_amounts(self.amount, balance) < 0:
            if (not self.partial_approved_at
                or self.partial_approved_by_id != self.organization_id.owner_user_id
                or self.partial_approved_by_id == self.cash_session_id.cashier_id
                or self.currency_id.compare_amounts(self.partial_approved_amount, self.amount)
                or self.currency_id.compare_amounts(self.partial_approved_balance, balance)):
                raise ValidationError("El abono parcial requiere autorización vigente del responsable de la organización.")

    def unlink(self):
        if any(item.state != "draft" for item in self):
            raise UserError("Solo se pueden eliminar cobros pendientes.")
        return super().unlink()

    def action_register_payment(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError("Este cobro ya fue procesado.")
        self._check_scope()
        self._check_partial_authorization()
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
        if self.state != "draft" or self.cash_session_id.state != "open":
            raise UserError("El cobro debe seguir pendiente en una caja abierta.")
        if payment.company_id != self.company_id:
            raise ValidationError("El pago generado pertenece a otra compañía.")
        super(ODentalClinicalCollection, self).write(
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
            super(ODentalClinicalCollection, collection).write(
                {"state": "cancelled"}
            )
