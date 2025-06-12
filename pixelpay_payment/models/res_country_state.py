from odoo import api, fields, models
import pycountry


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    code_3166_2 = fields.Char(
        string="State Code ISO 3166-2",
        help="ISO 3166-2 code for the state",
    )

    @api.depends("code")
    def _compute_codes(self):
        for state in self:
            c = False
            for country_type in ["countries", "historic_countries"]:
                try:
                    c = getattr(pycountry, country_type).get(alpha_2=state.country_id.code + '-' + state.code)
                except KeyError:
                    c = getattr(pycountry, country_type).get(alpha2=state.code)
                if c:
                    break
            if c:
                state.code_alpha3 = getattr(c, "alpha_3", getattr(c, "alpha3", False))
                state.code_numeric = c.numeric
            else:
                state.code_alpha3 = False
                state.code_numeric = False