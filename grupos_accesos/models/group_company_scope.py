from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ResGroups(models.Model):
    _inherit = "res.groups"

    restriction_company_ids = fields.Many2many(
        "res.company",
        "res_groups_restriction_company_rel",
        "group_id",
        "company_id",
        string="Empresa",
        help="Empresas donde este grupo aplica su restriccion.",
    )


class ResUsers(models.Model):
    _inherit = "res.users"

    def _company_restriction_active_for_group(self, group_xmlid, company=None):
        self.ensure_one()
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        if not group:
            return False

        company = company or self.env.company
        return bool(group.restriction_company_ids and company in group.restriction_company_ids)

    def _has_group_for_company_restriction(self, group_xmlid, company=None):
        self.ensure_one()
        if not self.has_group(group_xmlid):
            return False
        return self._company_restriction_active_for_group(group_xmlid, company=company)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def action_apply_inventory(self):
        user = self.env.user
        company = self.env.company

        if (
            user._company_restriction_active_for_group(
                "grupos_accesos.group_inventory_adjustments_access", company=company
            )
            and not user.has_group("grupos_accesos.group_inventory_adjustments_access")
        ):
            raise AccessError(_(
                "No tiene permisos para aplicar ajustes de inventario en esta empresa."
            ))

        return super().action_apply_inventory()


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    def _check_scrap_access_by_company(self):
        user = self.env.user
        restricted_scraps = self.filtered(
            lambda scrap: user._company_restriction_active_for_group(
                "grupos_accesos.group_inventory_scrap_access",
                company=scrap.company_id or self.env.company,
            )
            and not user.has_group("grupos_accesos.group_inventory_scrap_access")
        )
        if restricted_scraps:
            raise AccessError(_(
                "No tiene permisos para operar desechos de inventario en esta empresa."
            ))

    @api.model_create_multi
    def create(self, vals_list):
        scraps = super().create(vals_list)
        scraps._check_scrap_access_by_company()
        return scraps

    def write(self, vals):
        self._check_scrap_access_by_company()
        return super().write(vals)

    def action_validate(self):
        self._check_scrap_access_by_company()
        return super().action_validate()
    
    
    
    