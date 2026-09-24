from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LenkaContractTemplate(models.Model):
    _name = 'lenka.contract.template'
    _description = 'Plantilla Contractual Lenka'
    _order = 'document_type, operation_type, name'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    document_type = fields.Selection([
        ('contract', 'Contrato'),
        ('promissory', 'Pagare'),
        ('guarantee', 'Documento de garantia'),
    ], required=True, default='contract')
    operation_type = fields.Selection([
        ('loan', 'Prestamo'),
        ('financing', 'Financiamiento'),
        ('lease', 'Arrendamiento'),
        ('all', 'Todos'),
    ], required=True, default='all')
    body_html = fields.Html(string='Contenido de plantilla', required=True)
    active = fields.Boolean(default=True)
    notes = fields.Text()

    def action_preview(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Plantilla contractual'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }


class LenkaGeneratedDocument(models.Model):
    _name = 'lenka.generated.document'
    _description = 'Documento Contractual Generado Lenka'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(required=True)
    operation_id = fields.Many2one('lenka.financial.operation', required=True, ondelete='cascade', tracking=True)
    partner_id = fields.Many2one(related='operation_id.partner_id', store=True)
    template_id = fields.Many2one('lenka.contract.template', required=True)
    document_type = fields.Selection(related='template_id.document_type', store=True)
    date = fields.Date(default=fields.Date.context_today, required=True)
    rendered_html = fields.Html(string='Documento generado', sanitize=False)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('generated', 'Generado'),
        ('signed', 'Firmado'),
        ('cancelled', 'Cancelado'),
    ], default='draft', tracking=True)
    attachment_id = fields.Many2one('ir.attachment', string='PDF / archivo firmado')
    signed_date = fields.Date()
    notes = fields.Text()

    def action_render(self):
        for rec in self:
            rec.rendered_html = rec.operation_id._render_lenka_template(rec.template_id)
            rec.state = 'generated'
        return True

    def action_mark_signed(self):
        for rec in self:
            if rec.state != 'generated':
                raise ValidationError(_('El documento debe estar generado antes de marcarlo como firmado.'))
            if rec.document_type == 'contract' and not rec.attachment_id:
                raise ValidationError(_('Adjunte el contrato firmado antes de marcarlo como firmado.'))
            rec.write({
                'state': 'signed',
                'signed_date': fields.Date.context_today(rec),
            })
            if rec.document_type == 'contract':
                rec.operation_id.write({
                    'contract_signed': True,
                    'contract_date': rec.signed_date,
                    'contract_reference': rec.name,
                })
        return True


class LenkaFinancialOperationContract(models.Model):
    _inherit = 'lenka.financial.operation'

    generated_document_ids = fields.One2many(
        'lenka.generated.document',
        'operation_id',
        string='Documentos contractuales',
    )

    def _template_values(self):
        self.ensure_one()
        guarantors = ', '.join(self.guarantor_ids.mapped('display_name')) or ''
        guarantees = '; '.join(self.guarantee_ids.mapped('description')) or ''
        product = self.product_id.display_name if self.product_id else ''
        operation_label = dict(self._fields['operation_type'].selection).get(self.operation_type, '')
        rate_label = dict(self._fields['rate_period'].selection).get(self.rate_period, '')
        return {
            '{{OPERACION}}': self.name or '',
            '{{TIPO_OPERACION}}': operation_label,
            '{{CLIENTE}}': self.partner_id.display_name or '',
            '{{IDENTIDAD_CLIENTE}}': getattr(self.partner_id, 'vat', False) or '',
            '{{RTN_CLIENTE}}': getattr(self.partner_id, 'vat', False) or '',
            '{{DIRECCION_CLIENTE}}': self.partner_id.contact_address or '',
            '{{CORREO_CLIENTE}}': self.partner_id.email or '',
            '{{TELEFONO_CLIENTE}}': self.partner_id.phone or self.partner_id.mobile or '',
            '{{AVALES}}': guarantors,
            '{{MONEDA}}': self.currency_id.name or '',
            '{{MONTO}}': format(self.principal_amount or 0.0, ',.2f'),
            '{{PRIMA}}': format(self.down_payment or 0.0, ',.2f'),
            '{{MONTO_FINANCIADO}}': format(self.financed_amount or 0.0, ',.2f'),
            '{{TASA}}': format(self.interest_rate or 0.0, '.4f').rstrip('0').rstrip('.'),
            '{{PERIODO_TASA}}': rate_label,
            '{{PLAZO_MESES}}': str(self.term_months or 0),
            '{{PRIMER_PAGO}}': fields.Date.to_string(self.first_payment_date) if self.first_payment_date else '',
            '{{PRODUCTO}}': product,
            '{{GARANTIAS}}': guarantees,
            '{{OPCION_COMPRA}}': format(self.residual_purchase_amount or 0.0, ',.2f'),
            '{{FECHA}}': fields.Date.to_string(fields.Date.context_today(self)),
        }

    def _render_lenka_template(self, template):
        self.ensure_one()
        if template.company_id != self.company_id:
            raise ValidationError(_('La plantilla contractual pertenece a otra empresa.'))
        if template.operation_type not in ('all', self.operation_type):
            raise ValidationError(_('La plantilla seleccionada no corresponde al tipo de operacion.'))
        body = template.body_html or ''
        for token, value in self._template_values().items():
            body = body.replace(token, value)
        return body

    def action_generate_contract_documents(self):
        for rec in self:
            if rec.is_quote:
                raise ValidationError(_('Convierta la cotizacion en solicitud antes de generar documentos contractuales.'))
            templates = self.env['lenka.contract.template'].search([
                ('company_id', '=', rec.company_id.id),
                ('active', '=', True),
                ('operation_type', 'in', (rec.operation_type, 'all')),
            ])
            if not templates:
                raise ValidationError(_('No existen plantillas contractuales activas para esta operacion.'))
            for template in templates:
                name = '%s - %s' % (rec.name, template.name)
                existing = rec.generated_document_ids.filtered(
                    lambda d: d.template_id == template and d.state != 'cancelled'
                )
                if existing:
                    continue
                doc = self.env['lenka.generated.document'].create({
                    'name': name,
                    'operation_id': rec.id,
                    'template_id': template.id,
                })
                doc.action_render()
        return True
