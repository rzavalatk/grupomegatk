# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class PaymentInvoice(models.TransientModel):
    _name = "banks.invoice.payment.supplier"

    @api.model
    def _get_invoice_number(self):
        ctx = self._context
        if 'active_id' in ctx:
            inv = self.env['account.invoice'].browse(ctx['active_id'])
            return inv.number
        else:
            raise Warning(_('!! No se pudo completar la transacción intente nuevamente!!'))

    def get_msg_number(self):
        if self.journal_id and self.doc_type:
            flag = False
            for seq in self.journal_id.secuencia_ids:
                if seq.move_type == self.doc_type:
                    self.name = seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual
                    flag = True
            if not flag:
                self.msg = "No existe numeración para este banco, verifique la configuración"
                self.name = ""
            else:
                self.msg = ""

    @api.onchange("doc_type")
    def onchangedoc_type(self):
        if self.journal_id and self.doc_type:
            self.get_msg_number()

    @api.onchange("journal_id")
    def onchangedoc_journal(self):
        if self.journal_id and self.doc_type:
            self.get_msg_number()

    @api.model
    def _get_amount(self):
        ctx = self._context
        if 'active_id' in ctx:
            inv = self.env['account.invoice'].browse(ctx['active_id'])
            return inv.residual
        else:
            return 0.00

    fecha = fields.Date(string="Fecha", required=True)
    journal_id = fields.Many2one('account.journal', 'Diario', required=True, domain=[('type', 'in', ['bank', 'cash'])])
    name = fields.Char(string="Número", required=True, compute=get_msg_number)
    amount = fields.Float("Monto a Pagar", required=True, default=_get_amount)
    invoice_number = fields.Char("# de Factura", readonly=True, default=_get_invoice_number)
    doc_type = fields.Selection([('check', 'Cheque'), ('transference', 'Transferencia'), ('otro', 'Otro')], string='Tipo de Transacción', required=True)
    msg = fields.Char(compute=get_msg_number)
    ref = fields.Char("Referencia de pago", required=True)

    @api.multi
    def action_pago(self):
        self.get_msg_number()
        obj_pago = self.env["banks.payment.invoices.custom"]
        active_id = self._context.get('active_id')
        lineas = []
        if active_id:
            inv = self.env['account.invoice'].browse(active_id)
            if inv.residual < 0:
                raise Warning(_('!! Amount must be greater than zero !!'))

            invoice_ids = {
                'partner_id': inv.partner_id.id,
                'number': inv.number,
                'date_invoice': inv.date_invoice,
                'date_due': inv.date_due,
                'name': inv.name,
                'invoice_id': inv.id,
                'amount_total': inv.amount_total,
                'residual': inv.residual,
                'amount_total': inv.amount_total,
                'monto_pago': self.amount,
                'state': inv.state,
            }
            lineas.append((0, 0, invoice_ids))
            values = {
                'bank_reference': self.ref,
                'effective_date': self.fecha,
                'date': self.fecha,
                'journal_id': self.journal_id.id,
                'partner_id': inv.partner_id.id,
                'invoice_ids': lineas,
                'doc_type': self.doc_type,
                'amount': self.amount,
                'state': 'draft',
                'name': self.name,
            }
            inv_id = obj_pago.create(values)
            inv_id.post_payment()

        else:
            raise except_orm(_('Advertencia'), _('.No se puede registrar el pago, consulte el administrador del sistema!!'))

