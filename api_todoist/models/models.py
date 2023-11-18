# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import Warning
import requests


class ApiTodoist(models.TransientModel):
    _name = "api.todoist"
    _description = "description"

    basePath = "https://api.todoist.com/rest/v2"

    def get_function(self, route, header, id=False):
        try:
            if id:
                res = requests.get(self.basePath + route +
                                '/' + id, headers=header).json()
            else:
                res = requests.get(self.basePath + route, headers=header).json()
            return res
        except:
            return {}


    def post_function(self, route, header, data):
        try:
            res = requests.post(self.basePath + route, headers=header, json=data).json()
            return res
        except:
            return {}


class TodoistUsers(models.Model):
    _name = "todoist.users"
    _description = "description"

    name = fields.Many2one("res.users", "Empleado")
    token = fields.Char("Token de usuario todoist")
    
    def get_id_projects(self):
        route = '/projects'
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.env['api.todoist'].get_function(route, headers)
        res_final = None
        for item in res:
            if item['name'] == 'Inbox':
                res_final = item['id']
        return res_final
    
    def create_task(self, data):
        route = '/tasks'
        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.env['api.todoist'].post_function(route,headers,data)
        try:
            res['id']
        except:
            raise Warning('Error al crear la tarea en todoist')



class MailActivity(models.Model):
    _inherit = "mail.activity"

    """#@api.model_create_multi
    def create(self, values):
        try:
            model = self.env['ir.model'].browse(values['res_model_id']).model
            users = self.env['todoist.users'].search(
                [('name', '=', values['user_id'])])
            user = {}
            if users:
                for item in users:
                    user = item
            project = self.env['todoist.users'].browse(user.id).get_id_projects()
            vals = {
                "content": values['summary'] + " - Ticket: "+ str(values['res_id']) if model == 'crm.lead' else values['summary'],
                "due_lang": "es",
                "due_date": values['date_deadline'],
                "project_id": project
            }
            self.env['todoist.users'].browse(user.id).create_task(vals)
            return super(MailActivity, self).create(values)
        except:
        # except Exception as inst:
            # print("/////////////////",type(inst),"/////////////////")
            # print("/////////////////",inst.args,"/////////////////")
            # print("/////////////////",inst,"/////////////////")            
            return super(MailActivity, self).create(values)"""


