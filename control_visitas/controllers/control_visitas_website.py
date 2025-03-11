import datetime as dt
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class ControlVisitasWebsite(http.Controller):
    
    @http.route(f'/control_visitas_tgu', type='json', auth='public', website=True)
    def control_visitas_dashboard_tgu(self):
    
        admin = request.env["control.visitas"].search_count(
             [('name', '=', 'Visita Administración'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
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
    
    @http.route('/control_visitas_dia_tgu', type='json', auth='public', website=True)
    def control_visitas_dashboard_dia_tgu(self):
      
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '=', dt.date.today()),('region', '=', "TGU")])
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
    
    @http.route(f'/control_visitas_semana_tgu', type='json', auth='public', website=True)
    def control_visitas_dashboard_semana_tgu(self):
      
        hoy = dt.date.today()
        semana = str(hoy - dt.timedelta(days=7)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', semana),('region', '=', "TGU")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', semana),('region', '=', "TGU")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', semana),('region', '=', "TGU")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', semana),('region', '=', "TGU")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', semana),('region', '=', "TGU")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', semana),('region', '=', "TGU")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', semana),('region', '=', "TGU")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', semana),('region', '=', "TGU")])
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
    
    @http.route(f'/control_visitas_mes_tgu', type='json', auth='public', website=True)
    def control_visitas_dashboard_mes_tgu(self):
    
        hoy = dt.date.today()
        mes = str(hoy - dt.timedelta(days=30)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', mes),('region', '=', "TGU")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', mes),('region', '=', "TGU")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', mes),('region', '=', "TGU")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', mes),('region', '=', "TGU")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', mes),('region', '=', "TGU")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
      #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', mes),('region', '=', "TGU")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', mes),('region', '=', "TGU")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', mes),('region', '=', "TGU")])
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
    
    @http.route(f'/control_visitas_anio_tgu', type='json', auth='public', website=True)
    def control_visitas_dashboard_anio_tgu(self):
      
        hoy = dt.date.today()
        anio = str(hoy - dt.timedelta(days=365)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', anio),('region', '=', "TGU")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', anio),('region', '=', "TGU")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', anio),('region', '=', "TGU")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', anio),('region', '=', "TGU")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', anio),('region', '=', "TGU")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', anio),('region', '=', "TGU")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', anio),('region', '=', "TGU")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', anio),('region', '=', "TGU")])
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
    @http.route(f'/control_visitas_sps', type='json', auth='public', website=True)
    def control_visitas_dashboard_sps(self):
      
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
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
    
    @http.route(f'/control_visitas_dia_sps', type='json', auth='public', website=True)
    def control_visitas_dashboard_dia_sps(self):
      
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '=', dt.date.today()),('region', '=', "SPS")])
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
    
    @http.route(f'/control_visitas_semana_sps', type='json', auth='public', website=True)
    def control_visitas_dashboard_semana_sps(self):
      
        hoy = dt.date.today()
        semana = str(hoy - dt.timedelta(days=7)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', semana),('region', '=', "SPS")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', semana),('region', '=', "SPS")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', semana),('region', '=', "SPS")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', semana),('region', '=', "SPS")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', semana),('region', '=', "SPS")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', semana),('region', '=', "SPS")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', semana),('region', '=', "SPS")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', semana),('region', '=', "SPS")])
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
    
    @http.route(f'/control_visitas_mes_sps', type='json', auth='public', website=True)
    def control_visitas_dashboard_mes_sps(self):
    
        hoy = dt.date.today()
        mes = str(hoy - dt.timedelta(days=30)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', mes),('region', '=', "SPS")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', mes),('region', '=', "SPS")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', mes),('region', '=', "SPS")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', mes),('region', '=', "SPS")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', mes),('region', '=', "SPS")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
      #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', mes),('region', '=', "SPS")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', mes),('region', '=', "SPS")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', mes),('region', '=', "SPS")])
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
    
    @http.route(f'/control_visitas_anio_sps', type='json', auth='public', website=True)
    def control_visitas_dashboard_anio_sps(self):
      
        hoy = dt.date.today()
        anio = str(hoy - dt.timedelta(days=365)) + ' '
        
        admin = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Administración'), ('fecha', '>', anio),('region', '=', "SPS")])
        admin_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Administración')])
        admin_ls = [data.name for data in admin_name]
        #..........................................    
        megatk = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Megatk'), ('fecha', '>', anio),('region', '=', "SPS")])
        megatk_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Megatk')])
        megatk_ls = [data.name for data in megatk_name]
        #..........................................    
        meditek = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Tienda Meditek'), ('fecha', '>', anio),('region', '=', "SPS")])
        meditek_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Tienda Meditek')])
        meditek_ls = [data.name for data in meditek_name]
        #..........................................    
        lenka = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Lenka'), ('fecha', '>', anio),('region', '=', "SPS")])
        lenka_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Lenka')])
        lenka_ls = [data.name for data in lenka_name]
        #..........................................    
        clinica = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Clínica'), ('fecha', '>', anio),('region', '=', "SPS")])
        clinica_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Clínica')])
        clinica_ls = [data.name for data in clinica_name]
        #..........................................    
        gerencia = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Gerencia'), ('fecha', '>', anio),('region', '=', "SPS")])
        gerencia_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Gerencia')])
        gerencia_ls = [data.name for data in gerencia_name]
        #..........................................    
        soporte = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Soporte'), ('fecha', '>', anio),('region', '=', "SPS")])
        soporte_name = request.env["control.visitas"].search(
            [('name', '=', 'Visita Soporte')])
        soporte_ls = [data.name for data in soporte_name]
        #..........................................    
        otros = request.env["control.visitas"].search_count(
            [('name', '=', 'Visita Otros'), ('fecha', '>', anio),('region', '=', "SPS")])
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
    
    
    @http.route(f'/control_visitas_user_reg', type='json', auth='public', website=True)
    def user_region(self) :
        user_reg = request.env.user.ubicacion_vendedor
        user_email = request.env.user.login
        
        return {
                "user_reg": user_reg,
                "user_email": user_email  
                }