from odoo import api, models, fields


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    order_menu = fields.Boolean(default=False, string='Order Menu Alphabets')

    @api.model
    def get_values(self):
        """ Obtener valores para los campos en la configuración y asignarles el valor."""
        res = super(Settings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        order_menu = params.get_param('order_menu', default=False)
        res.update(
            order_menu=order_menu,
        )
        return res

    def set_values(self):
        """ guardar los valores de los campos en la configuración"""
        super(Settings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("order_menu",  self.order_menu)

    @api.onchange('order_menu')
    def onchange_order_menu(self):
        asc_order_menu = self.env['ir.config_parameter'].sudo().get_param('order_menu') or False
        sqno = 1
        if asc_order_menu:
            # menus = self.env['ir.ui.menu'].sudo().search([('parent_id','=', False),('name', 'not in', ['Apps', 'Settings', 'Dashboard'])], order='name ASC')
            menus = self.env['ir.ui.menu'].sudo().search(['&',('parent_id','=', False),('name','not in',('Apps','Settings','Dashboard'))])
            for menu in menus:
                if not menu.order_changed:
                    menu.recent_menu_sequence = menu.sequence
                    menu.sequence = sqno
                    menu.order_changed = True
                    sqno += 1
        else:
            menus = self.env['ir.ui.menu'].search([('parent_id', '=', False), ('name', 'not in', ('Apps', 'Settings', 'Dashboard'))])

            for menu in menus:
                if menu.order_changed:
                    menu.sequence = menu.recent_menu_sequence
                    menu.recent_menu_sequence = 0
                    menu.order_changed = False

        return False

