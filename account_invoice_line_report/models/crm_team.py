from odoo import models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    def _allow_multi_company_team_read(self):
        return self.env.user.has_group(
            "account_invoice_line_report.group_crm_team_multi_company_read"
        )

    def _search(self, domain, offset=0, limit=None, order=None):
        if self._allow_multi_company_team_read():
            # Bypass record rules only for users explicitly allowed by group.
            return super(CrmTeam, self.sudo())._search(
                domain,
                offset=offset,
                limit=limit,
                order=order,
            )
        return super()._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
        )

    def check_access_rule(self, operation):
        if (
            operation == "read"
            and (
                (
                    self.env.context.get("allow_account_invoice_line_report_team_read")
                    and self.env.user.has_group("account.group_account_user")
                )
                or self._allow_multi_company_team_read()
            )
        ):
            return
        return super().check_access_rule(operation)
