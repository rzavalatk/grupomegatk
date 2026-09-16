from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ODentalService(models.Model):
    _inherit = "odental.service"

    product_id = fields.Many2one(
        "product.product",
        string="Producto facturable",
        domain="[('type', '=', 'service')]",
        ondelete="restrict",
        help="Producto de servicio que aparecerá en cotizaciones y facturas. O Dental lo crea automáticamente.",
    )
    product_auto_created = fields.Boolean(
        string="Producto creado automáticamente",
        default=False,
        readonly=True,
        copy=False,
    )
    currency_id = fields.Many2one(
        related="organization_id.company_id.currency_id", readonly=True
    )
    price_unit = fields.Monetary(
        string="Precio de referencia",
        currency_field="currency_id",
        help="Precio sugerido del servicio. Podrá ajustarse al preparar el plan de tratamiento.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        services = super().create(vals_list)
        services._ensure_billing_product()
        return services

    def write(self, vals):
        if self.env.context.get("skip_odental_product_sync"):
            return super().write(vals)
        values = dict(vals)
        if "product_id" in values:
            values["product_auto_created"] = False
        result = super().write(values)
        if {"name", "price_unit", "organization_id", "product_id"} & set(values):
            self._ensure_billing_product()
            self.filtered("product_auto_created")._sync_billing_product()
        return result

    def _ensure_billing_product(self):
        for service in self.filtered(lambda item: not item.product_id):
            product = self.env["product.product"].sudo().with_company(
                service.organization_id.company_id
            ).create(
                {
                    "name": service.name,
                    "type": "service",
                    "sale_ok": True,
                    "purchase_ok": False,
                    "list_price": service.price_unit,
                    "company_id": service.organization_id.company_id.id,
                }
            )
            service.with_context(skip_odental_product_sync=True).write(
                {"product_id": product.id, "product_auto_created": True}
            )

    def _sync_billing_product(self):
        for service in self.filtered(lambda item: item.product_id and item.product_auto_created):
            service.product_id.sudo().write(
                {
                    "name": service.name,
                    "list_price": service.price_unit,
                    "company_id": service.organization_id.company_id.id,
                }
            )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for service in self:
            if service.product_id:
                service.price_unit = service.product_id.lst_price

    @api.constrains("product_id", "organization_id")
    def _check_product_company(self):
        for service in self:
            product_company = service.product_id.company_id
            if product_company and product_company != service.organization_id.company_id:
                raise ValidationError("El producto facturable pertenece a otra compañía.")


class ODentalProfessional(models.Model):
    _inherit = "odental.professional"

    billing_company_id = fields.Many2one(
        "res.company",
        string="Compañía para facturación independiente",
        default=lambda self: self.env.company,
        help="Se utiliza cuando el profesional factura con su propia empresa.",
    )


class ODentalClinicalRecord(models.Model):
    _inherit = "odental.clinical.record"

    treatment_plan_ids = fields.One2many(
        "odental.treatment.plan", "clinical_record_id", string="Planes de tratamiento"
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    odental_treatment_plan_id = fields.Many2one(
        "odental.treatment.plan",
        string="Plan de tratamiento O Dental",
        readonly=True,
        copy=False,
        index=True,
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    odental_treatment_line_id = fields.Many2one(
        "odental.treatment.plan.line",
        string="Línea clínica O Dental",
        readonly=True,
        copy=False,
        index=True,
    )
