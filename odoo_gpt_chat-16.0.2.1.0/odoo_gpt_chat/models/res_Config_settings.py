from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    chat_bot_id = fields.Char("Chat bot ID", config_parameter="odoo_gpt_chat.chat_bot_id")
    show_chat_bot = fields.Boolean("Show chat Bot", config_parameter="odoo_gpt_chat.show_chat_bot")
    show_chat_bot_f = fields.Boolean("Show chat Bot in frontend", config_parameter="odoo_gpt_chat.show_chat_bot_f")
    show_chat_bot_b = fields.Boolean("Show chat Bot in backend", config_parameter="odoo_gpt_chat.show_chat_bot_b")