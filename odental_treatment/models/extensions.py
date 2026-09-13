from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ODentalService(models.Model):
    _inherit = "odental.service"

    product_id = fields.Many2one(
        "product.product",
        string="Producto facturable",
        domain="[('type', '=', 'service')]",
        ondelete="restrict",
    )
    currency_id = fields.Many2one(
        related="organization_id.company_id.currency_id", readonly=True
    )
    price_unit = fields.Monetary(string="Precio de referencia", currency_field="currency_id")

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

