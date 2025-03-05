import datetime as dt
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class ControlVisitasWebsite(http.Controller):
    
    @http.route('/control_visitas', type='json', auth='public', website=True)
    def control_visitas_dashboard(self):
        cod_reg = request.env.user.ubicacion_vendedor
        reg = ""
        if cod_reg == "2":
            reg = "SPS"
        elif cod_reg == "3":
            reg = "TGU"
            
        _logger.warning(f"region {reg}")

        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        otros_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Otros')])
        otros_ls = [data.name for data in otros_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'gerencia': gerencia,
                'soporte': soporte,
                'otros': otros,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
                'gerencia_name': gerencia_ls,
                'soporte_name': soporte_ls,
                'otros_name': otros_ls
            }
        
        return dashboard_values    
    
    @http.route('/control_visitas_dia', type='json', auth='public', website=True)
    def control_visitas_dashboard_dia(self):
        cod_reg = request.env.user.ubicacion_vendedor
        reg = ""
        if cod_reg == "2":
            reg = "SPS"
        elif cod_reg == "3":
            reg = "TGU"
            

        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '=', dt.date.today()),('region', '=', reg)])
        otros_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Otros')])
        otros_ls = [data.name for data in otros_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'gerencia': gerencia,
                'soporte': soporte,
                'otros': otros,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
                'gerencia_name': gerencia_ls,
                'soporte_name': soporte_ls,
                'otros_name': otros_ls
            }
        
        return dashboard_values    
    
    @http.route('/control_visitas_semana', type='json', auth='public', website=True)
    def control_visitas_dashboard_semana(self):
        cod_reg = request.env.user.ubicacion_vendedor
        reg = ""
        if cod_reg == "2":
            reg = "SPS"
        elif cod_reg == "3":
            reg = "TGU"
        

        
        hoy = dt.date.today()
        semana = str(hoy - dt.timedelta(days=7)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', semana),('region', '=', reg)])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', semana),('region', '=', reg)])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', semana),('region', '=', reg)])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', semana),('region', '=', reg)])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', semana),('region', '=', reg)])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', semana),('region', '=', reg)])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', semana),('region', '=', reg)])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', semana),('region', '=', reg)])
        otros_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Otros')])
        otros_ls = [data.name for data in otros_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'gerencia': gerencia,
                'soporte': soporte,
                'otros': otros,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
                'gerencia_name': gerencia_ls,
                'soporte_name': soporte_ls,
                'otros_name': otros_ls
            }
        
        return dashboard_values    
    
    @http.route('/control_visitas_mes', type='json', auth='public', website=True)
    def control_visitas_dashboard_mes(self):
        cod_reg = request.env.user.ubicacion_vendedor
        reg = ""
        if cod_reg == "2":
            reg = "SPS"
        elif cod_reg == "3":
            reg = "TGU"
        

        
        hoy = dt.date.today()
        mes = str(hoy - dt.timedelta(days=30)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', mes),('region', '=', reg)])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', mes),('region', '=', reg)])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', mes),('region', '=', reg)])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', mes),('region', '=', reg)])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', mes),('region', '=', reg)])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
      #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', mes),('region', '=', reg)])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', mes),('region', '=', reg)])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', mes),('region', '=', reg)])
        otros_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Otros')])
        otros_ls = [data.name for data in otros_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'gerencia': gerencia,
                'soporte': soporte,
                'otros': otros,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
                'gerencia_name': gerencia_ls,
                'soporte_name': soporte_ls,
                'otros_name': otros_ls
            }
        
        return dashboard_values    
    
    @http.route('/control_visitas_anio', type='json', auth='public', website=True)
    def control_visitas_dashboard_anio(self):
        cod_reg = request.env.user.ubicacion_vendedor
        reg = ""
        if cod_reg == "2":
            reg = "SPS"
        elif cod_reg == "3":
            reg = "TGU"
        

        
        hoy = dt.date.today()
        anio = str(hoy - dt.timedelta(days=365)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', anio),('region', '=', reg)])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', anio),('region', '=', reg)])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', anio),('region', '=', reg)])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', anio),('region', '=', reg)])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', anio),('region', '=', reg)])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', anio),('region', '=', reg)])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', anio),('region', '=', reg)])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', anio),('region', '=', reg)])
        otros_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Otros')])
        otros_ls = [data.name for data in otros_name]
        #..........................................    
           
        dashboard_values = {
                'admin': admin,
                'clinica': clinica,
                'meditek': meditek,
                'megatk': megatk,
                'lenka': lenka,
                'gerencia': gerencia,
                'soporte': soporte,
                'otros': otros,
                'admin_name': admin_ls,
                'clinica_name': clinica_ls,
                'meditek_name': meditek_ls,
                'megatk_name': megatk_ls,
                'lenka_name': lenka_ls,
                'gerencia_name': gerencia_ls,
                'soporte_name': soporte_ls,
                'otros_name': otros_ls
            }
        
        return dashboard_values    