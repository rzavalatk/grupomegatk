from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ODentalAppointment(models.Model):
    _inherit = "odental.appointment"

    rental_booking_ids = fields.One2many("odental.rental.booking", "appointment_id", string="Reservas de alquiler")
    rental_booking_count = fields.Integer(compute="_compute_rental_booking_count")

    @api.depends("rental_booking_ids")
    def _compute_rental_booking_count(self):
        for appointment in self:
            appointment.rental_booking_count = len(appointment.rental_booking_ids)

    def _sync_rental_booking(self):
        for appointment in self:
            resources = appointment.resource_ids.filtered("is_rentable")
            booking = appointment.rental_booking_ids[:1]
            if not resources:
                if booking and booking.state in {"draft", "reserved"}:
                    booking.action_cancel()
                continue
            providers = resources.mapped("organization_id")
            if len(providers) != 1:
                raise ValidationError("Los recursos alquilados deben pertenecer a un solo propietario por cita.")
            if not booking:
                booking = self.env["odental.rental.booking"].create({
                    "appointment_id": appointment.id,
                    "provider_organization_id": providers.id,
                })
            if appointment.state in {"scheduled", "confirmed"}:
                booking.action_reserve()
            elif appointment.state == "in_progress" and booking.state == "reserved":
                booking.action_start()
            elif appointment.state == "done" and booking.state in {"reserved", "in_progress"}:
                booking.action_complete()
            elif appointment.state in {"cancelled", "no_show"} and booking.state != "completed":
                booking.action_cancel()

    def write(self, vals):
        result = super().write(vals)
        watched = {"state", "resource_ids", "start_datetime", "duration_minutes", "preparation_minutes", "cleaning_minutes"}
        if watched.intersection(vals):
            self._sync_rental_booking()
        return result

    def action_view_rental_booking(self):
        self.ensure_one()
        booking = self.rental_booking_ids[:1]
        if not booking:
            self._sync_rental_booking()
            booking = self.rental_booking_ids[:1]
        if not booking:
            raise UserError("Esta cita no utiliza recursos alquilables.")
        return {
            "type": "ir.actions.act_window", "res_model": "odental.rental.booking",
            "res_id": booking.id, "view_mode": "form", "target": "current",
        }


class SaleOrder(models.Model):
    _inherit = "sale.order"

    odental_rental_booking_id = fields.Many2one(
        "odental.rental.booking", string="Reserva O Dental", readonly=True, copy=False, index=True
    )
    odental_rental_package_id = fields.Many2one(
        "odental.rental.package", string="Paquete O Dental", readonly=True, copy=False, index=True
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    odental_rental_booking_line_id = fields.Many2one(
        "odental.rental.booking.line", string="Cargo de alquiler O Dental", readonly=True, copy=False, index=True
    )
