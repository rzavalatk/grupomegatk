# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HelpTeam(models.Model):
    """ Esta clase representa un equipo de soporte técnico en el sistema y proporciona
     Información sobre los miembros del equipo, el líder y el proyecto relacionado."""
    _name = 'help.team'
    _description = 'Helpdesk Team'

    name = fields.Char(string='Nombre', help='Nombre del equipo de ayuda')
    team_lead_id = fields.Many2one(
        'res.users',
        string='Lider del equipo',
        help='Nombre del lider del equipo.',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'odoo_website_helpdesk.helpdesk_team_leader').id)])
    member_ids = fields.Many2many(
        'res.users',
        string='Miembros del equipo',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'odoo_website_helpdesk.helpdesk_user').id)])
    email = fields.Char(string='Email', help='Email')
    project_id = fields.Many2one('project.project',
                                 string='Proyecto',
                                 help='El proyecto en el que se encuentran actualmente.')
    create_task = fields.Boolean(string="Crear tarea",
                                 help="Habilitar para permitir que el equipo"
                                      "crear tareas a partir de tickets")

    @api.onchange('team_lead_id')
    def members_choose(self):
        """ Este método se activa cuando se cambia el líder del equipo. Él
        actualiza los miembros del equipo disponibles según el líder seleccionado y
        filtra al líder de la lista de miembros potenciales."""
        fetch_members = self.env['res.users'].search([])
        filtered_members = fetch_members.filtered(
            lambda x: x.id != self.team_lead_id.id)
        return {'domain': {'member_ids': [
            ('id', '=', filtered_members.ids),
            ('groups_id', 'in', self.env.ref('base.group_user').id),
            ('groups_id', 'not in', self.env.ref(
                'odoo_website_helpdesk.helpdesk_team_leader').id)]}}
