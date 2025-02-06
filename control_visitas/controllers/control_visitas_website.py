import datetime as dt
from odoo import http
from odoo.http import request


class ControlVisitasWebsite(http.Controller):
    
    @http.route(['/control_visitas'], type='json', auth='public', website=True)
    def control_visitas_dashboard(self):
        
        visitas_admin = request.env['control.visitas'].search(
            [('name', '=', 'Visita Administración')], limit=1).id
        visitas_megatk = request.env['control.visitas'].search(
            [('name', '=', 'Visita Tienda Megatk')], limit=1).id
        visitas_mediatek = request.env['control.visitas'].search(
            [('name', '=', 'Visita Tienda Meditek')], limit=1).id
        visitas_lenka = request.env['control.visitas'].search(
            [('name', '=', 'Visita Lenka')], limit=1).id
        visitas_clinica = request.env['control.visitas'].search(
            [('name', '=', 'Visita Clínica')], limit=1).id
        
        admin = request.env["control.visitas"].search_count(
            [('name', 'in', visitas_admin)])
        admin_id = request.env["control.visitas"].search(
            [('name', 'in', visitas_admin)])
        admin_ls = [data.name for data in admin_id]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', 'in', visitas_megatk)])
        megatk_id = request.env["control.visitas"].search(
            [('name', 'in', visitas_megatk)])
        megatk_ls = [data.name for data in megatk_id]
        #..........................................    
        mediatek = request.env["control.visitas"].search_count(
            [('name', 'in', visitas_mediatek)])
        mediatek_id = request.env["control.visitas"].search(
            [('name', 'in', visitas_mediatek)])
        mediatek_ls = [data.name for data in mediatek_id]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', 'in', visitas_lenka)])
        lenka_id = request.env["control.visitas"].search(
            [('name', 'in', visitas_lenka)])
        lenka_ls = [data.name for data in lenka_id]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', 'in', visitas_clinica)])
        clinica_id = request.env["control.visitas"].search(
            [('name', 'in', visitas_clinica)])
        clinica_ls = [data.name for data in clinica_id]
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