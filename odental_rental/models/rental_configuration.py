import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ODentalRentalCategory(models.Model):
    _name = "odental.rental.category"
    _description = "Categoría de alquiler O Dental"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    tier = fields.Selection(
        [("standard", "Estándar"), ("premium", "Premium"), ("specialized", "Especializado")],
        required=True, default="standard"
    )
    organization_id = fields.Many2one(
        "odental.organization", string="Organización propietaria", required=True,
        ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    resource_ids = fields.One2many("odental.resource", "rental_category_id", string="Recursos")
    notes = fields.Text()

    _sql_constraints = [
        ("category_code_org_unique", "unique(code, organization_id)", "El código debe ser único por organización."),
    ]


class ODentalResource(models.Model):
    _inherit = "odental.resource"

    is_rentable = fields.Boolean(string="Disponible para alquiler")
    rental_category_id = fields.Many2one(
        "odental.rental.category", string="Categoría tarifaria", ondelete="restrict"
    )

    @api.constrains("is_rentable", "rental_category_id", "organization_id")
    def _check_rental_category(self):
        for resource in self:
            if resource.is_rentable and not resource.rental_category_id:
                raise ValidationError("Un recurso alquilable debe tener categoría tarifaria.")
            if resource.rental_category_id and resource.rental_category_id.organization_id != resource.organization_id:
                raise ValidationError("La categoría debe pertenecer al propietario del recurso.")


class ODentalRentalRate(models.Model):
    _name = "odental.rental.rate"
    _description = "Tarifa de alquiler O Dental"
    _order = "sequence, name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    organization_id = fields.Many2one(
        "odental.organization", string="Organización propietaria", required=True,
        ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    resource_id = fields.Many2one("odental.resource", string="Recurso específico", ondelete="cascade")
    category_id = fields.Many2one("odental.rental.category", string="Categoría", ondelete="cascade")
    billing_basis = fields.Selection(
        [("hour", "Por hora"), ("half_day", "Media jornada"), ("day", "Jornada completa"), ("patient", "Por paciente")],
        required=True, default="hour"
    )
    price = fields.Monetary(required=True, currency_field="currency_id")
    included_minutes = fields.Integer(string="Minutos incluidos", default=60)
    minimum_minutes = fields.Integer(string="Mínimo facturable", default=60)
    increment_minutes = fields.Integer(string="Incremento de cobro", default=30)
    overage_price_per_hour = fields.Monetary(string="Excedente por hora", currency_field="currency_id")
    product_id = fields.Many2one(
        "product.product", string="Producto facturable", required=True,
        domain="[('type', '=', 'service')]", ondelete="restrict"
    )

    @api.constrains(
        "resource_id", "category_id", "organization_id", "price", "included_minutes",
        "minimum_minutes", "increment_minutes", "product_id"
    )
    def _check_rate(self):
        for rate in self:
            if bool(rate.resource_id) == bool(rate.category_id):
                raise ValidationError("La tarifa debe aplicar a un recurso o a una categoría, no a ambos.")
            target_org = rate.resource_id.organization_id or rate.category_id.organization_id
            if target_org != rate.organization_id:
                raise ValidationError("La tarifa y su objetivo deben tener el mismo propietario.")
            if rate.price < 0 or rate.minimum_minutes <= 0 or rate.increment_minutes <= 0:
                raise ValidationError("El precio y los intervalos no son válidos.")
            if rate.billing_basis in {"half_day", "day"} and rate.included_minutes <= 0:
                raise ValidationError("La tarifa plana debe indicar minutos incluidos.")
            if rate.product_id.company_id and rate.product_id.company_id != rate.company_id:
                raise ValidationError("El producto facturable pertenece a otra compañía.")

    def _rounded_hours(self, minutes):
        self.ensure_one()
        billed = max(int(minutes or 0), self.minimum_minutes)
        billed = math.ceil(billed / self.increment_minutes) * self.increment_minutes
        return billed / 60.0

    def amount_for_minutes(self, minutes):
        self.ensure_one()
        minutes = max(int(minutes or 0), 0)
        if self.billing_basis == "patient":
            return self.price
        if self.billing_basis in {"half_day", "day"} and minutes <= self.included_minutes:
            return self.price
        if self.billing_basis in {"half_day", "day"}:
            extra = minutes - self.included_minutes
            hourly = self.overage_price_per_hour or (self.price * 60.0 / self.included_minutes)
            return self.price + self._rounded_hours(extra) * hourly
        return self._rounded_hours(minutes) * self.price

    def overage_amount(self, minutes):
        self.ensure_one()
        if minutes <= 0:
            return 0.0
        billed = math.ceil(minutes / self.increment_minutes) * self.increment_minutes
        return billed / 60.0 * (self.overage_price_per_hour or self.price)


class ODentalRentalPackageType(models.Model):
    _name = "odental.rental.package.type"
    _description = "Tipo de paquete de alquiler O Dental"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    organization_id = fields.Many2one(
        "odental.organization", string="Organización propietaria", required=True,
        ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    resource_id = fields.Many2one("odental.resource", string="Recurso específico", ondelete="cascade")
    category_id = fields.Many2one("odental.rental.category", string="Categoría", ondelete="cascade")
    purchased_minutes = fields.Integer(string="Minutos comprados", required=True, default=300)
    bonus_minutes = fields.Integer(string="Minutos de bonificación", default=0)
    validity_days = fields.Integer(string="Vigencia en días", required=True, default=30)
    price = fields.Monetary(required=True, currency_field="currency_id")
    product_id = fields.Many2one(
        "product.product", string="Producto facturable", required=True,
        domain="[('type', '=', 'service')]", ondelete="restrict"
    )

    @api.constrains(
        "resource_id", "category_id", "organization_id", "purchased_minutes",
        "bonus_minutes", "validity_days", "price", "product_id"
    )
    def _check_package_type(self):
        for package_type in self:
            if bool(package_type.resource_id) == bool(package_type.category_id):
                raise ValidationError("El paquete debe aplicar a un recurso o a una categoría.")
            target_org = package_type.resource_id.organization_id or package_type.category_id.organization_id
            if target_org != package_type.organization_id:
                raise ValidationError("El paquete y su objetivo deben tener el mismo propietario.")
            if package_type.purchased_minutes <= 0 or package_type.bonus_minutes < 0:
                raise ValidationError("Los minutos del paquete no son válidos.")
            if package_type.validity_days <= 0 or package_type.price < 0:
                raise ValidationError("La vigencia y el precio no son válidos.")
            if package_type.product_id.company_id and package_type.product_id.company_id != package_type.company_id:
                raise ValidationError("El producto facturable pertenece a otra compañía.")

    def applies_to(self, resource):
        self.ensure_one()
        return self.resource_id == resource or (not self.resource_id and self.category_id == resource.rental_category_id)
