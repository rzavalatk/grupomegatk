# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_persisted_template_id(self):
        self.ensure_one()
        if self._origin and self._origin.id:
            return self._origin.id
        return self.id if isinstance(self.id, int) else False

    lot_reference_id = fields.Many2one(
        "stock.lot",
        string="Lote de referencia",
        help="Selecciona un lote para cargar su fecha de caducidad y calcular automáticamente los días.",
    )
    valid_lot_ids = fields.Many2many(
        "stock.lot",
        compute="_compute_valid_lot_ids",
        string="Lotes validos",
    )
    expiration_date_helper = fields.Date(
        string="Fecha de caducidad sugerida",
        compute="_compute_lot_dates_preview",
        readonly=True,
    )

    def _get_lot_expiry_field_map(self):
        lot_fields = self.env["stock.lot"]._fields
        return {
            "life": "life_date" if "life_date" in lot_fields else ("expiration_date" if "expiration_date" in lot_fields else False),
            "use": "use_date" if "use_date" in lot_fields else False,
            "removal": "removal_date" if "removal_date" in lot_fields else False,
            "alert": "alert_date" if "alert_date" in lot_fields else False,
        }

    @api.depends("product_variant_ids", "product_variant_ids.write_date", "company_id")
    def _compute_valid_lot_ids(self):
        lot_model = self.env["stock.lot"]
        lot_fields = lot_model._fields
        field_map = self._get_lot_expiry_field_map()
        qty_field = "product_qty" if "product_qty" in lot_fields else ("quantity" if "quantity" in lot_fields else False)
        now_dt = fields.Datetime.now()

        for product in self:
            variant_ids = product.product_variant_ids.ids
            if not variant_ids:
                product.valid_lot_ids = False
                continue

            domain = [("product_id", "in", variant_ids)]
            if product.company_id:
                domain += ["|", ("company_id", "=", False), ("company_id", "=", product.company_id.id)]

            lots = lot_model.search(domain)

            if qty_field:
                lots = lots.filtered(lambda lot: (lot[qty_field] or 0) > 0)

            life_field = field_map["life"]
            if life_field:
                lots = lots.filtered(
                    lambda lot: not lot[life_field]
                    or fields.Datetime.to_datetime(lot[life_field]) >= now_dt
                )

            product.valid_lot_ids = lots

    @api.depends("lot_reference_id", "lot_reference_id.write_date")
    def _compute_lot_dates_preview(self):
        field_map = self._get_lot_expiry_field_map()
        for product in self:
            product_tmpl_id = product._get_persisted_template_id()
            product.expiration_date_helper = False

            lot = product.lot_reference_id
            if not lot:
                continue
            if product_tmpl_id and lot.product_id.product_tmpl_id.id != product_tmpl_id:
                continue

            life_field = field_map["life"]
            if life_field and lot[life_field]:
                product.expiration_date_helper = fields.Datetime.to_datetime(lot[life_field]).date()

    @api.onchange("lot_reference_id")
    def _onchange_lot_reference_id(self):
        from datetime import datetime, time as time_module
        field_map = self._get_lot_expiry_field_map()
        for product in self:
            product_tmpl_id = product._get_persisted_template_id()
            lot = product.lot_reference_id
            if not lot:
                product.expiration_time = False
                product.use_time = False
                product.removal_time = False
                product.alert_time = False
                continue
            if lot.id not in product.valid_lot_ids.ids:
                product.lot_reference_id = False
                return {
                    "warning": {
                        "title": "Lote invalido",
                        "message": "Solo se permiten lotes con stock y no vencidos.",
                    }
                }
            if product_tmpl_id and lot.product_id.product_tmpl_id.id != product_tmpl_id:
                product.lot_reference_id = False
                _logger.warning(
                    "id del producto persistido: %s, id del producto actual: %s, id del lote: %s, id del producto del lote: %s",
                    product_tmpl_id,
                    product.id,
                    lot.id,
                    lot.product_id.product_tmpl_id.id,
                )
                return {
                    "warning": {
                        "title": "Lote invalido",
                        "message": "El lote seleccionado no pertenece a este producto.",
                    }
                }
            life_field = field_map["life"]
            if life_field and lot[life_field]:
                life_dt = lot[life_field]
                if isinstance(life_dt, str):
                    life_dt = fields.Datetime.from_string(life_dt)
                today = fields.Date.context_today(product)
                if isinstance(today, str):
                    today = fields.Date.from_string(today)
                life_date_only = datetime.combine(life_dt.date() if hasattr(life_dt, 'date') else life_dt, time_module.min).date()
                days_to_expiry = (life_date_only - today).days
                product.expiration_time = max(0, days_to_expiry)
                product.use_time = 0
                product.removal_time = 0
                product.alert_time = 0

