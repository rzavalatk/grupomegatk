# -*- coding: utf-8 -*-

from odoo import models


class WebsiteMenu(models.Model):
    """
     Heredando el menú del sitio web.

     Esta clase hereda del modelo 'website.menu' y extiende su
     Funcionalidad para calcular la visibilidad del menú.
     elemento basado en el valor de 'odoo_website_helpdesk.helpdesk_menu_show'
     parámetro de configuración.

     Atributos:
        _inherit (cadena): el nombre del modelo que se hereda.
    """
    _inherit = "website.menu"

    def _compute_visible(self):
        """
        Calcule la visibilidad del elemento del menú.

        Este método se utiliza para determinar si el elemento del menú debe ser
        visible u oculto según el valor del
        Parámetro de configuración 'odoo_website_helpdesk.helpdesk_menu_show'.

        Devoluciones:
            Ninguno

        Efectos secundarios:
            Establece el campo 'is_visible' del registro del elemento del menú en Verdadero o
            Falso en consecuencia.
        """
        super()._compute_visible()
        show_menu_header = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.helpdesk_menu_show')
        for menu in self:
            if menu.name == 'Helpdesk' and show_menu_header is False:
                menu.is_visible = False
            if menu.name == 'Helpdesk' and show_menu_header is True:
                menu.is_visible = True
