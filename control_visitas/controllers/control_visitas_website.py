import datetime as dt
from odoo import http
from odoo.http import request


class ControlVisitasWebsite(http.Controller):
    
    @http.route('/control_visitas', type='json', auth='public', website=True)
    def control_visitas_dashboard(self):
        
        visitas_admin = request.env['control.visitas'].search(
            [('name', '=', 'Visita Administración')]).id
        visitas_megatk = request.env['control.visitas'].search(
            [('name', '=', 'Visita Tienda Megatk')]).id
        visitas_mediatek = request.env['control.visitas'].search(
            [('name', '=', 'Visita Tienda Meditek')]).id
        visitas_lenka = request.env['control.visitas'].search(
            [('name', '=', 'Visita Lenka')]).id
        visitas_clinica = request.env['control.visitas'].search(
            [('name', '=', 'Visita Clínica')]).id
        
        admin = request.env["help.ticket"].search_count(
            [('name', 'in', visitas_admin)])
        admin_id = request.env["help.ticket"].search(
            [('name', 'in', visitas_admin)])
        admin_ls = [data.id for data in admin_id]
        #..........................................    
        megatk = request.env["help.ticket"].search_count(
            [('name', 'in', visitas_megatk)])
        megatk_id = request.env["help.ticket"].search(
            [('name', 'in', visitas_megatk)])
        megatk_ls = [data.id for data in megatk_id]
        #..........................................    
        mediatek = request.env["help.ticket"].search_count(
            [('name', 'in', visitas_mediatek)])
        mediatek_id = request.env["help.ticket"].search(
            [('name', 'in', visitas_mediatek)])
        mediatek_ls = [data.id for data in mediatek_id]
        #..........................................    
        lenka = request.env["help.ticket"].search_count(
            [('name', 'in', visitas_lenka)])
        lenka_id = request.env["help.ticket"].search(
            [('name', 'in', visitas_lenka)])
        lenka_ls = [data.id for data in lenka_id]
        #..........................................    
        clinica = request.env["help.ticket"].search_count(
            [('name', 'in', visitas_clinica)])
        clinica_id = request.env["help.ticket"].search(
            [('name', 'in', visitas_clinica)])
        clinica_ls = [data.id for data in clinica_id]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'mediatek': mediatek,
                'megatk': megatk,
                'lenka': lenka,
                'admin_id': admin_ls,
                'clinica_id': clinica_ls,
                'mediatek_id': mediatek_ls,
                'megatk_id': megatk_ls,
                'lenka_id': lenka_ls,
            }
        
        return dashboard_values