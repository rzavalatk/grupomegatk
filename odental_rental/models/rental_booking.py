import math

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalRentalBooking(models.Model):
    _name = "odental.rental.booking"
    _description = "Reserva de alquiler O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    appointment_id = fields.Many2one("odental.appointment", string="Cita", required=True, ondelete="restrict", index=True)
    renter_organization_id = fields.Many2one(related="appointment_id.organization_id", store=True, index=True)
    provider_organization_id = fields.Many2one(
        "odental.organization", string="Organización propietaria", required=True,
        ondelete="restrict", index=True
    )
    professional_id = fields.Many2one(related="appointment_id.professional_id", store=True, index=True)
    start_datetime = fields.Datetime(related="appointment_id.blocking_start", store=True, index=True)
    end_datetime = fields.Datetime(related="appointment_id.blocking_end", store=True, index=True)
    actual_start = fields.Datetime(tracking=True)
    actual_end = fields.Datetime(tracking=True)
    company_id = fields.Many2one(related="provider_organization_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    line_ids = fields.One2many("odental.rental.booking.line", "booking_id", string="Recursos")
    amount_gross = fields.Monetary(compute="_compute_amounts", store=True)
    amount_package = fields.Monetary(compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(compute="_compute_amounts", store=True)
    state = fields.Selection(
        [("draft", "Borrador"), ("reserved", "Reservada"), ("in_progress", "En uso"),
         ("completed", "Liquidada"), ("cancelled", "Cancelada")],
        required=True, default="draft", tracking=True, index=True
    )
    sale_order_id = fields.Many2one("sale.order", string="Cotización de cargos", readonly=True, copy=False)

    _sql_constraints = [
        ("appointment_unique", "unique(appointment_id)", "Solo puede existir una reserva de alquiler por cita."),
    ]

    @api.depends("line_ids.gross_amount", "line_ids.package_credit_amount", "line_ids.amount_total")
    def _compute_amounts(self):
        for booking in self:
            booking.amount_gross = sum(booking.line_ids.mapped("gross_amount"))
            booking.amount_package = sum(booking.line_ids.mapped("package_credit_amount"))
            booking.amount_total = sum(booking.line_ids.mapped("amount_total"))

    def write(self, vals):
        protected = {"state", "sale_order_id"}
        if protected.intersection(vals) and not self.env.context.get("odental_rental_transition"):
            raise UserError("Utilice las acciones de la reserva para cambiar su estado o liquidación.")
        if {"actual_start", "actual_end"}.intersection(vals) and any(
            booking.state in {"completed", "cancelled"} for booking in self
        ):
            raise UserError("Las horas reales de una reserva cerrada son inmutables.")
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.rental.booking") or "Nuevo"
        return super().create(vals_list)

    @api.constrains("appointment_id", "provider_organization_id")
    def _check_provider(self):
        for booking in self:
            providers = booking.appointment_id.resource_ids.filtered("is_rentable").mapped("organization_id")
            if providers and (len(providers) != 1 or providers != booking.provider_organization_id):
                raise ValidationError("El propietario de la reserva debe coincidir con los recursos alquilados.")

    def _find_rate(self, resource):
        self.ensure_one()
        common = [("active", "=", True), ("organization_id", "=", resource.organization_id.id)]
        rates = self.env["odental.rental.rate"]
        return (
            rates.search(common + [("resource_id", "=", resource.id)], limit=1)
            or rates.search(common + [("category_id", "=", resource.rental_category_id.id)], limit=1)
        )

    def _find_package(self, resource):
        self.ensure_one()
        today = fields.Date.context_today(self)
        packages = self.env["odental.rental.package"].search([
            ("state", "=", "active"),
            ("provider_organization_id", "=", resource.organization_id.id),
            ("renter_organization_id", "=", self.renter_organization_id.id),
            ("professional_id", "=", self.professional_id.id),
            ("expiration_date", ">=", today),
            ("remaining_minutes", ">", 0),
        ], order="expiration_date, id")
        return packages.filtered(lambda package: package.package_type_id.applies_to(resource))[:1]

    def action_sync_resources(self):
        for booking in self:
            if booking.state in {"in_progress", "completed", "cancelled"}:
                raise UserError("No se pueden cambiar recursos después de iniciar o cerrar la reserva.")
            resources = booking.appointment_id.resource_ids.filtered("is_rentable")
            if not resources:
                raise ValidationError("La cita no contiene recursos marcados para alquiler.")
            providers = resources.mapped("organization_id")
            if len(providers) != 1:
                raise ValidationError("Todos los recursos alquilados deben tener el mismo propietario.")
            booking.provider_organization_id = providers.id
            existing = {line.resource_id.id: line for line in booking.line_ids}
            for resource in resources:
                rate = booking._find_rate(resource)
                if not rate:
                    raise ValidationError(f"No existe una tarifa activa para {resource.name}.")
                package = booking._find_package(resource) if rate.billing_basis == "hour" else False
                values = {"rate_id": rate.id, "package_id": package.id if package else False}
                if resource.id in existing:
                    existing[resource.id].write(values)
                else:
                    values.update({"booking_id": booking.id, "resource_id": resource.id})
                    self.env["odental.rental.booking.line"].create(values)
            booking.line_ids.filtered(lambda line: line.resource_id not in resources).unlink()
        return True

    def action_reserve(self):
        for booking in self:
            if booking.state not in {"draft", "reserved"}:
                raise UserError("La reserva ya no puede confirmarse.")
            booking.action_sync_resources()
            booking.with_context(odental_rental_transition=True).write({"state": "reserved"})

    def action_start(self):
        for booking in self:
            if booking.state != "reserved":
                raise UserError("Solo una reserva confirmada puede iniciar.")
            booking.with_context(odental_rental_transition=True).write({"state": "in_progress", "actual_start": booking.actual_start or booking.start_datetime})

    def action_complete(self):
        for booking in self:
            if booking.state not in {"reserved", "in_progress"}:
                raise UserError("Solo una reserva confirmada o en uso puede liquidarse.")
            start = booking.actual_start or booking.start_datetime
            end = booking.actual_end or booking.end_datetime
            if not start or not end or end <= start:
                raise ValidationError("Las horas reales de uso no son válidas.")
            booking.with_context(odental_rental_transition=True).write({"actual_start": start, "actual_end": end})
            minutes = max(math.ceil((end - start).total_seconds() / 60.0), 1)
            for line in booking.line_ids:
                line._settle(minutes)
            booking.with_context(odental_rental_transition=True).write({"state": "completed"})

    def action_cancel(self):
        for booking in self:
            if booking.state == "completed":
                raise UserError("Una reserva liquidada no puede cancelarse.")
            booking.with_context(odental_rental_transition=True).write({"state": "cancelled"})

    def _ensure_partner(self):
        self.ensure_one()
        if self.professional_id.partner_id:
            return self.professional_id.partner_id
        partner = self.env["res.partner"].create({"name": self.professional_id.name, "company_id": False})
        self.professional_id.partner_id = partner
        return partner

    def action_create_quotation(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede crear la cotización.")
        if self.state != "completed":
            raise UserError("La reserva debe estar liquidada antes de cotizar cargos.")
        if self.sale_order_id:
            return self.action_view_quotation()
        billable = self.line_ids.filtered(lambda line: line.amount_total > 0)
        if not billable:
            raise UserError("La reserva no tiene cargos pendientes fuera del paquete.")
        pricelist = self.env["product.pricelist"].with_company(self.company_id).search([
            ("currency_id", "=", self.currency_id.id),
            "|", ("company_id", "=", False), ("company_id", "=", self.company_id.id),
        ], limit=1)
        if not pricelist:
            raise ValidationError("Configure una tarifa de venta en la moneda del propietario.")
        order_lines = []
        for line in billable:
            product = line.rate_id.product_id
            order_lines.append((0, 0, {
                "product_id": product.id, "name": f"{line.resource_id.name} — {self.name}",
                "product_uom_qty": 1, "product_uom": product.uom_id.id,
                "price_unit": line.amount_total, "odental_rental_booking_line_id": line.id,
            }))
        order = self.env["sale.order"].with_company(self.company_id).create({
            "partner_id": self._ensure_partner().id, "company_id": self.company_id.id,
            "pricelist_id": pricelist.id, "origin": self.name,
            "odental_rental_booking_id": self.id, "order_line": order_lines,
        })
        self.with_context(odental_rental_transition=True).write({"sale_order_id": order.id})
        return self.action_view_quotation()

    def action_view_quotation(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError("Esta reserva todavía no tiene cotización.")
        return {
            "type": "ir.actions.act_window", "res_model": "sale.order",
            "res_id": self.sale_order_id.id, "view_mode": "form", "target": "current",
        }


class ODentalRentalBookingLine(models.Model):
    _name = "odental.rental.booking.line"
    _description = "Recurso de reserva O Dental"
    _order = "id"

    booking_id = fields.Many2one("odental.rental.booking", required=True, ondelete="cascade", index=True)
    provider_organization_id = fields.Many2one(related="booking_id.provider_organization_id", store=True, index=True)
    renter_organization_id = fields.Many2one(related="booking_id.renter_organization_id", store=True, index=True)
    professional_id = fields.Many2one(related="booking_id.professional_id", store=True, index=True)
    resource_id = fields.Many2one("odental.resource", required=True, ondelete="restrict", index=True)
    rate_id = fields.Many2one("odental.rental.rate", required=True, ondelete="restrict")
    package_id = fields.Many2one("odental.rental.package", string="Paquete aplicado", ondelete="restrict")
    currency_id = fields.Many2one(related="booking_id.currency_id", store=True)
    billable_minutes = fields.Integer(readonly=True)
    covered_minutes = fields.Integer(string="Minutos cubiertos", readonly=True)
    overage_minutes = fields.Integer(string="Minutos de excedente", readonly=True)
    gross_amount = fields.Monetary(string="Valor bruto", currency_field="currency_id", readonly=True)
    package_credit_amount = fields.Monetary(string="Cubierto por paquete", currency_field="currency_id", readonly=True)
    amount_total = fields.Monetary(string="Cargo pendiente", currency_field="currency_id", readonly=True)

    _sql_constraints = [
        ("booking_resource_unique", "unique(booking_id, resource_id)", "El recurso solo puede aparecer una vez por reserva."),
    ]

    def write(self, vals):
        protected = {"billable_minutes", "covered_minutes", "overage_minutes", "gross_amount", "package_credit_amount", "amount_total"}
        if protected.intersection(vals) and not self.env.context.get("odental_rental_settlement"):
            raise UserError("Los importes solo pueden cambiar durante la liquidación controlada.")
        return super().write(vals)

    @api.constrains("resource_id", "rate_id", "package_id")
    def _check_configuration(self):
        for line in self:
            if line.resource_id.organization_id != line.booking_id.provider_organization_id:
                raise ValidationError("El recurso no pertenece al propietario de la reserva.")
            if line.rate_id.organization_id != line.booking_id.provider_organization_id:
                raise ValidationError("La tarifa no pertenece al propietario de la reserva.")
            if line.rate_id.resource_id and line.rate_id.resource_id != line.resource_id:
                raise ValidationError("La tarifa específica no corresponde al recurso.")
            if line.rate_id.category_id and line.rate_id.category_id != line.resource_id.rental_category_id:
                raise ValidationError("La tarifa no corresponde a la categoría del recurso.")
            if line.package_id:
                if line.rate_id.billing_basis != "hour":
                    raise ValidationError("Los paquetes de minutos solo se aplican a tarifas por hora.")
                if line.package_id.professional_id != line.booking_id.professional_id:
                    raise ValidationError("El paquete pertenece a otro profesional.")
                if line.package_id.renter_organization_id != line.booking_id.renter_organization_id:
                    raise ValidationError("El paquete pertenece a otra organización arrendataria.")
                if line.package_id.provider_organization_id != line.booking_id.provider_organization_id:
                    raise ValidationError("El paquete pertenece a otro proveedor de espacios.")
                if not line.package_id.package_type_id.applies_to(line.resource_id):
                    raise ValidationError("El paquete no cubre este recurso.")

    def _settle(self, minutes):
        self.ensure_one()
        gross = self.rate_id.amount_for_minutes(minutes)
        covered = self.package_id._consume(minutes, self) if self.package_id else 0
        overage = max(minutes - covered, 0)
        amount = self.rate_id.overage_amount(overage) if self.package_id else gross
        self.with_context(odental_rental_settlement=True).write({
            "billable_minutes": minutes, "covered_minutes": covered,
            "overage_minutes": overage, "gross_amount": gross,
            "package_credit_amount": max(gross - amount, 0.0), "amount_total": amount,
        })
