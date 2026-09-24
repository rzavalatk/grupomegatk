from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class ResPartnerLenkaMobile(models.Model):
    _inherit = 'res.partner'

    lenka_mobile_enabled = fields.Boolean(
        string='Acceso App Financiero Lenka',
        tracking=True,
        help='Habilita a este cliente para consultar su informacion financiera desde la app Lenka.',
    )
    lenka_mobile_enabled_date = fields.Datetime(string='Acceso Lenka habilitado el', readonly=True)
    lenka_mobile_user_id = fields.Many2one(
        'res.users',
        string='Usuario App Lenka',
        compute='_compute_lenka_mobile_user',
    )

    def _compute_lenka_mobile_user(self):
        Users = self.env['res.users'].sudo()
        for partner in self:
            user = Users.search([('partner_id', '=', partner.id)], limit=1)
            partner.lenka_mobile_user_id = user

    def action_enable_lenka_mobile(self):
        group = self.env.ref('lenka_financiero.group_lenka_mobile_client')
        portal_group = self.env.ref('base.group_portal')
        Users = self.env['res.users'].sudo()
        for partner in self:
            if not partner.email:
                raise ValidationError(_('El cliente debe tener un correo electronico antes de habilitar la app Lenka.'))
            user = Users.search([('partner_id', '=', partner.id)], limit=1)
            if not user:
                user = Users.with_context(no_reset_password=True).create({
                    'name': partner.name,
                    'login': partner.email,
                    'email': partner.email,
                    'partner_id': partner.id,
                    'groups_id': [(6, 0, [portal_group.id, group.id])],
                })
            else:
                user.write({'groups_id': [(4, portal_group.id), (4, group.id)]})
            partner.write({
                'lenka_mobile_enabled': True,
                'lenka_mobile_enabled_date': fields.Datetime.now(),
            })
        return True

    def action_disable_lenka_mobile(self):
        group = self.env.ref('lenka_financiero.group_lenka_mobile_client')
        for partner in self:
            user = self.env['res.users'].sudo().search([('partner_id', '=', partner.id)], limit=1)
            if user:
                user.write({'groups_id': [(3, group.id)]})
            partner.lenka_mobile_enabled = False
        return True
