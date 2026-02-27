# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import UserError
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
            raise UserError('Error al crear la tarea en todoist')

