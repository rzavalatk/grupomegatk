from datetime import datetime
from decimal import Decimal

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BCHCurrencyService(models.AbstractModel):
    _name = "megatk.bch.currency.service"
    _description = "MEGATK BCH currency update service"

    _API = "https://bchapi-am.azure-api.net/api/v1/indicadores/620/cifras?formato=Json"
    _AUTHORIZED_COMPANY_IDS = (8, 9, 11)

    def _companies(self):
        companies = self.env["res.company"].browse(self._AUTHORIZED_COMPANY_IDS).exists()
        if set(companies.ids) != set(self._AUTHORIZED_COMPANY_IDS):
            raise UserError(_("No se encontraron las tres compañías autorizadas (8, 9 y 11)."))
        bad = companies.filtered(lambda company: company.currency_id.name != "HNL")
        if bad:
            raise UserError(
                _("Solo se permiten compañías con moneda HNL: %s")
                % ", ".join(bad.mapped("name"))
            )
        return companies.sorted("id")

    def _quote(self):
        key = self.env["ir.config_parameter"].sudo().get_param(
            "megatk_bch_currency.api_key"
        )
        if not key:
            raise UserError(_("Falta la llave BCH en Parámetros del sistema."))
        try:
            response = requests.get(
                self._API,
                headers={"clave": key},
                timeout=20,
            )
            response.raise_for_status()
            rows = response.json()
        except (requests.RequestException, ValueError) as error:
            raise UserError(_("BCH no respondió correctamente: %s") % error) from error

        rows = rows if isinstance(rows, list) else rows.get("data", [])
        quotes = []
        for row in rows:
            if int(row.get("IndicadorId") or 0) != 620:
                continue
            try:
                quote_date = datetime.fromisoformat(
                    str(row.get("Fecha") or "").replace("Z", "+00:00")
                ).date()
                value = Decimal(str(row.get("Valor") or "").replace(",", ""))
                if value > 0:
                    quotes.append((quote_date, value))
            except (TypeError, ValueError, ArithmeticError):
                continue

        if not quotes:
            raise UserError(_("BCH no devolvió una tasa de venta USD utilizable."))

        quote_date, hnl_per_usd = max(quotes)
        if not Decimal("15") <= hnl_per_usd <= Decimal("45"):
            raise UserError(
                _("La tasa BCH (%s HNL/USD) no pasó la validación.")
                % hnl_per_usd
            )
        return quote_date, hnl_per_usd

    def preview_usd_rate(self):
        quote_date, hnl_per_usd = self._quote()
        return {
            "date": quote_date,
            "hnl_per_usd": float(hnl_per_usd),
            "usd_per_hnl": float(Decimal(1) / hnl_per_usd),
            "companies": self._companies(),
        }

    def update_usd_rates(self):
        preview = self.preview_usd_rate()
        usd = self.env.ref("base.USD")
        Rate = self.env["res.currency.rate"].sudo()
        results = []

        for company in preview["companies"]:
            rate = Rate.search(
                [
                    ("currency_id", "=", usd.id),
                    ("company_id", "=", company.id),
                    ("name", "=", preview["date"]),
                ],
                limit=1,
            )
            values = {"rate": preview["usd_per_hnl"]}
            if rate:
                action = (
                    "sin cambios"
                    if abs(rate.rate - preview["usd_per_hnl"]) < 1e-12
                    else "actualizada"
                )
                if action == "actualizada":
                    rate.write(values)
            else:
                Rate.create(
                    {
                        **values,
                        "name": preview["date"],
                        "currency_id": usd.id,
                        "company_id": company.id,
                    }
                )
                action = "creada"
            results.append("%s: %s" % (company.name, action))

        return preview, results

    def cron_update_usd_rates(self):
        return self.update_usd_rates()


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def action_bch_preview(self):
        self.ensure_one()
        if self.name != "USD":
            raise UserError(_("La consulta BCH está disponible únicamente para USD."))

        preview = self.env["megatk.bch.currency.service"].preview_usd_rate()
        wizard = self.env["megatk.bch.currency.preview"].create(
            {
                "currency_id": self.id,
                "quote_date": preview["date"],
                "hnl_per_usd": preview["hnl_per_usd"],
                "usd_per_hnl": preview["usd_per_hnl"],
                "company_names": "\\n".join(preview["companies"].mapped("name")),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Tasa de venta BCH"),
            "res_model": "megatk.bch.currency.preview",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }


class BCHCurrencyPreview(models.TransientModel):
    _name = "megatk.bch.currency.preview"
    _description = "Vista previa de tasa BCH"

    currency_id = fields.Many2one("res.currency", readonly=True, required=True)
    quote_date = fields.Date(string="Fecha BCH", readonly=True, required=True)
    hnl_per_usd = fields.Float(
        string="HNL por USD (Venta BCH)", digits=(16, 6), readonly=True
    )
    usd_per_hnl = fields.Float(
        string="USD por HNL (valor interno Odoo)", digits=(16, 12), readonly=True
    )
    company_names = fields.Text(string="Empresas autorizadas", readonly=True)

    def action_apply(self):
        self.ensure_one()
        preview, results = self.env[
            "megatk.bch.currency.service"
        ].update_usd_rates()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Tasas BCH actualizadas"),
                "message": _("Venta BCH: L %(rate).4f por USD — %(date)s\\n%(results)s")
                % {
                    "rate": preview["hnl_per_usd"],
                    "date": preview["date"],
                    "results": "\\n".join(results),
                },
                "type": "success",
                "sticky": True,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
