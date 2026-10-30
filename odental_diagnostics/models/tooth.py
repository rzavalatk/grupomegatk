from odoo import api, fields, models
from odoo.osv import expression


_PRIMARY_ADA = {
    "5": "EDCBA", "6": "FGHIJ", "7": "ONMLK", "8": "PQRST",
}


def ada_designation(fdi):
    """Return the ADA Universal designation, retaining FDI as the stable key."""
    if not fdi or len(fdi) != 2 or not fdi.isdigit():
        return False
    quadrant, position = fdi[0], int(fdi[1])
    if quadrant in "1234" and 1 <= position <= 8:
        return str({"1": 9 - position, "2": 8 + position,
                    "3": 25 - position, "4": 24 + position}[quadrant])
    if quadrant in _PRIMARY_ADA and 1 <= position <= 5:
        return _PRIMARY_ADA[quadrant][position - 1]
    return False


class ODentalTooth(models.Model):
    _name = "odental.tooth"
    _description = "Pieza dental FDI"
    _order = "sequence, code"

    code = fields.Char(string="Código FDI", required=True, index=True)
    ada_code = fields.Char(string="Código ADA", compute="_compute_ada_code", store=True, index=True)
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

    @api.depends("code")
    def _compute_ada_code(self):
        for tooth in self:
            tooth.ada_code = ada_designation(tooth.code)

    @api.depends("code", "ada_code")
    @api.depends_context("odental_notation")
    def _compute_display_name(self):
        notation = self.env.context.get("odental_notation", "fdi")
        for tooth in self:
            tooth.display_name = (tooth.ada_code if notation == "ada" else tooth.code) or tooth.code

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if not name:
            return super().name_search(name=name, args=args, operator=operator, limit=limit)
        domain = expression.AND([list(args or []), expression.OR([
            [("code", operator, name)],
            [("ada_code", operator, name)],
            [("name", operator, name)],
        ])])
        records = self.search(domain, limit=limit)
        return [(tooth.id, tooth.display_name) for tooth in records]

