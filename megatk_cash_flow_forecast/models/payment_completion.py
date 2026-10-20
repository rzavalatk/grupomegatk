from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


AUDIT_FIELDS = {'paid_amount', 'paid_date', 'paid_reference', 'paid_by'}


class CashflowPromisePayment(models.Model):
    _inherit = 'cashflow.promise'

    state = fields.Selection(selection_add=[('paid', 'Pago realizado')], ondelete={'paid': 'set default'})
    paid_amount = fields.Monetary(string='Importe pagado', currency_field='currency_id', readonly=True, copy=False, tracking=True)
    paid_date = fields.Date(string='Fecha del pago', readonly=True, copy=False, tracking=True)
    paid_reference = fields.Char(string='Referencia del pago', readonly=True, copy=False, tracking=True)
    paid_by = fields.Many2one('res.users', string='Registrado por', readonly=True, copy=False, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        if any(v.get('state') == 'paid' or any(v.get(f) for f in AUDIT_FIELDS) for v in vals_list):
            raise AccessError(_('Utilice Marcar pago realizado para registrar el cierre.'))
        return super().create(vals_list)

    def write(self, vals):
        if AUDIT_FIELDS.intersection(vals) or vals.get('state') == 'paid':
            raise AccessError(_('Utilice Marcar pago realizado para registrar el cierre.'))
        if self.filtered(lambda p: p.state == 'paid'):
            raise ValidationError(_('El pago realizado conserva su historial y no puede modificarse.'))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda p: p.state == 'paid'):
            raise ValidationError(_('El pago realizado debe conservarse en el historial.'))
        return super().unlink()

    def action_open_payment_completion(self):
        self.ensure_one()
        self.check_access('write')
        if self.direction != 'payable' or self.state != 'active':
            raise ValidationError(_('Seleccione un pago planificado activo.'))
        return {'type': 'ir.actions.act_window', 'name': _('Marcar pago realizado'),
                'res_model': 'cashflow.payment.completion', 'view_mode': 'form', 'target': 'new',
                'context': {'default_promise_id': self.id}}

    def _complete_payment(self, amount, payment_date, reference):
        self.ensure_one()
        self.check_access('write')
        self.env.cr.execute('SELECT id FROM cashflow_promise WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        if self.direction != 'payable' or self.state != 'active':
            raise ValidationError(_('Seleccione un pago planificado activo.'))
        amount = self.currency_id.round(amount)
        if amount <= 0 or self.currency_id.compare_amounts(amount, self.amount) > 0:
            raise ValidationError(_('El importe pagado debe ser mayor que cero y no superar el pago planificado.'))
        if not payment_date or fields.Date.to_date(payment_date) > fields.Date.context_today(self):
            raise ValidationError(_('Indique la fecha real del pago, sin fechas futuras.'))
        if not (reference or '').strip():
            raise ValidationError(_('Indique una referencia o descripción del pago realizado.'))
        remaining = self.currency_id.round(self.amount - amount)
        # No payment, journal entry or reconciliation is created. For a partial
        # payment, retain the original plan in history and project only the rest.
        if remaining:
            self.copy({'amount': remaining, 'state': 'active'})
        super(CashflowPromisePayment, self).write({
            'state': 'paid', 'paid_amount': amount, 'paid_date': payment_date,
            'paid_reference': reference.strip(), 'paid_by': self.env.uid,
        })
        self.message_post(body=Markup('<b>Pago realizado</b><p>Fecha: %s · Importe: %s %s · Referencia: %s</p><p>Pendiente de esta planificación: %s. No se generaron asientos contables.</p>') % (
            payment_date, self.currency_id.name, amount, reference.strip(), remaining))
        return True


class CashflowPaymentCompletion(models.TransientModel):
    _name = 'cashflow.payment.completion'
    _description = 'Confirmar pago realizado en la proyección'

    promise_id = fields.Many2one('cashflow.promise', required=True, readonly=True)
    currency_id = fields.Many2one(related='promise_id.currency_id')
    amount = fields.Monetary(string='Importe pagado', required=True, currency_field='currency_id')
    payment_date = fields.Date(string='Fecha del pago', required=True, default=fields.Date.context_today)
    reference = fields.Char(string='Referencia o descripción', required=True)

    @api.model
    def default_get(self, names):
        vals = super().default_get(names)
        if vals.get('promise_id') and 'amount' in names:
            promise = self.env['cashflow.promise'].browse(vals['promise_id'])
            promise.check_access('write')
            vals['amount'] = promise.amount
        return vals

    def action_confirm(self):
        self.ensure_one()
        self.promise_id._complete_payment(self.amount, self.payment_date, self.reference)
        return {'type': 'ir.actions.client', 'tag': 'reload'}
