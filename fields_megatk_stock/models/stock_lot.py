# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta

from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    expiration_date_helper = fields.Date(
        string="Fecha de caducidad sugerida",
        help="Ayuda visual para calcular fechas de lote usando la fecha elegida.",
    )

    def _get_lot_expiry_field_map(self):
        lot_fields = self._fields
        return {
            "life": "life_date" if "life_date" in lot_fields else ("expiration_date" if "expiration_date" in lot_fields else False),
            "use": "use_date" if "use_date" in lot_fields else False,
            "removal": "removal_date" if "removal_date" in lot_fields else False,
            "alert": "alert_date" if "alert_date" in lot_fields else False,
        }

    @api.onchange("expiration_date_helper", "product_id")
    def _onchange_expiration_date_helper(self):
        field_map = self._get_lot_expiry_field_map()
        for lot in self:
            if not lot.expiration_date_helper:
                continue

            helper_date = lot.expiration_date_helper
            if isinstance(helper_date, str):
                helper_date = fields.Date.from_string(helper_date)

            life_dt = datetime.combine(helper_date, time.min)

            if field_map["life"]:
                lot[field_map["life"]] = life_dt

            product_tmpl = lot.product_id.product_tmpl_id
            if not product_tmpl:
                continue

            if field_map["use"]:
                lot[field_map["use"]] = life_dt - timedelta(days=getattr(product_tmpl, "use_time", 0) or 0)
            if field_map["removal"]:
                lot[field_map["removal"]] = life_dt - timedelta(days=getattr(product_tmpl, "removal_time", 0) or 0)
            if field_map["alert"]:
                lot[field_map["alert"]] = life_dt - timedelta(days=getattr(product_tmpl, "alert_time", 0) or 0)

    @api.onchange("life_date", "expiration_date")
    def _onchange_life_date_sync_helper(self):
        field_map = self._get_lot_expiry_field_map()
        for lot in self:
            life_field = field_map["life"]
            life_value = lot[life_field] if life_field else False

            if life_value:
                lot.expiration_date_helper = fields.Datetime.to_datetime(life_value).date()
            else:
                lot.expiration_date_helper = False