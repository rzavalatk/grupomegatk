# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import Warning


class ReasignarMeta(models.TransientModel):
    _name = "hr.meta.reasignar"

    def _active_id(self):
        active_id = self.env.context.get('active_ids', [])
        return [('id', 'not in', active_id)]

    def _define_user(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        return employee

    empleados_ids = fields.Many2many(
        "hr.employee", "planeadas_ids", string="Asignados",required=True)
    evaluator = fields.Many2one(
        "hr.employee", "Evaluador", domain=_active_id, default=_define_user,required=True)
    point_meta = fields.Float("Puntaje",required=True)
    date_max = fields.Date("Fecha maxima",required=True)

    def _check(self, items_hr, points):
        for item in items_hr:
            res = item.check_availability(points)
            if res == False:
                raise Warning(
                    f"El Empleado {item.name} ya no tiene puntos disponibles para asignarle una meta.")
        return True

    def re_assign(self):
        active_id = self.env.context.get('active_id')
        ids = []
        today=datetime.today()
        for item in self.empleados_ids:
            ids.append(item.id)
        hr = self.env['hr.employee'].search([('id', 'in', ids)])
        if self._check(hr, self.point_meta):
            t=self.env['hr.metas'].browse(active_id)
            t.write({
                'team': [(5,)],
                'date_max': self.date_max,
                'date': today
            })
            asign_meta = self.env['hr.metas.asignadas']
            team = self.env['hr.metas.team']
            for employee in hr:
                asign_meta.create({
                    'meta_id': active_id,
                    'empleado_id': employee.id,
                    'evaluator': self.evaluator.id,
                    'date_valid': today,
                    'point_meta': self.point_meta,
                })
                team.create({
                    'meta_id': active_id,
                    'empleado_id': employee.id,
                })
                # for meta in employee.metas_ids:
                #      if meta.meta_id.id == active_id:
                #          employee.write({
                #              'metas_ids': [(2,meta.id)]
                #          })
        
             

class PuntajeMeta(models.TransientModel):
    _name = "hr.meta.puntaje"

    point_meta = fields.Float("Puntaje")

    def set_point_meta(self):
        active_id = self.env.context.get('active_id')
        assign = self.env['hr.metas.asignadas'].browse(active_id)
        check = assign.sudo().empleado_id.check_availability_edit(
            assign.point_meta, self.point_meta)
        if check:
            vals = {
                'point_meta': self.point_meta,
            }
            assign.write(vals)
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            raise Warning(
                "El Empleado sobre pasa el 100'%' de puntos en las metas.")


class AvanceMeta(models.TransientModel):
    _name = "hr.meta.avance"

    advance = fields.Text("Avances")

    def set_advance(self):
        active_id = self.env.context.get('active_id')
        assign = self.env['hr.metas.asignadas'].browse(active_id)
        vals = {
            'advance': self.advance,
            'state': 'valid'
        }
        assign.write(vals)
        assign.send_email()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class EvaluarMeta(models.TransientModel):
    _name = "hr.meta.evaluar"

    point_assign = fields.Integer("Porcentaje %")
    remark = fields.Text("Observación")

    def set_points(self):
        porcentaje = self.point_assign
        if porcentaje < 0:
            porcentaje = porcentaje * -1
        if porcentaje > 100:
            raise Warning(
                "El valor NO puede superar los 100, intente de nuevo y asegurece de ingresar un valor entre 0 - 100.")

        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        assign = self.env[active_model].browse(active_id)
        points = assign.point_meta * \
            (porcentaje/100) if assign.point_meta > 0 else porcentaje
        vals = {
            'point_assign': points,
            'state': 'done',
            'date_end': datetime.today(),
            'remark': self.remark
        }
        check = {}
        try:
            check = assign.sudo().empleado_id.check_total_assign(
                -points if assign.meta_id.negative else points)
        except:
            check = assign.sudo().empleado_id.check_total_assign(points)
        if check:
            assign.write(vals)
            # return {
            #     'type': 'ir.actions.client',
            #     'tag': 'reload',
            # }
        else:
            raise Warning(
                "El Empleado sobre pasa el 100'%' de puntos en las metas, Corrija el valor antes de evaluar")


class AssignMeta(models.TransientModel):
    _name = "hr.meta.wizard"

    def _active_id(self):
        active_id = self.env.context.get('active_ids', [])
        return [('id', 'not in', active_id)]

    def _define_user(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        return employee

    name = fields.Text("Meta", required=True)
    obj = fields.Text("Objetivo",required=True)
    evaluator = fields.Many2one(
        "hr.employee", "Evaluador", domain=_active_id, default=_define_user,required=True)
    mates = fields.Many2many("hr.employee", "metas_ids",
                             string="Compañeros", domain=_active_id)
    tipo_meta = fields.Selection([
        ('strategic', 'Estratégicas'),
        ('extra', 'Apoyo extra'),
    ], string="Tipo de meta",required=True)
    date_max = fields.Date("Fecha maxima",required=True)
    reapet = fields.Boolean("Repetitiva")
    point_meta = fields.Float("Puntaje",required=True)

    def _check(self, items_hr, points):
        for item in items_hr:
            res = item.check_availability(points)
            if res == False:
                raise Warning(
                    f"El Empleado {item.name} ya no tiene puntos disponibles para asignarle una meta.")
        return True

    def create_meta(self, current):
        ids = [current['active_id']]
        for item in self.mates:
            ids.append(item.id)
        hr = self.env['hr.employee'].search([('id', 'in', ids)])

        if self._check(hr, self.point_meta):
            vals = {
                'name': self.name,
                'obj': self.obj,
                'tipo_meta': self.tipo_meta,
                'date_max': self.date_max,
                'reapet': self.reapet,
                'date': datetime.today(),
            }
            id_meta = self.env['hr.metas'].create(vals)
            asign_meta = self.env['hr.metas.asignadas']
            team = self.env['hr.metas.team']
            for employee in hr:
                asign_meta.create({
                    'meta_id': id_meta.id,
                    'empleado_id': employee.id,
                    'evaluator': self.evaluator.id,
                    'date_valid': datetime.today(),
                    'point_meta': self.point_meta,
                })
                team.create({
                    'meta_id': id_meta.id,
                    'empleado_id': employee.id,
                })


class AssignMetaPlaneada(models.TransientModel):
    _name = "hr.meta.planeada.wizard"

    def _active_id(self):
        active_id = self.env.context.get('active_ids', [])
        return [('id', 'not in', active_id)]

    def _define_user(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        return employee

    name = fields.Text("Meta")
    obj = fields.Text("Objetivo")
    evaluator = fields.Many2one(
        "hr.employee", "Evaluador", domain=_active_id, default=_define_user)
    mates = fields.Many2many("hr.employee", "normas_ids",
                             string="Compañeros", domain=_active_id)
    tipo_meta = fields.Selection([
        ('strategic', 'Estratégicas'),
        ('extra', 'Apoyo extra'),
    ], string="Tipo de meta")
    date = fields.Date("Fecha")
    date_max = fields.Date("Fecha maxima")
    reapet = fields.Boolean("Repetitiva")
    point_meta = fields.Float("Puntaje")

    def _check(self, items_hr, points):
        for item in items_hr:
            res = item.check_availability(points)
            if res == False:
                raise Warning(
                    f"El Empleado {item.name} ya no tiene puntos disponibles para asignarle una meta.")
        return True

    def plan_meta(self, current):
        ids = [current['active_id']]
        for item in self.mates:
            ids.append(item.id)
        hr = self.env['hr.employee'].search([('id', 'in', ids)])
        vals = {
            'name': self.name,
            'obj': self.obj,
            'tipo_meta': self.tipo_meta,
            'date_max': self.date_max,
            'reapet': self.reapet,
            'date': self.date,
        }
        id_meta = self.env['hr.metas'].create(vals)
        planeada_meta = self.env['hr.metas.planeadas']
        team = self.env['hr.metas.team']
        for employee in hr:
            planeada_meta.create({
                'meta_id': id_meta.id,
                'empleado_id': employee.id,
                'evaluator': self.evaluator.id,
                'point_meta': self.point_meta,
            })
            team.create({
                'meta_id': id_meta.id,
                'empleado_id': employee.id,
            })
