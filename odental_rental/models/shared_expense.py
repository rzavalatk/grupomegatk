from datetime import datetime, time

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ODentalSharedExpense(models.Model):
    _name = "odental.shared.expense"
    _description = "Gasto compartido O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    description = fields.Char(required=True, tracking=True)
    provider_organization_id = fields.Many2one(
        "odental.organization", string="Organización administradora", required=True,
        ondelete="restrict", index=True
    )
    company_id = fields.Many2one(related="provider_organization_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    period_start = fields.Date(required=True)
    period_end = fields.Date(required=True)
    amount = fields.Monetary(required=True, currency_field="currency_id", tracking=True)
    allocation_method = fields.Selection(
        [
            ("equal", "Partes iguales"),
            ("percentage", "Porcentaje personalizado"),
            ("fixed", "Monto fijo por profesional"),
            ("hours", "Horas utilizadas"),
            ("patients", "Pacientes atendidos"),
            ("usage", "Valor de recursos utilizados"),
            ("hybrid", "Cuota fija más uso"),
            ("manual", "Asignación manual excepcional"),
        ],
        required=True, default="equal", tracking=True
    )
    hybrid_fixed_pool = fields.Monetary(
        string="Fondo fijo", currency_field="currency_id",
        help="Parte del gasto híbrido que se divide en cuotas iguales; el saldo se distribuye por horas."
    )
    line_ids = fields.One2many("odental.shared.expense.line", "expense_id", string="Distribución")
    allocated_amount = fields.Monetary(compute="_compute_allocated", store=True, currency_field="currency_id")
    difference_amount = fields.Monetary(compute="_compute_allocated", store=True, currency_field="currency_id")
    state = fields.Selection(
        [("draft", "Borrador"), ("calculated", "Calculado"), ("approved", "Aprobado"), ("cancelled", "Cancelado")],
        required=True, default="draft", tracking=True, index=True
    )
    notes = fields.Text()

    @api.depends("amount", "line_ids.allocated_amount")
    def _compute_allocated(self):
        for expense in self:
            expense.allocated_amount = sum(expense.line_ids.mapped("allocated_amount"))
            expense.difference_amount = expense.amount - expense.allocated_amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.shared.expense") or "Nuevo"
        return super().create(vals_list)

    @api.constrains("period_start", "period_end", "amount", "hybrid_fixed_pool")
    def _check_values(self):
        for expense in self:
            if expense.period_end < expense.period_start:
                raise ValidationError("El período final no puede ser anterior al inicial.")
            if expense.amount < 0:
                raise ValidationError("El gasto no puede ser negativo.")
            if expense.hybrid_fixed_pool < 0 or expense.hybrid_fixed_pool > expense.amount:
                raise ValidationError("El fondo fijo híbrido debe estar entre cero y el total del gasto.")

    def write(self, vals):
        protected = {"provider_organization_id", "period_start", "period_end", "amount", "allocation_method", "hybrid_fixed_pool", "line_ids"}
        if "state" in vals and not self.env.context.get("odental_expense_transition"):
            raise UserError("Utilice las acciones del gasto para cambiar su estado.")
        for expense in self:
            if expense.state == "approved" and protected.intersection(vals):
                raise UserError("Un reparto aprobado es inmutable. Cancele y cree uno nuevo.")
        return super().write(vals)

    def _period_domain(self):
        self.ensure_one()
        start = datetime.combine(self.period_start, time.min)
        end = datetime.combine(self.period_end, time.max)
        return [("start_datetime", ">=", start), ("start_datetime", "<=", end)]

    def _completed_bookings(self):
        self.ensure_one()
        return self.env["odental.rental.booking"].search([
            ("provider_organization_id", "=", self.provider_organization_id.id),
            ("state", "=", "completed"),
        ] + self._period_domain())

    def action_load_professionals(self):
        for expense in self:
            if expense.state == "approved":
                raise UserError("El reparto aprobado no puede modificarse.")
            professionals = expense._completed_bookings().mapped("professional_id")
            existing = expense.line_ids.mapped("professional_id")
            commands = [(0, 0, {"professional_id": professional.id}) for professional in professionals - existing]
            if commands:
                expense.write({"line_ids": commands})

    def _driver_by_professional(self, method):
        self.ensure_one()
        bookings = self._completed_bookings()
        result = {}
        for professional in self.line_ids.mapped("professional_id"):
            owned = bookings.filtered(lambda booking: booking.professional_id == professional)
            if method == "patients":
                result[professional.id] = float(len(owned))
            elif method == "usage":
                result[professional.id] = sum(owned.mapped("amount_gross"))
            else:
                result[professional.id] = sum(owned.line_ids.mapped("billable_minutes")) / 60.0
        return result

    def action_calculate(self):
        for expense in self:
            if expense.state == "approved":
                raise UserError("El reparto aprobado no puede recalcularse.")
            if not expense.line_ids:
                expense.action_load_professionals()
            if not expense.line_ids:
                raise ValidationError("Agregue profesionales o complete reservas dentro del período.")
            method = expense.allocation_method
            count = len(expense.line_ids)
            amounts = {}
            drivers = {}
            if method == "equal":
                amounts = {line.id: expense.amount / count for line in expense.line_ids}
            elif method == "percentage":
                if abs(sum(expense.line_ids.mapped("percentage")) - 100.0) > 0.01:
                    raise ValidationError("Los porcentajes deben sumar 100 %.")
                amounts = {line.id: expense.amount * line.percentage / 100.0 for line in expense.line_ids}
            elif method in {"fixed", "manual"}:
                field_name = "fixed_amount" if method == "fixed" else "manual_amount"
                values = [getattr(line, field_name) for line in expense.line_ids]
                if abs(sum(values) - expense.amount) > 0.01:
                    raise ValidationError("Los montos ingresados deben sumar el total del gasto.")
                amounts = {line.id: getattr(line, field_name) for line in expense.line_ids}
            else:
                driver_method = "hours" if method == "hybrid" else method
                drivers = expense._driver_by_professional(driver_method)
                total_driver = sum(drivers.values())
                if total_driver <= 0:
                    raise ValidationError("No hay actividad registrada para calcular este reparto.")
                variable_pool = expense.amount
                fixed_each = 0.0
                if method == "hybrid":
                    variable_pool -= expense.hybrid_fixed_pool
                    fixed_each = expense.hybrid_fixed_pool / count
                amounts = {
                    line.id: fixed_each + variable_pool * drivers.get(line.professional_id.id, 0.0) / total_driver
                    for line in expense.line_ids
                }
            rounded = []
            accumulated = 0.0
            for index, line in enumerate(expense.line_ids):
                amount = amounts[line.id]
                if index == count - 1:
                    amount = expense.amount - accumulated
                else:
                    amount = expense.currency_id.round(amount)
                    accumulated += amount
                rounded.append((line, amount))
            for line, amount in rounded:
                line.write({
                    "driver_value": drivers.get(line.professional_id.id, 0.0),
                    "allocated_amount": amount,
                })
            expense.with_context(odental_expense_transition=True).write({"state": "calculated"})

    def action_approve(self):
        for expense in self:
            if expense.state != "calculated":
                raise UserError("Calcule el reparto antes de aprobarlo.")
            if not expense.currency_id.is_zero(expense.difference_amount):
                raise ValidationError("La distribución no coincide con el total del gasto.")
            expense.with_context(odental_expense_transition=True).write({"state": "approved"})

    def action_cancel(self):
        self.with_context(odental_expense_transition=True).write({"state": "cancelled"})


class ODentalSharedExpenseLine(models.Model):
    _name = "odental.shared.expense.line"
    _description = "Línea de gasto compartido O Dental"
    _order = "id"

    expense_id = fields.Many2one("odental.shared.expense", required=True, ondelete="cascade", index=True)
    provider_organization_id = fields.Many2one(related="expense_id.provider_organization_id", store=True, index=True)
    professional_id = fields.Many2one("odental.professional", required=True, ondelete="restrict", index=True)
    currency_id = fields.Many2one(related="expense_id.currency_id", store=True)
    percentage = fields.Float(string="Porcentaje")
    fixed_amount = fields.Monetary(string="Monto fijo", currency_field="currency_id")
    manual_amount = fields.Monetary(string="Monto manual", currency_field="currency_id")
    driver_value = fields.Float(string="Base de reparto", readonly=True)
    allocated_amount = fields.Monetary(string="Monto asignado", currency_field="currency_id", readonly=True)
    notes = fields.Char()

    _sql_constraints = [
        ("expense_professional_unique", "unique(expense_id, professional_id)", "Cada profesional solo puede aparecer una vez en el reparto."),
    ]

    @api.constrains("percentage", "fixed_amount", "manual_amount")
    def _check_nonnegative(self):
        for line in self:
            if line.percentage < 0 or line.fixed_amount < 0 or line.manual_amount < 0:
                raise ValidationError("Los valores de distribución no pueden ser negativos.")

    @api.model_create_multi
    def create(self, vals_list):
        expenses = self.env["odental.shared.expense"].browse(
            [vals.get("expense_id") for vals in vals_list if vals.get("expense_id")]
        )
        if any(expense.state == "approved" for expense in expenses):
            raise UserError("No se pueden agregar líneas a un reparto aprobado.")
        return super().create(vals_list)

    def write(self, vals):
        if any(line.expense_id.state == "approved" for line in self):
            raise UserError("Las líneas de un reparto aprobado son inmutables.")
        return super().write(vals)

    def unlink(self):
        if any(line.expense_id.state == "approved" for line in self):
            raise UserError("Las líneas de un reparto aprobado son inmutables.")
        return super().unlink()
