from odoo import fields, models


class ODentalTooth(models.Model):
    _name = "odental.tooth"
    _description = "Pieza dental FDI"
    _order = "sequence, code"

    code = fields.Char(string="Código FDI", required=True, index=True)
    name = fields.Char(required=True)
    dentition = fields.Selection(
        [("permanent", "Permanente"), ("primary", "Temporal")],
        required=True,
        index=True,
    )
    quadrant = fields.Selection(
        [(str(number), f"Cuadrante {number}") for number in range(1, 9)],
        required=True,
        index=True,
    )
    tooth_type = fields.Selection(
        [
            ("incisor", "Incisivo"),
            ("canine", "Canino"),
            ("premolar", "Premolar"),
            ("molar", "Molar"),
        ],
        required=True,
    )
    sequence = fields.Integer(default=10, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("tooth_code_unique", "unique(code)", "El código FDI debe ser único."),
    ]

    def name_get(self):
        return [(tooth.id, f"{tooth.code} - {tooth.name}") for tooth in self]

