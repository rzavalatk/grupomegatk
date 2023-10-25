# -*- coding: utf-8 -*-
from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Empleado(models.Model):
    _inherit = "hr.employee"

    equipo_metas_id = fields.Many2one(
        'hr.employee.equipo.metas', string='Equipo metas',)


class EmpleadoEquipoMetas(models.Model):
    _name = 'hr.employee.equipo.metas'
    _description = 'Metas'
    _order = 'name asc'
    _description = "description de la description descriptiva"

    name = fields.Char("Equipo")
    active = fields.Boolean(string='Activo', default=True)
    employe_ids = fields.One2many(
        'hr.employee', 'equipo_metas_id', string='Empleados',)
    employe_jefe_id = fields.Many2one('hr.employee', string='Jefe',)
    
    #@api.model_create_multi
    def go_metas(self):
        ids=[]
        for item in self.employe_ids:
            ids.append(item.id) 
        return {
        'name': 'Metas',
         'type': 'ir.actions.act_window',
         'res_model': 'hr.employee.metas',
         'view_type': 'form',
         'view_mode': 'tree,form',
         'views': [(False, 'tree'),(False,'form')],
         'target': 'current',
         'domain': [('empleado_id', 'in', ids)],
        }


class EmpleadoMetas(models.Model):
    _name = 'hr.metas'
    _description = "description"
    

    name = fields.Char("Meta")
    employee_meta_id = fields.Many2one('hr.employee.metas')
    value = fields.Integer("Valor en %")
    asign = fields.Float("Asignado")
    tipo_meta = fields.Selection([
        ('continuous', 'Ordinarias y continuas'),
        ('strategic', 'Estratégicas'),
        ('extra', 'Apoyo extra'),
    ], string="Tipo de meta")
    state = fields.Char()



class EmpleadoMetas(models.Model):
    _name = 'hr.employee.metas'
    _description = "description"

    def _state_meta(self):
        for item in self.metas_id:
            item.write({
                'state': self.state
            })
    
    def _employee(self):
        self.name = self.empleado_id.name
        
    def _total_posible(self):
        total = 0
        for item in self.metas_id:
            total += item.value
        self.total_posible = total
        
    def _total(self):
        total = 0
        for item in self.metas_id:
            total += item.asign
        total += self.extra
        total -= self.admonition
        self.total = total
             

    name = fields.Char(compute=_employee)
    date_meta = fields.Date("Fecha")
    empleado_id = fields.Many2one(
        'hr.employee', 'Empleado', auto_join=True, index=True, ondelete="cascade", required=True)
    metas_id = fields.Many2many('hr.metas','employee_meta_id')
    extra = fields.Float("Puntos extra")
    admonition = fields.Float("Amonestación")
    total = fields.Float("Total",compute=_total)
    total_posible = fields.Float("Posible total",compute=_total_posible)
    nota = fields.Text("Anotaciones")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('valid', 'Validado'),
        ('qualified', 'Calificado'),
        ('cancel', 'Cancelado'),
    ], string="Tipo de meta", default='draft')
    state_meta = fields.Float("Total",compute=_state_meta)

    
    def back_to_draft(self):
        for item in self.metas_id:
             item.write({
                 'asign': 0
             })
        self.write({
            'state': 'draft',
            'extra': 0,
            'admonition': 0,
        })
        
    def valid_metas(self):
        if self.total_posible == 100:
            self.write({
            'state': 'valid'
        })
        else:
            raise UserError(_('La suma de las tareas tiene que ser igual a 100%.'))
            
    def qualified_metas(self):
        for item in self.metas_id:
            if item.asign > item.value:
                raise UserError(_('No se puede calificar, una asignacion supera el valor maximo. Revice los valores maximos que puede proporcionar a una meta.'))
        self.write({
            'state': 'qualified'
        })
    
    def cancel_metas(self):
        self.write({
            'state': 'cancel'
        })