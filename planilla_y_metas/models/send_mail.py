# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.exceptions import Warning


class Mails(models.Model):
    _inherit = "hr.employee.equipo.madrugador"
    
    def _state(self):
        send_metas = True
        for item in self.employe_ids:
            if item.state_email == 0:
                send_metas = False
        if send_metas:
            comfirm_metas = True
            for item in self.employe_ids:
                if item.state == 'procces':
                    comfirm_metas = False
            if comfirm_metas:
                self.state = 'result'
            else:
                self.state = 'confirm' 
        else:
            self.state = 'metas'
                
             
        
    
    state = fields.Selection([
        ('metas','Por Enviar Metas'),
        ('confirm','Por Confirmar'),
        ('result','Por Enviar Resultados'),
    ],string='Estado',readonly=True, compute=_state)
    
    
    def send_metas_email(self):
        menos_de_100 = []
        for item in self.employe_ids:
            if item._point_totals() != False:
                menos_de_100.append(item.name)
        if len(menos_de_100) > 0:
            employees = ""
            for item in menos_de_100:
                 employees += item+", "
            raise Warning(f"El(s) empleado(s): {employees} no tienen los 100 puntos asignados.")
        else:
            for item in self.employe_ids:
                if item.state_email == 0:  
                    item.send_mentas()
                    
    
    def confirm_eval_metas(self):
        falta_eval = []
        for item in self.employe_ids:
            if item.review_state_metas() == False:
                falta_eval.append(item.name)
        if len(falta_eval) > 0:
            employees = ""
            for item in falta_eval:
                 employees += item+", "
            raise Warning(f"El(s) empleado(s): {employees} le(s) falta(n) que le(s) evaluen metas.")
        else:
            for item in self.employe_ids:
                    item.state_done('state')
                    
    
    def send_result(self):
        for item in self.employe_ids:
            item.send_results()