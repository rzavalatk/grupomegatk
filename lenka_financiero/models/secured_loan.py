import copy
import re
from html import escape

from lxml import html, etree
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import file_open


SECURED_KEY = 'secured_loan_20261016'


def bold(value):
    return '<strong>%s</strong>' % escape(str(value or ''))


def paragraph(value):
    return '<p>%s</p>' % value


class LenkaPartnerIdentity(models.Model):
    _inherit = 'res.partner'

    lenka_identity_number = fields.Char(
        string='Documento de identidad (Lenka)',
        help='DNI o documento de identidad de la persona. Es independiente del RTN / NIF fiscal.',
    )


class LenkaSecuredTemplate(models.Model):
    _inherit = 'lenka.contract.template'

    @api.model
    def _approved_secured_loan_template(self, company):
        template = self.with_context(active_test=False).search([
            ('company_id', '=', company.id), ('builtin_key', '=', SECURED_KEY),
        ], limit=1)
        if template:
            if not template.active:
                raise ValidationError(_('El contrato con aval o garantía está archivado. Reactívelo en Plantillas contractuales.'))
            return template
        with file_open('lenka_financiero/data/secured_loan_contract.html', 'r') as source:
            body = source.read()
        # Preserve the company's approved letterhead without copying its wording.
        approved = self.search([
            ('company_id', '=', company.id),
            ('builtin_key', '=', 'unsecured_loan_20261014'),
        ], limit=1)
        if approved:
            fragment = html.fragment_fromstring(approved.body_html, create_parent='div')
            logo = fragment.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " lenka-membrete ")]')
            if logo:
                body = etree.tostring(copy.deepcopy(logo[0]), encoding='unicode', method='html') + body
        elif company.logo and not company.uses_default_logo:
            body = '<div class="lenka-membrete"><img alt="Inversiones Lenka" style="width:220px;height:auto" src="data:image/png;base64,%s"></div>' % company.logo.decode() + body
        return self.create({
            'name': 'Préstamo con aval solidario o garantía — Lenka',
            'company_id': company.id, 'document_type': 'contract',
            'operation_type': 'loan', 'builtin_key': SECURED_KEY,
            'body_html': body,
            'notes': 'Referencia: Contrato de Prestamo Condepah.doc. Entidad, representante y avales separados. '
                     'El representante solo responde personalmente si fue agregado expresamente como aval. '
                     'Garantías tomadas del expediente; la constitución o inscripción del respaldo se documenta por separado cuando corresponda.',
        })


