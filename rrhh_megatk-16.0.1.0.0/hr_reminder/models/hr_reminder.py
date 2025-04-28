# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields


class HrPopupReminder(models.Model):
    _name = 'hr.reminder'

    name = fields.Char(string='Titulo', required=True)
    model_name = fields.Many2one('ir.model', help="Elija un modelo",
                                 string="Modelo", required=True,
                                 ondelete='cascade',
                                 domain="[('model', 'like','hr')]")
    model_field = fields.Many2one('ir.model.fields', string='Campo',
                                  help="Elija un campo",
                                  domain="[('model_id', '=',model_name),"
                                         "('ttype', 'in', ['datetime','date'])]"
                                  , required=True, ondelete='cascade')
    search_by = fields.Selection([('today', 'Hoy'),
                                  ('set_period', 'Por periodo'),
                                  ('set_date', 'Por fecha'), ],
                                 required=True, string="Buscar por")
    days_before = fields.Integer(string='Recordatorio antes',
                                 help="Número de días antes del recordatorio")
    active = fields.Boolean(string="Activo", default=True)
    # exclude_year = fields.Boolean(string="Consider day alone")
    reminder_active = fields.Boolean(string="Recordatorio Activo",
                                     help="Recordatorio activo")
    date_set = fields.Date(string='Seleccionar fecha',
                           help="Seleccione la fecha de configuración del recordatorio")
    date_from = fields.Date(string="Fecha de inicio", help="Fecha de inicio")
    date_to = fields.Date(string="Fecha de finalización", help="Fecha de finalización")
    expiry_date = fields.Date(string="Fecha de vencimiento del recordatorio", help="Fecha de vencimiento del recordatorio")
    company_id = fields.Many2one('res.company', string='Compañia',
                                 required=True, help="Compañia",
                                 default=lambda self: self.env.user.company_id)

    def reminder_scheduler(self):
        """Función para ejecutar el programador para recordatorios."""
        now = fields.Datetime.from_string(fields.Datetime.now())
        today = fields.Date.today()
        obj = self.env['hr.reminder'].search([])
        for i in obj:
            if i.search_by != "today":
                if i.expiry_date and datetime.strptime(str(today),
                                                       "%Y-%m-%d") == datetime.\
                        strptime(str(i.expiry_date), "%Y-%m-%d"):
                    i.active = False
                else:
                    if i.search_by == "set_date":
                        d1 = datetime.strptime(str(i.date_set), "%Y-%m-%d")
                        d2 = datetime.strptime(str(today), "%Y-%m-%d")
                        daydiff = abs((d2 - d1).days)
                        if daydiff <= i.days_before:
                            i.reminder_active = True
                        else:
                            i.reminder_active = False
                    elif i.search_by == "set_period":
                        d1 = datetime.strptime(str(i.date_from), "%Y-%m-%d")
                        d2 = datetime.strptime(str(today), "%Y-%m-%d")
                        daydiff = abs((d2 - d1).days)
                        if daydiff <= i.days_before:
                            i.reminder_active = True
                        else:
                            i.reminder_active = False
            else:
                i.reminder_active = True
