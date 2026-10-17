from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPartnerCompany(TransactionCase):
    def test_active_company_and_explicit_company(self):
        other = self.env['res.company'].create({'name': 'Empresa RTN prueba'})
        Partner = self.env['res.partner'].with_context(no_vat_validation=True)
        partner = Partner.with_company(other).create({'name': 'Cliente en activa'})
        self.assertEqual(partner.company_id, other)
        explicit = Partner.with_company(other).create({'name': 'Cliente explícito', 'company_id': self.env.company.id})
        self.assertEqual(explicit.company_id, self.env.company)

    def test_rtn_independent_per_company_and_duplicate_write(self):
        other = self.env['res.company'].create({'name': 'Otra empresa RTN prueba'})
        Partner = self.env['res.partner'].with_context(no_vat_validation=True)
        first = Partner.create({'name': 'Primero RTN', 'vat': 'RTN-PRUEBA-UNICO'})
        second = Partner.with_company(other).create({'name': 'Segundo RTN', 'vat': first.vat})
        self.assertNotEqual(first.company_id, second.company_id)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Partner.create({'name': 'Duplicado RTN', 'vat': first.vat})
        third = Partner.create({'name': 'Otro RTN'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            third.vat = first.vat
        with self.assertRaises(ValidationError), self.cr.savepoint():
            Partner.create([{'name': 'Lote uno', 'vat': 'RTN-LOTE'}, {'name': 'Lote dos', 'vat': 'RTN-LOTE'}])
