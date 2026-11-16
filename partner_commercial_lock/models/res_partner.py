from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = "res.partner"

    commercial_assignment_locked = fields.Boolean(
        string="Reasignación de comercial bloqueada",
        compute="_compute_commercial_assignment_locked",
        compute_sudo=False,
    )

    @api.depends_context("uid")
    def _compute_commercial_assignment_locked(self):
        locked = self.env.user.has_group(
            "partner_commercial_lock.group_no_reassign_partner_commercial"
        )
        for partner in self:
            partner.commercial_assignment_locked = locked

    def write(self, vals):
        # Check before super(): a rejected batch must not write any record or
        # any of the other submitted fields. Do not trust client context flags.
        if "user_id" in vals and self.env.user.has_group(
            "partner_commercial_lock.group_no_reassign_partner_commercial"
        ):
            requested_user_id = vals["user_id"] or False
            if any(partner.user_id.id != requested_user_id for partner in self):
                raise AccessError(_(
                    "No tiene permiso para cambiar o quitar el comercial de "
                    "un contacto. Solicite la reasignación a Administración."
                ))
        return super().write(vals)
