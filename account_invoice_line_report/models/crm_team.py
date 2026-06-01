from odoo import models


class CrmTeam(models.Model):
    _inherit = "crm.team"
    
    # Este modelo ya no necesita lógica especial
    # La seguridad se maneja completamente en el método compute del reporte
