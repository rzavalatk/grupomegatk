# -*- coding: utf-8 -*-
from email.policy import default
from time import strftime
from odoo import models, api, fields
from odoo.exceptions import Warning
from datetime import datetime, date, timedelta


class Empleado(models.Model):
    _inherit = "hr.employee"

    def _suma_points(self):
        total = 0
        for meta in self.metas_ids:
            total = total + meta.point_meta

        for norma in self.normas_ids:
            total = total + norma.meta_id.point_meta

        return total

    def _suma_points_assign(self):
        total = 0
        for meta in self.metas_ids:
            total = total + meta.point_assign

        for norma in self.normas_ids:
            total = total + norma.point_assign

        return total

    def _total_points(self):
        self.total_points = self._suma_points()

    def _total_assign(self):
        self.total_assign = self._suma_points_assign()

    def listen(self):
        ready_norma = True
        ready_meta = True
        for item in self.normas_ids:
            if item.state != 'done':
                ready_norma = False
        for item in self.metas_ids:
            if item.state != 'done':
                ready_meta = False
        if ready_meta and ready_norma and self._suma_points() == 100:
            self.state_done('state')
        else:
            raise Warning(
                "No ha terminado de evaluar metas. Todavia tiene pendientes como para cambiar de estado.")

    def _define_user(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        if employee:
            return employee
        else:
            return self.parent_id

    planeadas_ids = fields.One2many("hr.metas.planeadas", "empleado_id")
    metas_ids = fields.One2many("hr.metas.asignadas", "empleado_id")
    normas_ids = fields.One2many("hr.metas.asignadas.default", "empleado_id")
    total_points = fields.Float("Total Puntos", compute=_total_points)
    total_assign = fields.Float(
        "Total Puntos asignados", compute=_total_assign)
    invisible_extra = fields.Boolean(default=False)
    invisible_amonestacion = fields.Boolean(default=False)
    state = fields.Selection([
        ('procces', 'En proceso'),
        ('done', 'Evaluadas'),
    ], string="Estado", default='procces')

    def go_to_resultados(self):
        return {
            'name': 'Resultados',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.resultados',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
            'domain': [('name', '=', self.id)],
        }

    def get_planificadas(self):
        today_date = date.today()
        td = timedelta(30)
        days = today_date + td
        metas_dis = []
        for item in self.planeadas_ids:
            if item.date < days.strftime('%Y-%m-%d'):
                metas_dis.append(item.id)
        return metas_dis

    def send_results(self):
        resultado = self.env['hr.resultados'].create({
            'name': self.id,
            'team': self.equipo_madrug_id.name,
            'date': date.today(),
        })
        normas = self.env['hr.metas.resultados.default']
        metas = self.env['hr.metas.resultados']

        for norma in self.normas_ids:
            vals = {
                'meta_id': norma.meta_id.id,
                'resultado_id': resultado.id,
                'empleado_id': self.id,
                'point_meta': norma.point_meta,
                'point_assign': norma.point_assign,
                'advance': norma.advance,
                'date_end': norma.date_end,
                'remark': norma.remark
            }
            normas.create(vals)
            norma.write({
                'point_assign': 0,
                'date_end': None,
                'remark': "",
                'state': "valid",
            })
        for meta in self.metas_ids:
            vals = {
                'name': self.name,
                'resultado_id': resultado.id,
                'meta_id': meta.meta_id.id,
                'empleado_id': self.id,
                'evaluator': meta.evaluator.id,
                'point_meta': meta.point_meta,
                'point_assign': meta.point_assign,
                'advance': meta.advance,
                'remark': meta.remark,
                'date_end': meta.date_end,
                'date_valid': meta.date_valid,
            }
            metas.create(vals)

            if meta.meta_id.reapet:
                meta.write({
                    'point_assign': 0,
                    'advance': "",
                    'remark': "",
                    'date_end': None,
                    'date_valid': None,
                    'state': "draft"
                })
                self.write({
                    'state': 'procces',
                    'invisible_extra': False,
                    'invisible_amonestacion': False
                })
            else:
                self.write({
                    'metas_ids': [(2, meta.id)],
                    'state': 'procces',
                    'invisible_extra': False,
                    'invisible_amonestacion': False
                })
        planificadas = self.get_planificadas()
        for item in planificadas:
            meta = self.env['hr.metas.planeadas'].browse(item)
            vals = {
                'meta_id': meta.meta_id.id,
                'empleado_id': meta.empleado_id.id,
                'evaluator': meta.evaluator.id,
                'date_valid': meta.meta_id.date,
                'point_meta': meta.point_meta
            }
            self.env['hr.metas.asignadas'].create(vals)
            self.write({
                'planeadas_ids': [(2, item)],
            })

    def create_exta_amonestacion(self):
        type_meta = self.env.context.get('type_meta')
        metas_id = self.env['hr.metas']
        meta_id = metas_id.search(
            [('name', '=', "Puntos Extra" if type_meta == 'extra' else "Amonestación")])
        ids = []
        for item in meta_id:
            ids.append(item)
        id_meta = {}
        if len(ids):
            id_meta = ids[0]
        else:
            vals = {
                'name': "Puntos Extra" if type_meta == 'extra' else "Amonestación",
                'obj': "Puntos Extra" if type_meta == 'extra' else "Amonestación",
                'advance': "Puntos Extra" if type_meta == 'extra' else "Amonestación",
                'reapet': False,
                'point_meta': 0,
                'date': datetime.today(),
                'negative': False if type_meta == 'extra' else True,
            }
            id_meta = metas_id.create(vals)
        asign_meta = self.env['hr.metas.asignadas']
        evaluator = self._define_user()
        asign_meta.create({
            'meta_id': id_meta.id,
            'empleado_id': self.id,
            'evaluator': evaluator.id,
            'date_valid': datetime.today()
        })
        field = "invisible_extra" if type_meta == 'extra' else "invisible_amonestacion"
        val = {}
        val[field] = True
        self.write(val)

    def state_done(self, state):
        item = {}
        item[state] = 'done'
        self.write(item)

    def state_non(self):
        self.write({
            'state': 'procces'
        })

    def _point_totals(self):
        total = self._suma_points()
        if total < 100:
            return total if total > 0 else True
        else:
            return False

    def check_total_assign(self, points_meta):
        total = self._suma_points_assign()
        new_total = total + points_meta
        if new_total <= 100:
            return True
        else:
            return False

    def check_availability(self, points_meta):
        total = self._point_totals()
        if total:
            new_total = total + points_meta
            if new_total <= 100:
                return True
            else:
                return False
        else:
            return False

    def check_availability_edit(self, points_meta, new_point):
        total = self._suma_points()
        new_total = total - points_meta + new_point
        if new_total <= 100:
            return True
        else:
            return False

    def open_wizard(self):
        if self._point_totals():
            return {
                'name': 'Asignar Meta',
                'type': 'ir.actions.act_window',
                'res_model': 'hr.meta.wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'domain': [],
            }
        else:
            raise Warning(
                "Este Empleado ya no tiene puntos disponibles para asignarle una meta.")


class MetaAsignadadefault(models.Model):
    _name = "hr.metas.asignadas.default"

    @api.one
    def _point_meta(self):
        self.point_meta = self.meta_id.point_meta

    meta_id = fields.Many2one("hr.metas.default", "Meta", readonly=True)
    empleado_id = fields.Many2one("hr.employee", "Asignado", readonly=True)
    point_meta = fields.Float("Puntaje", compute=_point_meta)
    point_assign = fields.Float("Puntos asignados", readonly=True)
    advance = fields.Text("Avances", readonly=True, default="Norma")
    date_end = fields.Date("Fecha de evaluación", readonly=True)
    remark = fields.Text("Observaciones", readonly=True)
    state = fields.Selection([
        ('valid', 'En avances'),
        ('done', 'Evaluada'),
    ], string="Estado", default='draft')


class MetaAsignada(models.Model):
    _name = "hr.metas.asignadas"

    def _active_id(self):
        active_id = self.env.context.get('active_ids', [])
        return [('id', 'not in', active_id)]

    def _define_user(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        return employee

    @api.one
    def _name_assign(self):
        self.name = self.empleado_id.name
        
    @api.one
    def _current_date(self):
        self.date = datetime.today()

    name = fields.Char("Meta", compute=_name_assign)
    meta_id = fields.Many2one("hr.metas", "Meta", readonly=True)
    empleado_id = fields.Many2one("hr.employee", "Asignado", readonly=True)
    evaluator = fields.Many2one(
        "hr.employee", "Evaluador", domain=_active_id, default=_define_user)
    point_meta = fields.Float("Puntaje", readonly=True)
    point_assign = fields.Float("Puntos asignados", readonly=True)
    advance = fields.Text("Avances", readonly=True)
    remark = fields.Text("Observaciones", readonly=True)
    date = fields.Datetime("Fecha actual",compute=_current_date)
    date_end = fields.Date("Fecha de evaluación", readonly=True)
    date_valid = fields.Date("Fecha de asignación", readonly=True)
    state = fields.Selection([
        ('draft', 'Asignada'),
        ('valid', 'En avances'),
        ('done', 'Evaluada'),
    ], string="Estado", default='draft')

    @api.multi
    def write(self, vals):
        if self.meta_id.negative:
            vals['point_assign'] = -vals['point_assign']
        res = super(MetaAsignada, self).write(vals)
        return res
    
    def send_email(self):
        template = self.env.ref('planilla_y_metas.email_template_avance_metas_asignadas')
        email_values = {
            'email_to': self.evaluator.work_email,
            'email_from': self.env.user.email
        }
        template.send_mail(self.id, email_values=email_values, force_send=True)
        return True


class MetasTeam(models.Model):
    _name = "hr.metas.team"

    empleado_id = fields.Many2one("hr.employee", "Empleado")
    meta_id = fields.Many2one("hr.metas", "Meta")


class Metas(models.Model):
    _name = "hr.metas"

    name = fields.Text("Meta")
    obj = fields.Text("Objetivo")
    team = fields.One2many("hr.metas.team", "meta_id",
                           string="Equipo", readonly=True)
    tipo_meta = fields.Selection([
        ('strategic', 'Estratégicas'),
        ('extra', 'Apoyo extra'),
    ], string="Tipo de meta")
    date = fields.Date("Fecha", readonly=True)
    date_max = fields.Date("Fecha maxima")
    reapet = fields.Boolean("Repetitiva")
    negative = fields.Boolean("Repetitiva", default=False)

    @api.multi
    def unlink(self):
        metas_assign = self.env['hr.metas.asignadas'].search(
            [('meta_id', '=', self.id)])
        for item in metas_assign:
            item.unlink()
        res = super(Metas, self).unlink()
        return res


class Metasdefault(models.Model):
    _name = "hr.metas.default"

    name = fields.Text("Meta")
    obj = fields.Text("Objetivo")
    point_meta = fields.Float("Puntaje")

    def assign_all_employee(self):
        employees = self.env['hr.employee'].search([])
        assign = self.env['hr.metas.asignadas.default']
        for employee in employees:
            exist = False
            for item in employee.normas_ids:
                if item.meta_id.id == self.id:
                    exist = True
            if exist == False:
                vals = {
                    'meta_id': self.id,
                    'empleado_id': employee.id,
                    'state': 'valid'
                }
                assign.create(vals)


class MetaPlaneadas(models.Model):
    _name = "hr.metas.planeadas"

    def _active_id(self):
        active_id = self.env.context.get('active_ids', [])
        return [('id', 'not in', active_id)]

    def _define_user(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        return employee

    @api.one
    def _date_assign(self):
        self.date = self.meta_id.date

    date = fields.Char("Fecha", compute=_date_assign)
    meta_id = fields.Many2one("hr.metas", "Meta", readonly=True)
    empleado_id = fields.Many2one("hr.employee", "Asignado", readonly=True)
    evaluator = fields.Many2one(
        "hr.employee", "Evaluador", domain=_active_id, default=_define_user)
    point_meta = fields.Float("Puntaje", readonly=True)


class ResultadosNormas(models.Model):
    _name = "hr.metas.resultados.default"

    meta_id = fields.Many2one("hr.metas.default", "Meta", readonly=True)
    resultado_id = fields.Many2one("hr.resultados", readonly=True)
    empleado_id = fields.Many2one("hr.employee", "Asignado", readonly=True)
    point_meta = fields.Float("Puntaje", readonly=True)
    point_assign = fields.Float("Puntos asignados", readonly=True)
    advance = fields.Text("Avances", readonly=True)
    date_end = fields.Date("Fecha de evaluación", readonly=True)
    remark = fields.Text("Observaciones", readonly=True)


class ResultadosMetas(models.Model):
    _name = "hr.metas.resultados"

    name = fields.Char("Meta", readonly=True)
    resultado_id = fields.Many2one("hr.resultados", readonly=True)
    meta_id = fields.Many2one("hr.metas", "Meta", readonly=True)
    empleado_id = fields.Many2one("hr.employee", "Asignado", readonly=True)
    evaluator = fields.Many2one("hr.employee", "Evaluador", readonly=True)
    point_meta = fields.Float("Puntaje", readonly=True)
    point_assign = fields.Float("Puntos asignados", readonly=True)
    advance = fields.Text("Avances", readonly=True)
    remark = fields.Text("Observaciones", readonly=True)
    date_end = fields.Date("Fecha de evaluación", readonly=True)
    date_valid = fields.Date("Fecha de asignación", readonly=True)


class ResultadosNormas(models.Model):
    _name = "hr.resultados"

    def _suma_points_normas(self):
        total = 0

        for norma in self.normas_ids:
            total = total + norma.point_meta

        self.total_points_normas = total
        
    def _suma_points_estrategicas(self):
        total = 0

        for meta in self.metas_ids:
            if meta.meta_id.tipo_meta == 'strategic':
                total = total + meta.point_meta

        self.total_points_estatigicas = total
        
    def _suma_points_apoyo(self):
        total = 0

        for meta in self.metas_ids:
            if meta.meta_id.tipo_meta == 'extra':
                total = total + meta.point_meta

        self.total_points_apoyo = total
        
    def _str_date(self):
        self.str_date=self.date.strftime('%B del %Y')
    
    def _suma_points_assign(self):
        total = 0
        for meta in self.metas_ids:
            total = total + meta.point_assign

        for norma in self.normas_ids:
            total = total + norma.point_assign

        self.total_assign = total

    name = fields.Many2one("hr.employee", "Empleado", readonly=True)
    team = fields.Char("Equipo")
    date = fields.Date("Fecha")
    str_date = fields.Char("Fecha",compute=_str_date)
    metas_ids = fields.One2many("hr.metas.resultados", "resultado_id")
    normas_ids = fields.One2many("hr.metas.resultados.default", "resultado_id")
    total_points = fields.Float("Total Puntos", default=100)
    total_points_normas = fields.Float("Total Puntos", compute=_suma_points_normas)
    total_points_estatigicas = fields.Float("Total Puntos", compute=_suma_points_estrategicas)
    total_points_apoyo = fields.Float("Total Puntos", compute=_suma_points_apoyo)
    total_assign = fields.Float(
        "Total Puntos asignados", compute=_suma_points_assign)

    def send_email(self):
        template = self.env.ref('planilla_y_metas.email_template_resultados_meta')
        email_values = {
            'email_to': self.name.work_email,
            'email_from': self.env.user.email
        }
        template.send_mail(self.id, email_values=email_values, force_send=True)
        return True
