from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    odental_workspace_enabled = fields.Boolean(string='Menú simplificado de O Dental')
    odental_workspace_menu_ids = fields.Many2many(
        'ir.ui.menu', 'odental_workspace_company_menu_rel', 'company_id', 'menu_id',
        string='Aplicaciones del espacio dental', domain=[('parent_id', '=', False)],
        help='Solo simplifica la navegación. No concede ni revoca permisos de acceso.',
    )


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        info = super().session_info()
        info['odental_workspaces'] = {
            company.id: company.sudo().odental_workspace_menu_ids.ids
            for company in self.env.user.company_ids
            if company.sudo().odental_workspace_enabled
        }
        return info
