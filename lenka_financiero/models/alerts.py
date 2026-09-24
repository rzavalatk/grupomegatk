from odoo import api, fields, models, _


class ResCompanyLenkaAlerts(models.Model):
    _inherit = 'res.company'

    lenka_alert_days_before_due = fields.Integer(
        string='Lenka: Dias anticipacion cuota',
        default=5,
    )
    lenka_alert_days_before_maturity = fields.Integer(
        string='Lenka: Dias anticipacion vencimiento',
        default=15,
    )


class ResConfigSettingsLenkaAlerts(models.TransientModel):
    _inherit = 'res.config.settings'

    lenka_alert_days_before_due = fields.Integer(
        related='company_id.lenka_alert_days_before_due', readonly=False
    )
    lenka_alert_days_before_maturity = fields.Integer(
        related='company_id.lenka_alert_days_before_maturity', readonly=False
    )


class LenkaAlertAutomation(models.AbstractModel):
    _name = 'lenka.alert.automation'
    _description = 'Automatizacion de Alertas Lenka'

    @api.model
    def _activity_exists(self, model_name, res_id, summary):
        model = self.env['ir.model']._get(model_name)
        return bool(self.env['mail.activity'].search_count([
            ('res_model_id', '=', model.id),
            ('res_id', '=', res_id),
            ('summary', '=', summary),
        ]))

    @api.model
    def _create_activity(self, record, summary, note, deadline):
        if self._activity_exists(record._name, record.id, summary):
            return
        self.env['mail.activity'].create({
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': summary,
            'note': note,
            'date_deadline': deadline,
            'user_id': record.create_uid.id or self.env.user.id,
            'res_model_id': self.env['ir.model']._get(record._name).id,
            'res_id': record.id,
        })

    @api.model
    def _cron_lenka_alerts(self):
        today = fields.Date.context_today(self)

        operations = self.env['lenka.financial.operation'].search([
            ('state', '=', 'active'),
            ('is_quote', '=', False),
        ])
        for operation in operations:
            company = operation.company_id
            due_alert_days = max(company.lenka_alert_days_before_due, 0)
            maturity_alert_days = max(company.lenka_alert_days_before_maturity, 0)

            for line in operation.schedule_line_ids:
                if line.payment_state == 'paid' or not line.date:
                    continue
                if line.date < today:
                    summary = _('Lenka: Cuota vencida')
                    note = _(
                        'La operacion %s del cliente %s tiene la cuota #%s vencida desde %s. '
                        'Monto pendiente: %s %s.'
                    ) % (
                        operation.name, operation.partner_id.display_name,
                        line.sequence, line.date, line.amount_due,
                        operation.currency_id.name,
                    )
                    self._create_activity(operation, summary, note, today)
                elif line.date <= fields.Date.add(today, days=due_alert_days):
                    summary = _('Lenka: Cuota proxima a vencer')
                    note = _(
                        'La operacion %s del cliente %s tiene la cuota #%s con vencimiento %s. '
                        'Monto pendiente: %s %s.'
                    ) % (
                        operation.name, operation.partner_id.display_name,
                        line.sequence, line.date, line.amount_due,
                        operation.currency_id.name,
                    )
                    self._create_activity(operation, summary, note, line.date)

            future_lines = operation.schedule_line_ids.filtered(lambda l: l.date)
            if future_lines:
                final_date = max(future_lines.mapped('date'))
                if today <= final_date <= fields.Date.add(today, days=maturity_alert_days):
                    summary = _('Lenka: Operacion proxima a finalizar')
                    note = _(
                        'La operacion %s del cliente %s tiene vencimiento final el %s.'
                    ) % (operation.name, operation.partner_id.display_name, final_date)
                    self._create_activity(operation, summary, note, final_date)

        investments = self.env['lenka.investment'].search([
            ('state', 'in', ('active', 'matured')),
        ])
        for investment in investments:
            if not investment.maturity_date:
                continue
            days = max(investment.company_id.lenka_alert_days_before_maturity, 0)
            if today <= investment.maturity_date <= fields.Date.add(today, days=days):
                summary = _('Lenka: Deposito proximo a vencer')
                note = _(
                    'El deposito %s de %s vence el %s. Capital vigente: %s %s. '
                    'Tasa contractual: %s%% %s.'
                ) % (
                    investment.name, investment.partner_id.display_name,
                    investment.maturity_date, investment.outstanding_principal,
                    investment.currency_id.name, investment.passive_rate,
                    dict(investment._fields['rate_period'].selection).get(investment.rate_period),
                )
                self._create_activity(investment, summary, note, investment.maturity_date)

        return True
