from odoo import fields, models


class ODentalPatient(models.Model):
    _inherit = "odental.patient"

    receivable_amount = fields.Monetary(
        string="Saldo por cobrar", compute="_compute_receivables", currency_field="company_currency_id"
    )
    overdue_amount = fields.Monetary(
        string="Saldo vencido", compute="_compute_receivables", currency_field="company_currency_id"
    )
    open_invoice_count = fields.Integer(compute="_compute_receivables")
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    payment_agreement_ids = fields.One2many(
        "odental.payment.agreement", "patient_id", string="Convenios de pago"
    )
    payment_agreement_count = fields.Integer(compute="_compute_payment_agreement_count")

    def _compute_payment_agreement_count(self):
        grouped = self.env["odental.payment.agreement"]._read_group(
            [("patient_id", "in", self.ids)], ["patient_id"], ["__count"]
        ) if self.ids else []
        counts = {patient.id: count for patient, count in grouped}
        for patient in self:
            patient.payment_agreement_count = counts.get(patient.id, 0)

    def _compute_receivables(self):
        Move = self.env["account.move"]
        today = fields.Date.context_today(self)
        for patient in self:
            invoices = Move.search([
                ("odental_patient_id", "=", patient.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "in", ("not_paid", "partial")),
            ])
            patient.receivable_amount = sum(invoices.mapped("amount_residual"))
            patient.overdue_amount = sum(
                invoices.filtered(
                    lambda move: move.invoice_date_due and move.invoice_date_due < today
                ).mapped("amount_residual")
            )
            patient.open_invoice_count = len(invoices)

    def action_view_receivables(self):
        self.ensure_one()
        return {
            "name": "Cuentas por cobrar",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [
                ("odental_patient_id", "=", self.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "in", ("not_paid", "partial")),
            ],
            "context": {"create": False},
        }

    def action_view_payment_agreements(self):
        self.ensure_one()
        return {
            "name": "Convenios de pago",
            "type": "ir.actions.act_window",
            "res_model": "odental.payment.agreement",
            "view_mode": "list,form",
            "domain": [("patient_id", "=", self.id)],
            "context": {"default_patient_id": self.id},
        }


class AccountMove(models.Model):
    _inherit = "account.move"

    odental_payment_agreement_ids = fields.Many2many(
        "odental.payment.agreement",
        "odental_agreement_invoice_rel",
        "move_id",
        "agreement_id",
        string="Convenios O Dental",
        readonly=True,
    )


class ODentalClinicalCollection(models.Model):
    _inherit = "odental.clinical.collection"

    installment_allocation_ids = fields.One2many(
        "odental.installment.allocation", "collection_id", string="Aplicaciones a cuotas"
    )
