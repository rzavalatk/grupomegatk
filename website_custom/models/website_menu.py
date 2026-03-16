# -*- coding: utf-8 -*-
from odoo import models


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    def clean_url(self):
        """Compatibilidad Odoo 16→18: la plantilla website.submenu almacenada en
        la BD aún llama submenu.clean_url(). En Odoo 17/18 ese método dejó de
        existir en el modelo base; lo reintroducimos aquí."""
        self.ensure_one()
        url = self.url or '/'
        return url.split('#')[0] or '/'
