
from odoo import models, fields, api
from odoo.exceptions import Warning


class StockHistory(models.TransientModel):
    _name = 'stock.history'
    
   #movimiento_ids = fields.Many2one('stock.quant', string='movimiento')
    name = fields.Char('name')
    quant_id = fields.One2many('stock.quant', 'Quant')
    product_id = fields.Many2one('product.product', 'Product')
    location_id = fields.Many2one('stock.location', 'Location')
    quantity = fields.Float('Quantity')
    date = fields.Datetime('Date')
    user_id = fields.Many2one('res.users', 'User')

    @api.depends('quant_id')
    def _compute_product_id(self):
        for record in self:
            if record.quant_id:
                record.product_id = record.quant_id.product_id

    @api.depends('quant_id')
    def _compute_location_id(self):
        for record in self:
            if record.quant_id:
                record.location_id = record.quant_id.location_id

    @api.model
    def create_history(self, quant_id, quantity):
        self.env['stock.history'].create({
            'quant_id': quant_id,
            'product_id': quant_id.product_id,
            'location_id': quant_id.location_id,
            'quantity': quantity,
            'date': fields.Datetime.now(),
            'user_id': self.env.user.id,
        })


"""class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model_update_fields()
    def write(self, vals):
        res = super(StockQuant, self).write(vals)

        if 'quantity' in vals:
            for quant in self:
                self.env['stock.history'].create_history(quant, quant.quantity)

        return res"""