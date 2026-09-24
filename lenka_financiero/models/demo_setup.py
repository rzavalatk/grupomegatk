from odoo import fields, models, _


class LenkaDemoSetup(models.TransientModel):
    _name = 'lenka.demo.setup'
    _description = 'Preparar Demo Financiero Lenka'

    name = fields.Char(default='Preparar demo Lenka', readonly=True)

    def action_prepare_demo(self):
        self.ensure_one()

        Partner = self.env['res.partner'].sudo()
        Product = self.env['product.product'].sudo()
        Operation = self.env['lenka.financial.operation'].sudo()
        Investment = self.env['lenka.investment'].sudo()

        client = Partner.search([('email', '=', 'cliente.demo@lenka.test')], limit=1)
        if not client:
            client = Partner.create({
                'name': 'Cliente Demo Financiamiento Lenka',
                'email': 'cliente.demo@lenka.test',
                'phone': '9999-0001',
            })

        guarantor = Partner.search([('email', '=', 'aval.demo@lenka.test')], limit=1)
        if not guarantor:
            guarantor = Partner.create({
                'name': 'Aval Demo Lenka',
                'email': 'aval.demo@lenka.test',
                'phone': '9999-0002',
            })

        bank = Partner.search([('name', '=', 'Banco Demo Lenka')], limit=1) or Partner.create({'name': 'Banco Demo Lenka'})
        card_issuer = Partner.search([('name', '=', 'Emisor Tarjeta Empresarial Demo')], limit=1) or Partner.create({'name': 'Emisor Tarjeta Empresarial Demo'})

        investor = Partner.search([('email', '=', 'inversionista.demo@lenka.test')], limit=1)
        if not investor:
            investor = Partner.create({
                'name': 'Inversionista Demo Lenka',
                'email': 'inversionista.demo@lenka.test',
                'phone': '9999-0003',
            })

        product = Product.search([('name', '=', 'Vending Machine Demo MORAK')], limit=1)
        if not product:
            product = Product.create({
                'name': 'Vending Machine Demo MORAK',
                'type': 'consu',
                'list_price': 150000.0,
            })

        financing = Operation.search([
            ('notes', '=', 'Escenario demo: financiamiento con 10% de prima y cuota nivelada.')
        ], limit=1)
        if not financing:
            financing = Operation.create({
                'is_quote': False,
                'partner_id': client.id,
                'guarantor_ids': [(6, 0, guarantor.ids)],
                'operation_type': 'financing',
                'product_id': product.id,
                'principal_amount': 150000.0,
                'down_payment': 15000.0,
                'interest_rate': 3.0,
                'rate_period': 'monthly',
                'term_months': 24,
                'calculation_method': 'level',
                'state': 'review',
                'notes': 'Escenario demo: financiamiento con 10% de prima y cuota nivelada.',
            })
            financing.action_generate_schedule()
            self.env['lenka.funding.line'].sudo().create([
                {
                    'operation_id': financing.id,
                    'source_type': 'bank_loan',
                    'partner_id': bank.id,
                    'reference': 'Prestamo bancario demo 15% anual',
                    'amount': 80000.0,
                    'cost_rate': 15.0,
                    'cost_period': 'annual',
                },
                {
                    'operation_id': financing.id,
                    'source_type': 'own',
                    'reference': 'Capital propio demo',
                    'amount': 35000.0,
                    'cost_rate': 0.0,
                    'cost_period': 'annual',
                },
                {
                    'operation_id': financing.id,
                    'source_type': 'credit_card',
                    'partner_id': card_issuer.id,
                    'reference': 'Tarjeta empresarial demo',
                    'amount': 20000.0,
                    'cost_rate': 3.5,
                    'cost_period': 'monthly',
                },
            ])
            self.env['lenka.guarantee'].sudo().create({
                'operation_id': financing.id,
                'guarantee_type': 'equipment',
                'owner_id': client.id,
                'description': 'Vending Machine Demo MORAK financiada',
                'declared_value': 150000.0,
                'state': 'accepted',
            })

        interest_only = Operation.search([
            ('notes', '=', 'Escenario demo: pago mensual de intereses y capital al vencimiento.')
        ], limit=1)
        if not interest_only:
            interest_only = Operation.create({
                'is_quote': False,
                'partner_id': client.id,
                'operation_type': 'loan',
                'principal_amount': 100000.0,
                'down_payment': 0.0,
                'interest_rate': 2.5,
                'rate_period': 'monthly',
                'term_months': 12,
                'calculation_method': 'interest_only',
                'state': 'review',
                'notes': 'Escenario demo: pago mensual de intereses y capital al vencimiento.',
            })
            interest_only.action_generate_schedule()

        lease = Operation.search([
            ('notes', '=', 'Escenario demo: arrendamiento con opcion de compra del 5%.')
        ], limit=1)
        if not lease:
            lease = Operation.create({
                'is_quote': False,
                'partner_id': client.id,
                'operation_type': 'lease',
                'product_id': product.id,
                'principal_amount': 150000.0,
                'down_payment': 15000.0,
                'interest_rate': 3.0,
                'rate_period': 'monthly',
                'term_months': 36,
                'calculation_method': 'level',
                'residual_purchase_percent': 5.0,
                'state': 'review',
                'notes': 'Escenario demo: arrendamiento con opcion de compra del 5%.',
            })
            lease.action_generate_schedule()

        investment = Investment.search([
            ('notes', '=', 'Escenario demo: 1.5% mensual; retiro anticipado recalcula retroactivamente al 1% mensual.')
        ], limit=1)
        if not investment:
            investment = Investment.create({
                'partner_id': investor.id,
                'investment_type': 'fixed',
                'principal_amount': 100000.0,
                'passive_rate': 1.5,
                'early_withdrawal_rate': 1.0,
                'rate_period': 'monthly',
                'start_date': fields.Date.add(fields.Date.context_today(self), months=-3),
                'term_months': 12,
                'capitalization': 'monthly',
                'state': 'draft',
                'contract_reference': 'DEMO-INV-001',
                'notes': 'Escenario demo: 1.5% mensual; retiro anticipado recalcula retroactivamente al 1% mensual.',
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Demo Lenka preparado'),
                'message': _('Se crearon/verificaron los escenarios demo de financiamiento, prestamo, arrendamiento e inversion.'),
                'type': 'success',
                'sticky': False,
            },
        }
