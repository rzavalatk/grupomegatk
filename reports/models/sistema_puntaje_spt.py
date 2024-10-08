from odoo import models, fields, api
from datetime import datetime

import logging
import base64
import io
from odoo.tools.misc import xlsxwriter

_logger = logging.getLogger(__name__)

class SistemaPuntajeSoporte(models.Model):
    _name = 'sistema.puntaje.soporte'
    _description = 'Sistema de puntaje para comisiones de soporte tecnico'

    def _compute_name(self):
        for record in self:
            record.name = 'Puntaje del ' + str(record.fecha_inicio) + ' al ' + str(record.fecha_final) + ' de ' + str(record.company_id.name)  

    name = fields.Char("Nombre", compute='_compute_name')
    company_id = fields.Many2one(
        "res.company", "Compañia", default=lambda self: self.env.user.company_id.id)
    users_ids = fields.Many2many("res.users", "puntaje_id", string="Usuarios")
    fecha_inicio = fields.Date('Fecha inicial')
    fecha_final = fields.Date('Fecha final')
    
    state = fields.Selection([
        ("borrador", "Borrador"),
        ("hecho", "Hecho"),
        ("cancelado", "Cancelado")
    ], string="Estado", default="borrador")
    
    tabla_puntaje = fields.One2many(
        'sistema.tabla.puntaje', 'sistema_puntaje', string="Tabla de puntos", readonly=True)
    
    tabla_detalle = fields.One2many(
        'sistema.detalles.puntaje', 'sistema_puntaje', string="Detalles", readonly=True)
    
    tickets_ids = []
    

    def generate_report(self):

        domain = [
            ('date_deadline', '>=', self.fecha_inicio),
            ('date_deadline', '<=', self.fecha_final),
            ('puntuado', '=', False),
            ('user_id', 'in', self.users_ids.ids),
            ('stage_id', '=', 4)
        ]
            
        tickets = self.env['crm.lead'].search(domain)

        #_logger.warning("tamaño de products idsg: " + str(len(tickets)))

        porcentaje_tecnico = 1
        porcentaje_asis1 = 0
        porcentaje_asis2 = 0
        porcentaje_asis3 = 0
        user_points_taller = {}
        user_points_visita = {}
        user_points_llamada = {}
        user_points = {}
        user_top_service = {}
        user_top_marca = {}
       
        if not self.users_ids:
            raise Warning(_('No hay usuarios para puntuar'))

        if tickets:
            lines_tickets = []
            servicio_str = ""
            
            for ticket in tickets:
                marca = ticket.marca_spt
                servicio = ticket.servicio_spt
                tipo = ticket.tipo_servicio  # 'taller', 'visita', 'llamada'
                points_taller = 0
                points_llamada = 0
                points_visita = 0
                
                if marca:          
                    if tipo == 'taller':
                        points_taller = servicio.puntaje_taller
                        points_visita = 0
                        points_llamada = 0
                    elif tipo == 'visita':
                        points_taller = 0
                        points_visita = servicio.puntaje_visita
                        points_llamada = 0
                    elif tipo == 'llamada':
                        points_taller = 0
                        points_visita = 0
                        points_llamada = servicio.puntaje_llamada
                    else:
                        raise Warning(_('Error en el sistema de puntaje: tipo de servicio no definido'))

                    #Calculo de porcentajesf
                    if ticket.tecnico_asistente_3:
                        porcentaje_tecnico = 0.25
                        porcentaje_asis1 = 0.25
                        porcentaje_asis2 = 0.25
                        porcentaje_asis3 = 0.25
                    elif ticket.tecnico_asistente_2:
                        porcentaje_tecnico = 0.4
                        porcentaje_asis1 = 0.3
                        porcentaje_asis2 = 0.3
                    elif ticket.tecnico_asistente_1:
                        porcentaje_tecnico = 0.5
                        porcentaje_asis1 = 0.5
                    
                    
                    
                    lines_tickets.append((0, 0,{
                            'sistema_puntaje': self.id,
                            'tecnico_id': ticket.user_id.id,
                            'rol': 'Tecnico',
                            'marcas_id': ticket.marca_spt.name,
                            'servicio_id': ticket.servicio_spt.name,
                            'taller_id': points_taller * porcentaje_tecnico,
                            'visita_id': points_visita * porcentaje_tecnico,
                            'llamada_id': points_llamada * porcentaje_tecnico,
                            'ticket_id': ticket.id,
                        }))
                    
                    self._add_points(user_points_taller, ticket.user_id, points_taller * porcentaje_tecnico)
                    self._add_points(user_points_visita, ticket.user_id, points_visita * porcentaje_tecnico)
                    self._add_points(user_points_llamada, ticket.user_id, points_llamada * porcentaje_tecnico)
                    
                    if ticket.tecnico_asistente_1:
                        lines_tickets.append((0, 0,{
                            'sistema_puntaje': self.id,
                            'tecnico_id': ticket.tecnico_asistente_1.id,
                            'rol': 'Asistente',
                            'marcas_id': ticket.marca_spt.name,
                            'servicio_id': ticket.servicio_spt.name,
                            'taller_id': points_taller * porcentaje_asis1,
                            'visita_id': points_visita * porcentaje_asis1,
                            'llamada_id': points_llamada * porcentaje_asis1,
                            'ticket_id': ticket.id,
                        }))
                        
                        self._add_points(user_points_taller, ticket.tecnico_asistente_1, points_taller * porcentaje_asis1)
                        self._add_points(user_points_visita, ticket.tecnico_asistente_1, points_visita * porcentaje_asis1)
                        self._add_points(user_points_llamada, ticket.tecnico_asistente_1, points_llamada * porcentaje_asis1)
                    
                    if ticket.tecnico_asistente_2:
                        lines_tickets.append((0, 0,{
                            'sistema_puntaje': self.id,
                            'tecnico_id': ticket.tecnico_asistente_2.id,
                            'rol': 'Asistente',
                            'marcas_id': str(ticket.marca_spt.name),
                            'servicio_id': str(ticket.servicio_spt.name),
                            'taller_id': points_taller * porcentaje_asis2,
                            'visita_id': points_visita * porcentaje_asis2,
                            'llamada_id': points_llamada * porcentaje_asis2,
                            'ticket_id': ticket.id,
                        }))
                        
                        self._add_points(user_points_taller, ticket.tecnico_asistente_2, points_taller * porcentaje_asis2)
                        self._add_points(user_points_visita, ticket.tecnico_asistente_2, points_visita * porcentaje_asis2)
                        self._add_points(user_points_llamada, ticket.tecnico_asistente_2, points_llamada * porcentaje_asis2)
                        
                    if ticket.tecnico_asistente_3:
                        lines_tickets.append((0, 0,{
                            'sistema_puntaje': self.id,
                            'tecnico_id': ticket.tecnico_asistente_3.id,
                            'rol': 'Asistente',
                            'marcas_id': ticket.marca_spt.name,
                            'servicio_id': ticket.servicio_spt.name,
                            'taller_id': points_taller * porcentaje_asis3,
                            'visita_id': points_visita * porcentaje_asis3,
                            'llamada_id': points_llamada * porcentaje_asis3,
                            'ticket_id': ticket.id,
                        }))
                        
                        self._add_points(user_points_taller, ticket.tecnico_asistente_3, points_taller * porcentaje_asis3)
                        self._add_points(user_points_visita, ticket.tecnico_asistente_3, points_visita * porcentaje_asis3)
                        self._add_points(user_points_llamada, ticket.tecnico_asistente_3, points_llamada * porcentaje_asis3)
                    
                    #ticket.sudo().write({'puntuado': True})   
                    self.tickets_ids.append(ticket.id)

            lines = []
            for user in self.users_ids:
                
                total_points = user_points.get(user, 0)
                
                top_marca = user_top_marca.get(user, {'marca': '', 'points': 0})['marca']
                service_str = user_top_service.get(user, {'service': '', 'points': 0, 'service_str': ''})['service_str']
                
                # Agregar entrada a tabla_puntaje
                lines.append((0, 0,{
                    'sistema_puntaje': self.id,
                    'tecnico_id': user.id,
                    'taller_id': user_points_taller.get(user, 0),
                    'visita_id': user_points_visita.get(user, 0),
                    'llamada_id': user_points_llamada.get(user, 0),
                    'total': user_points_taller.get(user, 0) + user_points_visita.get(user, 0) + user_points_llamada.get(user, 0)
                    # Asegúrate de manejar los campos de taller, visita y llamada como sea necesario
                }))
            
            self.tabla_puntaje = lines
            self.tabla_detalle = lines_tickets

    def _add_points(self, user_points, user, points):
        if user:
            if user in user_points:
                user_points[user] += points
            else:
                user_points[user] = points

    def _track_top_service(self, user_top_service, user_top_marca, user, service, marca, points, service_str):
        if user:
            if user not in user_top_service:
                user_top_service[user] = {'service': service, 'points': points, 'service_str': service_str}
                user_top_marca[user] = {'marca': marca, 'points': points}
            else:
                if user_top_service[user]['points'] < points:
                    user_top_service[user] = {'service': service, 'points': points, 'service_str': service_str}
                    user_top_marca[user] = {'marca': marca, 'points': points}
        """
        Realiza el seguimiento del servicio superior para un usuario determinado en función de los puntos obtenidos.

        Args:
            user_top_service (dict): Un diccionario para almacenar el servicio superior para cada usuario.
            user (res.users): El usuario para el cual se está realizando el seguimiento del servicio superior.
            service (str): El servicio para el cual se están rastreando los puntos.
            points (int): Los puntos obtenidos por el usuario para el servicio.

        Returns:
            None
        """
    
    def action_confirm(self):
        

        domain = [
            ('date_deadline', '>=', self.fecha_inicio),
            ('date_deadline', '<=', self.fecha_final),
            ('puntuado', '=', False),
            ('user_id', 'in', self.users_ids.ids),
            ('stage_id', '=', 4)
        ]
            
        tickets_list = self.env['crm.lead'].search([('id', 'in', self.tickets_ids)])

        if tickets_list:
            
            for ticket_item in tickets_list:
                if ticket_item.marca_spt:
                    ticket_item.write({'puntuado': True})
        
        self.state = 'hecho'
    
    def exportar_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Crear hojas de Excel
        worksheet_puntaje = workbook.add_worksheet('Tabla de puntajes')
        worksheet_detalles = workbook.add_worksheet(f'Tabla de detallado de tickets')

        # Definir formatos
        header_format = workbook.add_format({'bold': True, 'align': 'center'})
        
        # Función para escribir encabezados y datos en una hoja y ajustar el tamaño de las columnas
        def escribir_hoja(worksheet, encabezados, datos, col_widths):
            # Ajustar el tamaño de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)
            
            # Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado, header_format)
            
            # Escribir los datos
            row = 1
            for record in datos:
                for col, value in enumerate(record):
                    worksheet.write(row, col, value)
                row += 1

        # Encabezados y anchos de columnas
        encabezados_lines_puntaje = ['Tecnico','Puntos taller', 'Puntos visita', 'Puntos llamada', 'Total puntos']
        col_widths_lines_puntaje = [45, 20, 20, 20, 20]  # Ajusta estos valores según sea necesario
        
        encabezados_reports_detalles = ['Tecnico', 'Rol', 'Marca', 'Servicio', 'Puntos taller', 'Puntos visita', 'Puntos llamada']
        col_widths_reports_detalles = [45, 25, 35, 35, 25, 25, 25]  # Ajusta estos valores según sea necesario
        
        # Preparar los datos
        datos_lines_from_puntaje = [
            (
                record.tecnico_id.name,
                record.taller_id,
                record.visita_id,
                record.llamada_id,
                record.total,
            )
            for record in self.tabla_puntaje
        ]
        
        datos_lines_to_detalles = [
            (
                record.tecnico_id.name,
                record.rol,
                record.marcas_id,
                record.servicio_id,
                record.taller_id,
                record.visita_id,
                record.llamada_id,
                
            )
            for record in self.tabla_detalle
        ]
        
        # Escribir datos en las hojas correspondientes y ajustar el tamaño de las columnas
        escribir_hoja(worksheet_puntaje, encabezados_lines_puntaje, datos_lines_from_puntaje, col_widths_lines_puntaje)
        escribir_hoja(worksheet_detalles, encabezados_reports_detalles, datos_lines_to_detalles, col_widths_reports_detalles)
        
        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': f'reporte_puntaje_spt_{self.fecha_inicio}_{self.fecha_final}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': f'reporte_puntaje_spt_{self.fecha_inicio}_{self.fecha_final}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Devolver la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    
