import base64
import re

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestApprovedEquipmentContract(TransactionCase):
    """Use fictitious parties; do not upload the approved source's personal data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.client = cls.env['res.partner'].create({
            'name': 'Cliente ficticio <equipo> & asociados', 'is_company': True,
        })
        cls.product = cls.env['product.product'].create({'name': 'Equipo de prueba'})

    def _operation(self, currency='HNL'):
        money = self.env['res.currency'].with_context(active_test=False).search([('name', '=', currency)], limit=1)
        money.active = True
        op = self.env['lenka.financial.operation'].create({
            'partner_id': self.client.id, 'product_id': self.product.id,
            'company_id': self.company.id, 'currency_id': money.id,
            'principal_amount': 10000, 'down_payment': 1000,
            'interest_rate': 3, 'rate_period': 'monthly', 'term_months': 12,
            'operation_type': 'financing', 'is_quote': False,
            'contract_seller_representative': 'Firmante vendedor de prueba',
            'contract_buyer_representative': 'Firmante comprador de prueba',
            'contract_equipment_serial': 'SERIE-PRUEBA', 'contract_isv_amount': 1000,
            'late_fee_rate': 2,
        })
        op.action_generate_schedule()
        return op

    def test_approved_contract_hnl_and_usd_without_accounts(self):
        for code in ('HNL', 'USD'):
            op = self._operation(code)
            op.action_use_approved_equipment_contract()
            op.action_generate_contract_documents()
            doc = op.generated_document_ids.filtered(lambda d: d.template_id == op.equipment_contract_template_id)
            self.assertEqual(len(doc), 1)
            self.assertIn('9,000.00', doc.rendered_html)
            self.assertIn('Anexo: plan de pagos', doc.rendered_html)
            self.assertIn(code, doc.rendered_html)
            self.assertIn('SERIE-PRUEBA', doc.rendered_html)
            self.assertIn('Firmante comprador de prueba', doc.rendered_html)
            self.assertNotIn('<equipo>', doc.rendered_html)
            self.assertFalse(re.search(r'\{\{[A-Z_]+\}\}', doc.rendered_html))
            self.assertNotIn('Conzuma', doc.rendered_html)
            before = doc.rendered_html
            original_template = doc.template_id.body_html
            op.action_generate_contract_documents()
            self.assertEqual(len(op.generated_document_ids.filtered(lambda d: d.template_id == doc.template_id)), 1)
            doc.template_id.body_html = '<p>Contenido cambiado después de generar</p>'
            self.assertEqual(doc.rendered_html, before)
            doc.template_id.body_html = original_template
            report = self.env.ref('lenka_financiero.action_report_lenka_generated_document')
            html, _ = report._render_qweb_html(report.report_name, docids=doc.ids)
            self.assertIn('Rúbrica VENDEDOR', html.decode())
            self.assertIn('Rúbrica COMPRADOR', html.decode())
            self.assertIn('Firmas de las partes', html.decode())

    def test_template_preserves_company_edits_and_does_not_duplicate(self):
        model = self.env['lenka.contract.template']
        one = model._approved_equipment_template(self.company)
        one.body_html = '<p>Texto personalizado</p>'
        two = model._approved_equipment_template(self.company)
        self.assertEqual(one, two)
        self.assertIn('Texto personalizado', two.body_html)
        two.active = False
        with self.assertRaises(ValidationError):
            model._approved_equipment_template(self.company)

    def test_cross_company_contract_rejected(self):
        op = self._operation()
        other = self.env['res.company'].create({'name': 'Otra empresa prueba contrato'})
        template = self.env['lenka.contract.template'].create({
            'company_id': other.id, 'name': 'Contrato ajeno', 'body_html': '<p>Ajeno</p>',
            'operation_type': 'financing',
        })
        with self.assertRaises(ValidationError):
            op._render_lenka_template(template)

    def test_quote_and_missing_schedule_block_generation(self):
        op = self._operation()
        op.action_use_approved_equipment_contract()
        op.is_quote = True
        with self.assertRaises(ValidationError):
            op.action_generate_contract_documents()
        op.is_quote = False
        op.schedule_line_ids.unlink()
        with self.assertRaises(ValidationError):
            op._render_lenka_template(op.equipment_contract_template_id)

    def test_sign_requires_attachment_and_freezes_regeneration(self):
        op = self._operation()
        op.action_use_approved_equipment_contract()
        op.action_generate_contract_documents()
        doc = op.generated_document_ids.filtered(lambda d: d.document_type == 'contract')
        with self.assertRaises(ValidationError):
            doc.action_mark_signed()
        doc.write({'signed_filename': 'prueba.pdf', 'signed_file': base64.b64encode(b'PRUEBA SIN VALIDEZ')})
        doc.action_mark_signed()
        self.assertTrue(op.contract_signed)
        with self.assertRaises(ValidationError):
            doc.action_render()

    def test_token_like_customer_name_is_literal(self):
        op = self._operation()
        op.partner_id.name = '{{MONTO}} <script>alert(1)</script>'
        template = self.env['lenka.contract.template'].create({
            'company_id': self.company.id, 'name': 'Escapado',
            'body_html': '<p>{{CLIENTE}} / {{MONTO}}</p>',
        })
        rendered = op._render_lenka_template(template)
        self.assertIn('{{MONTO}}', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertIn('10,000.00', rendered)

    def test_first_generation_loads_approved_template_without_demo(self):
        self.env['lenka.contract.template'].search([
            ('company_id', '=', self.company.id), ('document_type', '=', 'contract'),
        ]).write({'active': False})
        op = self._operation()
        op.action_generate_contract_documents()
        self.assertEqual(op.equipment_contract_template_id.builtin_key, 'equipment_20261009')
        self.assertTrue(op.generated_document_ids)

    def test_isv_cannot_exceed_price(self):
        op = self._operation()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.contract_isv_amount = 10001
