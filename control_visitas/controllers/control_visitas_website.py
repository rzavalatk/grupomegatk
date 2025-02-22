import datetime as dt
from odoo import http
from odoo.http import request


class ControlVisitasWebsite(http.Controller):
    
    @http.route('/control_visitas', type='json', auth='public', website=True)
    def control_visitas_dashboard(self):
        
        # visitas_admin = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Administración')], limit=1).id
        # visitas_megatk = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Megatk')], limit=1).id
        # visitas_mediatek = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Meditek')], limit=1).id
        # visitas_lenka = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Lenka')], limit=1).id
        # visitas_clinica = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Clínica')], limit=1).id
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '=', dt.date.today())])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '=', dt.date.today())])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '=', dt.date.today())])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '=', dt.date.today())])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '=', dt.date.today())])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
            }
        
        return dashboard_values    
    
    @http.route('/control_visitas_dia', type='json', auth='public', website=True)
    def control_visitas_dashboard_dia(self):
        
        # visitas_admin = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Administración')], limit=1).id
        # visitas_megatk = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Megatk')], limit=1).id
        # visitas_mediatek = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Meditek')], limit=1).id
        # visitas_lenka = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Lenka')], limit=1).id
        # visitas_clinica = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Clínica')], limit=1).id
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '=', dt.date.today())])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '=', dt.date.today())])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '=', dt.date.today())])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '=', dt.date.today())])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '=', dt.date.today())])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
            }
        
        return dashboard_values    
    
    @http.route('/control_visitas_semana', type='json', auth='public', website=True)
    def control_visitas_dashboard_semana(self):
        
        # visitas_admin = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Administración')], limit=1).id
        # visitas_megatk = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Megatk')], limit=1).id
        # visitas_mediatek = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Meditek')], limit=1).id
        # visitas_lenka = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Lenka')], limit=1).id
        # visitas_clinica = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Clínica')], limit=1).id
        
        hoy = dt.date.today()
        semana = str(hoy - dt.timedelta(days=7)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', semana)])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', semana)])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', semana)])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', semana)])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', semana)])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
            }
        
        return dashboard_values    
    
    @http.route('/control_visitas_semana', type='json', auth='public', website=True)
    def control_visitas_dashboard_mes(self):
        
        # visitas_admin = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Administración')], limit=1).id
        # visitas_megatk = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Megatk')], limit=1).id
        # visitas_mediatek = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Meditek')], limit=1).id
        # visitas_lenka = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Lenka')], limit=1).id
        # visitas_clinica = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Clínica')], limit=1).id
        
        hoy = dt.date.today()
        mes = str(hoy - dt.timedelta(days=30)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', mes)])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', mes)])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', mes)])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', mes)])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', mes)])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
            }
        
        return dashboard_values    
    
    @http.route('/control_visitas_semana', type='json', auth='public', website=True)
    def control_visitas_dashboard_anio(self):
        
        # visitas_admin = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Administración')], limit=1).id
        # visitas_megatk = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Megatk')], limit=1).id
        # visitas_mediatek = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Tienda Meditek')], limit=1).id
        # visitas_lenka = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Lenka')], limit=1).id
        # visitas_clinica = request.env['control.visitas'].search(
        #     [('name', '=', 'Visita Clínica')], limit=1).id
        
        hoy = dt.date.today()
        anio = str(hoy - dt.timedelta(days=365)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', anio)])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', anio)])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', anio)])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', anio)])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', anio)])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
            }
        
        return dashboard_values    