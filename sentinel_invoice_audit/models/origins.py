from odoo import models

from .context import origin


class IrCron(models.Model):
    _inherit = 'ir.cron'

    def _callback(self, cron_name, server_action_id):
        with origin('scheduled_job', self.env.uid, {'cron_id': self.id, 'server_action_id': server_action_id}):
            return super()._callback(cron_name, server_action_id)


class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    def _process(self, records, domain_post=None):
        with origin('automation', self.env.uid, {'automation_ids': self.ids}):
            return super()._process(records, domain_post=domain_post)