class TablaPuntaje(models.Model):
    _name = "sistema.tabla.puntaje"
    _description = "Tabla de puntaje del sistema para puntuar comisiones a soporte"

    sistema_puntaje = fields.Many2one(
        'sistema.puntaje.soporte', string="Tabla de puntos", ondelete='cascade')

    tecnico_id = fields.Many2one('res.users', string='Tecnico')
    marcas_id = fields.Char('Marca mas puntuada')
    servicio_id = fields.Char('Servicio mas puntuado')
    taller_id = fields.Float('Puntos taller')
    visita_id = fields.Float('Puntos visita')
    llamada_id = fields.Float('Puntos llamada')
    total = fields.Float('Total')

class PuntajeDetalles(models.Model):
    _name = "sistema.detalles.puntaje"
    _description = "Resumen detallado de los tickets puntuados"

    sistema_puntaje = fields.Many2one(
        'sistema.puntaje.soporte', string="Detalles", ondelete='cascade')

    tecnico_id = fields.Many2one('res.users', string='Tecnico')
    rol = fields.Char('Rol')
    ticket_id = fields.Many2one('crm.lead', string='Ticket')
    marcas_id = fields.Char('Marca ')
    servicio_id = fields.Char('Servicio')
    taller_id = fields.Float('Puntos taller')
    visita_id = fields.Float('Puntos visita')
    llamada_id = fields.Float('Puntos llamada')
