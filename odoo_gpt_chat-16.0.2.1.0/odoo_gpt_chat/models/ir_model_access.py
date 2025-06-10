
from odoo import api, fields, models, tools,_

class ir_model_access(models.Model):
    _inherit = 'ir.model.access'

    user_id = fields.Many2one('res.users', string='User')

    @api.model
    def default_get(self, fields_list):
        result = super(ir_model_access, self).default_get(fields_list)
        if self._context.get('is_whisperchat_access'):
            result['group_id'] = self.env.ref('odoo_gpt_chat.group_bot_user').id
        pass
        return result