class LenkaSecuredLoan(models.Model):
    _inherit = 'lenka.financial.operation'

    def _secured_loan_font_css(self):
        # Reuse the embedded fonts already configured for Lenka's approved PDF.
        view = self.env['ir.ui.view'].search([
            ('name', '=', 'Lenka fiduciario - Times New Roman 14'),
        ], limit=1)
        return Markup('\n'.join(re.findall(r'@font-face\s*\{[^}]*\}', view.arch_db or '')))

    def _secured_lender_and_payments(self):
        """Reuse company data in the database; private identifiers stay out of code."""
        self.ensure_one()
        seller = self.contract_seller_representative or ''
        identity = self.contract_seller_identity or ''
        payments = paragraph(escape(self.contract_payment_instructions)) if self.contract_payment_instructions else ''
        approved = self.env['lenka.contract.template'].search([
            ('company_id', '=', self.company_id.id),
            ('builtin_key', '=', 'unsecured_loan_20261014'),
        ], limit=1)
        if approved:
            root = html.fragment_fromstring(approved.body_html, create_parent='div')
            paragraphs = root.xpath('.//p')
            if paragraphs:
                names = paragraphs[0].xpath('.//strong')
                if len(names) >= 4:
                    old_seller = names[-2].text_content().strip()
                    old_identity = names[-1].text_content().strip()
                    if old_seller and not re.fullmatch(r'\{\{[A-Z_]+\}\}|[_\s]+', old_seller):
                        seller = seller or old_seller
                    if old_identity and not re.fullmatch(r'\{\{[A-Z_]+\}\}|[_\s]+', old_identity):
                        identity = identity or old_identity
            if not payments:
                headings = root.xpath('.//h3[starts-with(normalize-space(.), "Cuarta")]')
                if headings:
                    following = headings[0].getnext()
                    if following is not None and following.tag == 'p':
                        payments = etree.tostring(following, encoding='unicode', method='html')
        return seller, identity, payments

    def _secured_loan_signer(self):
        self.ensure_one()
        person = self.contract_buyer_partner_id
        name = self.contract_buyer_representative or person.name
        identity = self.contract_buyer_identity or person.lenka_identity_number
        if not self.partner_id.is_company:
            name = self.partner_id.name
            identity = self.contract_buyer_identity or self.partner_id.lenka_identity_number
        return name or '', identity or ''

    def _validate_secured_loan_contract(self):
        self.ensure_one()
        if self.operation_type != 'loan' or self.security_mode != 'backed':
            raise ValidationError(_('Este contrato corresponde a Préstamo con aval o garantía. Revise Tipo de operación y Modalidad de respaldo.'))
        if self.late_fee_method != 'balance_monthly':
            raise ValidationError(_('Revise Base de mora: seleccione Saldo de capital pendiente, mensual / 30 días para este contrato.'))
        if self.contract_buyer_partner_id.is_company:
            raise ValidationError(_('El representante legal / firmante debe ser una persona natural.'))
        guarantees = self.guarantee_ids.filtered(lambda g: g.state in ('proposed', 'accepted', 'active'))
        if not self.guarantor_ids and not guarantees:
            raise ValidationError(_('Registre al menos un Aval o una Garantía vigente/propuesta antes de generar el contrato.'))
        missing = []
        lender, lender_id, payments = self._secured_lender_and_payments()
        if not lender or not lender_id:
            missing.append(_('representante de Lenka e identidad'))
        if not payments:
            missing.append(_('lugar y cuenta para pagos'))
        name, identity = self._secured_loan_signer()
        if not name:
            missing.append(_('nombre del representante legal / firmante'))
        if not identity:
            missing.append(_('identidad del representante legal / firmante'))
        if not self.partner_id.vat:
            missing.append(_('RTN fiscal del deudor principal'))
        if self.partner_id.is_company and not self.contract_buyer_authority:
            missing.append(_('facultades del representante de la empresa'))
        for guarantor in self.guarantor_ids:
            if guarantor.is_company:
                raise ValidationError(_('El aval %s debe registrarse como persona natural para esta plantilla de aval personal.') % guarantor.name)
            if not guarantor.lenka_identity_number:
                missing.append(_('identidad del aval %s') % guarantor.name)
        for guarantee in guarantees:
            if not guarantee.owner_id:
                missing.append(_('propietario de la garantía %s') % guarantee.description)
        if missing:
            raise ValidationError(_('Revise Datos del contrato, Avales y Garantías. Falta: %s.') % '; '.join(missing))
        if not self.schedule_line_ids:
            raise ValidationError(_('Calcule el plan en Tabla de amortización antes de generar el contrato.'))

    def _secured_loan_sections(self):
        self.ensure_one()
        client = self.partner_id
        name, identity = self._secured_loan_signer()
        debtor = bold('EL PRESTATARIO') + ': ' + bold(client.name)
        debtor += ', con RTN ' + bold(client.vat)
        debtor += ', domicilio ' + escape(client.contact_address or '________________') + '. '
        if client.is_company:
            debtor += 'Entidad deudora principal, representada en este acto por ' + bold(name)
            debtor += ', con documento de identidad ' + bold(identity)
            debtor += ', quien firma exclusivamente en nombre de la entidad conforme a las facultades acreditadas mediante: '
            debtor += escape(self.contract_buyer_authority or '') + '. '
            debtor += 'Su calidad de representante legal no lo convierte por sí sola en aval personal.'
        else:
            debtor += 'Con documento de identidad ' + bold(identity)
            debtor += ', comparece en nombre propio y firma como ' + bold('PRESTATARIO') + '.'
        avals = []
        signatures = []
        for guarantor in self.guarantor_ids.sorted('id'):
            avals.append(paragraph(bold('AVAL SOLIDARIO') + ': ' + bold(guarantor.name)
                + ', identidad ' + bold(guarantor.lenka_identity_number) + ', domicilio '
                + escape(guarantor.contact_address or '________________')
                + '. Comparece a título personal, en función distinta de cualquier representación que ejerza.'))
            signatures.append(self._secured_signature(guarantor.name, 'AVAL SOLIDARIO - a título personal', guarantor.lenka_identity_number))
        if avals:
            avals.append(paragraph('Cada ' + bold('AVAL SOLIDARIO')
                + ' declara su voluntad expresa de garantizar solidariamente con '
                + bold('EL PRESTATARIO') + ' el capital efectivamente entregado y pendiente de pago, '
                + 'los intereses ordinarios y la mora expresamente pactados en este contrato y su Anexo 1. '
                + 'Frente al incumplimiento responde personalmente ante ' + bold('EL PRESTAMISTA')
                + ', dentro de esos límites. La firma como representante de la entidad y la firma como aval son independientes. '
                + 'Las modificaciones que amplíen esta obligación requieren la aceptación expresa del aval.'))
        else:
            avals.append(paragraph('No se ha pactado aval personal. El respaldo de esta operación corresponde a las garantías descritas a continuación.'))
        guarantees = []
        for guarantee in self.guarantee_ids.filtered(lambda g: g.state in ('proposed', 'accepted', 'active')).sorted('id'):
            kind = dict(guarantee._fields['guarantee_type'].selection).get(guarantee.guarantee_type, '')
            text = bold(kind) + ': ' + escape(guarantee.description or '')
            text += '. Propietario: ' + bold(guarantee.owner_id.name)
            if guarantee.owner_id.vat:
                text += ', RTN / identidad ' + bold(guarantee.owner_id.vat)
            text += '. Serie / VIN / matrícula: ' + bold(guarantee.serial_reference or '________________')
            text += '. Valor declarado: %s %s; valor de avalúo: %s %s.' % (
                escape(self.currency_id.name), format(guarantee.declared_value, ',.2f'),
                escape(self.currency_id.name), format(guarantee.appraisal_value, ',.2f'))
            guarantees.append(paragraph(text))
        if guarantees:
            guarantees.append(paragraph('Las partes identifican el respaldo ofrecido con los datos anteriores. '
                'Su constitución, aceptación, formalización e inscripción, cuando correspondan, constarán en los documentos del expediente. '
                'La sola descripción del bien en este contrato no sustituye esos documentos ni convierte a su propietario en aval personal.'))
        else:
            guarantees.append(paragraph('No se ha registrado garantía sobre bienes para esta operación. El respaldo corresponde al aval personal expresamente pactado.'))
        seller, seller_id, _payments = self._secured_lender_and_payments()
        primary = self._secured_signature(seller, 'PRESTAMISTA - Inversiones Lenka S. de R. L. de C.V.', seller_id)
        role = ('REPRESENTANTE LEGAL DE ' + client.name + ' - por EL PRESTATARIO') if client.is_company else 'PRESTATARIO - en nombre propio'
        primary += self._secured_signature(name, role, identity)
        return {
            '{{DEUDOR_PRINCIPAL_HTML}}': paragraph(debtor),
            '{{AVALES_SOLIDARIOS_HTML}}': ''.join(avals),
            '{{GARANTIAS_DETALLE_HTML}}': ''.join(guarantees),
            '{{FORMA_PAGO_HTML}}': self._secured_lender_and_payments()[2],
            '{{FIRMAS_PARTES_HTML}}': '<div class="lenka-firmas" style="overflow:hidden;page-break-inside:avoid;margin-top:45px">' + primary + '<div style="clear:both"></div></div>',
            '{{FIRMAS_AVALES_HTML}}': ''.join('<div class="lenka-firmas" style="overflow:hidden;page-break-inside:avoid;margin-top:45px">' + s + '<div style="clear:both"></div></div>' for s in signatures),
        }

    def _secured_signature(self, name, role, identity):
        return ('<div style="float:left;width:48%%;margin-right:2%%;page-break-inside:avoid">'
                '<p style="text-align:left;margin:0 0 3pt">%s</p>'
                '<p style="text-align:left;margin:0 0 3pt">%s</p>'
                '<p style="text-align:left;margin:0 0 3pt">No. de identidad: %s</p></div>') % (
                    bold(name), bold(role), bold(identity))

    def _render_lenka_template(self, template):
        if template.builtin_key != SECURED_KEY:
            return super()._render_lenka_template(template)
        self.ensure_one()
        if template.company_id != self.company_id or template.operation_type != 'loan':
            raise ValidationError(_('Seleccione una plantilla de préstamo de la misma empresa.'))
        self._validate_secured_loan_contract()
        sections = self._secured_loan_sections()
        values = self._template_values()
        lender, lender_id, _payments = self._secured_lender_and_payments()
        values['{{REPRESENTANTE_VENDEDOR}}'] = lender
        values['{{IDENTIDAD_VENDEDOR}}'] = lender_id
        def replace(match):
            token = match.group(0)
            if token in sections:
                return sections[token]
            if token not in values:
                raise ValidationError(_('Variable desconocida en la plantilla: %s') % token)
            return escape(str(values[token]))
        body = re.sub(r'\{\{[A-Z_]+\}\}', replace, template.body_html or '')
        return body + self._contract_schedule_html()
