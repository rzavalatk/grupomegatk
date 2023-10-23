# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime

class Logs(models.Model):
    _name="logs.model"
    
    name = fields.Char("Nambre")
    register = fields.Text()
    
    

class Gastos(models.Model):
    _inherit="account.move"
    
    @api.multi
    def assert_balanced(self):
        today = datetime.today()
        text = ""
        text += "////////////Context: "+str(self.env.context)+"//////////////"
        text += "\n"
        text += "////////////Context: "+str(self.ids)+"//////////////"
        
        self.env['logs.model'].create({
            'name': self._name +" : "+ str(today),
            'register': text
        })
        res = super(Gastos,self).assert_balanced()
    
        return res
    
    # @api.model
    # def create(self, vals):
    #     res = super(Gastos,self).create(vals)
    #     # self.env.context.get
    #     text = ""
    #     text += "////////////Create: "+str(res)+"//////////////"
    #     text += "\n"
    #     text += "////////////Vals: "+str(vals)+"//////////////"
    #     text += "\n"
    #     text += "////////////Context: "+str(self.env.context)+"//////////////"
        
    #     self.env['logs.model'].create({
    #         'name': self._name,
    #         'register': text
    #     })
        
    #     return res