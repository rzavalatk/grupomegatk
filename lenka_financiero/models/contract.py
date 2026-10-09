import re
from html import escape

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import file_open


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
    builtin_key = fields.Char(copy=False, readonly=True)

    _sql_constraints = [
        ('builtin_company_unique', 'unique(company_id, builtin_key)',
         'Esta empresa ya tiene una copia del contrato aprobado.'),
    ]

    @api.model
    def _approved_equipment_template(self, company):
        # Uses ordinary ACLs and the selected operation's company; never sudo.
        template = self.with_context(active_test=False).search([
            ('company_id', '=', company.id),
            ('builtin_key', '=', 'equipment_20261009'),
        ], limit=1)
        if template:
            if not template.active:
                raise ValidationError(_('El contrato aprobado está archivado. Reactivalo en Plantillas contractuales para utilizarlo.'))
            return template
        with file_open('lenka_financiero/data/equipment_contract.html', 'r') as source:
            body = source.read()
        return self.create({
            'name': 'Contrato de financiamiento de equipo — Lenka',
            'company_id': company.id, 'document_type': 'contract',
            'operation_type': 'financing', 'body_html': body,
            'builtin_key': 'equipment_20261009',
            'notes': 'Formato aprobado por Luis el 09/10/2026. Datos variables por operación. '
                     'Conservar las cláusulas aprobadas; cualquier cambio posterior requiere revisión.',
        })

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
    signed_file = fields.Binary(
        string='Subir contrato firmado', compute='_compute_signed_file',
        inverse='_inverse_signed_file', attachment=False,
    )
    signed_filename = fields.Char(string='Nombre del archivo firmado')
    signed_date = fields.Date()
    notes = fields.Text()

    @api.depends('attachment_id', 'attachment_id.datas')
    def _compute_signed_file(self):
        for rec in self:
            rec.signed_file = rec.attachment_id.with_context(bin_size=False).datas

    def _inverse_signed_file(self):
        for rec in self:
            if rec.state == 'signed':
                raise ValidationError(_('El documento ya está firmado; no se puede sustituir su archivo.'))
            if rec.signed_file:
                rec.attachment_id = self.env['ir.attachment'].create({
                    'name': rec.signed_filename or '%s-firmado.pdf' % rec.name,
                    'type': 'binary', 'datas': rec.signed_file,
                    'res_model': rec._name, 'res_id': rec.id,
                })
            else:
                rec.attachment_id = False

    def action_download_contract(self):
        self.ensure_one()
        if self.state not in ('generated', 'signed') or not self.rendered_html:
            raise ValidationError(_('Primero generá el documento para poder descargarlo.'))
        return self.env.ref('lenka_financiero.action_report_lenka_generated_document').report_action(self, config=False)

    def action_render(self):
        for rec in self:
            if rec.state == 'signed':
                raise ValidationError(_('No se puede regenerar un documento firmado.'))
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

    equipment_contract_template_id = fields.Many2one(
        'lenka.contract.template', string='Contrato de equipo', copy=False,
        domain="[('company_id', '=', company_id), ('document_type', '=', 'contract'), ('operation_type', 'in', ['financing', 'all'])]",
    )
    contract_seller_representative = fields.Char(string='Representante del vendedor')
    contract_seller_identity = fields.Char(string='Identidad del representante del vendedor')
    contract_buyer_representative = fields.Char(string='Representante del comprador')
    contract_buyer_identity = fields.Char(string='Identidad del firmante comprador')
    contract_equipment_serial = fields.Char(string='Serie del equipo')
    contract_warranty = fields.Char(string='Garantía del equipo', default='1 año por desperfectos de fábrica')
    contract_isv_amount = fields.Monetary(string='ISV incluido en el valor del equipo')
    contract_payment_instructions = fields.Text(string='Lugar y cuenta para pagos')
    contract_signing_city = fields.Char(string='Ciudad de firma')

    @api.constrains('contract_isv_amount', 'principal_amount')
    def _check_contract_isv(self):
        for rec in self:
            if rec.contract_isv_amount < 0 or rec.contract_isv_amount > rec.principal_amount:
                raise ValidationError(_('El ISV incluido debe estar entre cero y el valor del equipo.'))

    def action_use_approved_equipment_contract(self):
        self.ensure_one()
        if self.operation_type != 'financing':
            raise ValidationError(_('Este contrato corresponde al financiamiento de equipos.'))
        self.equipment_contract_template_id = self.env['lenka.contract.template']._approved_equipment_template(self.company_id)
        return True

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
        values = {
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
        blank = '____________________________'
        values.update({
            '{{EMPRESA}}': self.company_id.name or '',
            '{{RTN_EMPRESA}}': self.company_id.vat or blank,
            '{{DIRECCION_EMPRESA}}': self.company_id.partner_id.contact_address or blank,
            '{{TELEFONO_EMPRESA}}': self.company_id.phone or blank,
            '{{REPRESENTANTE_VENDEDOR}}': self.contract_seller_representative or blank,
            '{{IDENTIDAD_VENDEDOR}}': self.contract_seller_identity or blank,
            '{{REPRESENTANTE_COMPRADOR}}': self.contract_buyer_representative or (self.partner_id.name if not self.partner_id.is_company else blank),
            '{{IDENTIDAD_FIRMANTE_COMPRADOR}}': self.contract_buyer_identity or blank,
            '{{SERIE_EQUIPO}}': self.contract_equipment_serial or blank,
            '{{GARANTIA_EQUIPO}}': self.contract_warranty or blank,
            '{{ISV_INCLUIDO}}': format(self.contract_isv_amount or 0.0, ',.2f'),
            '{{INSTRUCCIONES_PAGO}}': self.contract_payment_instructions or blank,
            '{{CIUDAD_FIRMA}}': self.contract_signing_city or self.company_id.city or blank,
            '{{TASA_MORA}}': format(self.late_fee_rate or 0.0, '.4f').rstrip('0').rstrip('.'),
        })
        return values

    def _render_lenka_template(self, template):
        self.ensure_one()
        if template.company_id != self.company_id:
            raise ValidationError(_('La plantilla contractual pertenece a otra empresa.'))
        if template.operation_type not in ('all', self.operation_type):
            raise ValidationError(_('La plantilla seleccionada no corresponde al tipo de operacion.'))
        body = template.body_html or ''
        values = self._template_values()
        # A single replacement pass prevents customer text being interpreted as
        # another token, and escaping prevents it becoming executable HTML.
        body = re.sub(r'\{\{[A-Z_]+\}\}',
                      lambda match: escape(str(values[match.group(0)]))
                      if match.group(0) in values else match.group(0), body)
        if template.builtin_key == 'equipment_20261009':
            if not self.schedule_line_ids:
                raise ValidationError(_('Primero calculá el plan en Tabla de amortización; después generá el contrato.'))
            body += self._contract_schedule_html()
        return body

    def _contract_schedule_html(self):
        self.ensure_one()
        rows = []
        for line in self.schedule_line_ids.sorted(key=lambda line: (line.sequence, line.id)):
            values = [str(line.sequence), fields.Date.to_string(line.date) or '',
                      format(line.opening_balance, ',.2f'), format(line.capital, ',.2f'),
                      format(line.interest, ',.2f'), format(line.extra_charge, ',.2f'),
                      format(line.payment, ',.2f'), format(line.closing_balance, ',.2f')]
            rows.append('<tr>' + ''.join('<td>%s</td>' % escape(value) for value in values) + '</tr>')
        return ('<div style="page-break-before:always"><h3>Anexo: plan de pagos — %s</h3>'
                '<table class="table table-sm table-bordered"><thead><tr>'
                '<th>N.º</th><th>Fecha</th><th>Saldo inicial</th><th>Capital</th>'
                '<th>Interés</th><th>Otros</th><th>Cuota</th><th>Saldo final</th>'
                '</tr></thead><tbody>%s</tbody></table></div>') % (escape(self.currency_id.name), ''.join(rows))

    def action_generate_contract_documents(self):
        for rec in self:
            if rec.is_quote:
                raise ValidationError(_('Convierta la cotizacion en solicitud antes de generar documentos contractuales.'))
            templates = self.env['lenka.contract.template'].search([
                ('company_id', '=', rec.company_id.id),
                ('active', '=', True),
                ('operation_type', 'in', (rec.operation_type, 'all')),
            ])
            if rec.operation_type == 'financing':
                selected = rec.equipment_contract_template_id
                if not selected and not templates.filtered(lambda t: t.document_type == 'contract'):
                    selected = self.env['lenka.contract.template']._approved_equipment_template(rec.company_id)
                    rec.equipment_contract_template_id = selected
                if selected:
                    if not selected.active or selected.company_id != rec.company_id or selected.document_type != 'contract':
                        raise ValidationError(_('Seleccioná un contrato activo de la misma empresa.'))
                    templates = templates.filtered(lambda t: t.document_type != 'contract') | selected
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
        self.ensure_one()
        documents = self.generated_document_ids.filtered(lambda d: d.state != 'cancelled')
        action = {
            'type': 'ir.actions.act_window', 'name': _('Descargar y adjuntar documentos'),
            'res_model': 'lenka.generated.document',
            'domain': [('id', 'in', documents.ids)],
            'view_mode': 'list,form', 'target': 'current',
        }
        if len(documents) == 1:
            action.update(view_mode='form', res_id=documents.id, target='new')
        return action
