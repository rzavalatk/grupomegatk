from odoo import api, fields, models


class PrintProductLabelLine(models.TransientModel):
    _name = "print.product.label.line"
    _description = 'Línea con los datos de una etiqueta de producto'
    _order = 'sequence'

    sequence = fields.Integer(default=900)
    selected = fields.Boolean(string='Imprimir', default=True)
    wizard_id = fields.Many2one(comodel_name='print.product.label')
    product_id = fields.Many2one(comodel_name='product.product', required=True)
    barcode = fields.Char(compute='_compute_barcode')
    qty_initial = fields.Integer(string='Cantidad Inicial', default=1)
    qty = fields.Integer(string='Cantidad de etiquetas', default=1)
    custom_value = fields.Char(help="Este campo puede rellenarse manualmente para utilizarlo en plantillas de etiquetas.")
    company_id = fields.Many2one(comodel_name='res.company', compute='_compute_company_id')
    partner_id = fields.Many2one(comodel_name='res.partner', readonly=False)

    @api.depends('wizard_id.company_id')
    def _compute_company_id(self):
        for label in self:
            label.company_id = label.wizard_id.company_id.id \
                if label.wizard_id.company_id else self.env.user.company_id.id

    @api.depends('product_id')
    def _compute_barcode(self):
        for label in self:
            label.barcode = label.product_id.barcode

    def action_plus_qty(self):
        self.ensure_one()
        if not self.qty:
            self.update({'selected': True})
        self.update({'qty': self.qty + 1})

    def action_minus_qty(self):
        self.ensure_one()
        if self.qty > 0:
            self.update({'qty': self.qty - 1})
            if not self.qty:
                self.update({'selected': False})
