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
    
    def _load_puntaje_rules(self):
        # Definir las reglas de puntaje directamente en el código
        rules = {
            'evolis': {
                'evl_1': {
                    'taller': 8,
                    'visita': 10,
                    'llamada': 5,
                },
                'evl_2': {
                    'taller': 6,
                    'visita': 8,
                    'llamada': 5,
                },
                'evl_3': {
                    'taller': 5,
                    'visita': 7,
                    'llamada': 7,
                },
                'evl_4': {
                    'taller': 5,
                    'visita': 7,
                    'llamada': 7,
                },'evl_5': {
                    'taller': 5,
                    'visita': 7,
                    'llamada': 7,
                },'evl_6': {
                    'taller': 5,
                    'visita': 7,
                    'llamada': 7,
                },
            },
            'zebra': {
                'zeb_1': {
                    'taller': 9,
                    'visita': 12,
                    'llamada': 6,
                },
                'zeb_2': {
                    'taller': 7,
                    'visita': 9,
                    'llamada': 6,
                },
                
            },
            'pos': {
                'pos_1': {
                    'taller': 7,
                    'visita': 9,
                    'llamada': 4,
                },
                
            },
            'etiquetas': {
                'etq_1': {
                    'taller': 6,
                    'visita': 8,
                    'llamada': 4,
                },
                
            },
            'ploter': {
                'plt_1': {
                    'taller': 7,
                    'visita': 10,
                    'llamada': 6,
                },
                'plt_2': {
                    'taller': 7,
                    'visita': 10,
                    'llamada': 6,
                },
                'plt_3': {
                    'taller': 7,
                    'visita': 10,
                    'llamada': 6,
                },  
            },
            'traslados': {
                'tls_1': {
                    'taller': 5,
                    'visita': 7,
                    'llamada': 5,
                },
               
            },
            # Agrega más marcas aquí si es necesario
        }
        return rules

    def generate_report(self):
        rules = self._load_puntaje_rules()

        domain = [
            ('date_deadline', '>=', self.fecha_inicio),
            ('date_deadline', '<=', self.fecha_final),
            ('puntuado', '=', False),
            ('user_id', 'in', self.users_ids.ids),
            ('stage_id', '=', 4)
        ]
            
        tickets = self.env['crm.lead'].search(domain)

        #_logger.warning("tamaño de products idsg: " + str(len(tickets)))

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
                marca = ticket.marca
                servicios = [ticket.servicio_evolis, ticket.servicio_zebra, ticket.servicio_pos, 
                            ticket.servicio_etiquetas, ticket.servicio_ploter, ticket.servicio_traslado]
                
                servicio = ""
                tipo = ticket.tipo_servicio  # 'taller', 'visita', 'llamada'
                points_taller = 0
                points_llamada = 0
                points_visita = 0
                
                for item in servicios:
                    if item:
                        indice = servicios.index(item)
                        if indice == 0:
                            servicio_str = "servicio_evolis"
                        elif indice == 1:
                            servicio_str = "servicio_zebra"
                        elif indice == 2:
                            servicio_str = "servicio_pos"
                        elif indice == 3:
                            servicio_str = "servicio_etiquetas"
                        elif indice == 4:
                            servicio_str = "servicio_ploter"
                        elif indice == 5:
                            servicio_str = "servicio_traslado"
                        
                        servicio = item

                if marca in rules and servicio in rules[marca]:
                    puntos = rules[marca][servicio].get(tipo, 0)
                    
                    owner = ticket.user_id
                    assistant_1 = ticket.tecnico_asistente_1
                    assistant_2 = ticket.tecnico_asistente_2
                    
                    p_dueño = 1
                    porcentaje_1 = float(ticket.porcentaje1)
                    porcentaje_2 = float(ticket.porcentaje2)
                    
                    servicio_string =dict(ticket._fields[servicio_str].selection)[servicio]

                    if not assistant_1 and not assistant_2:
                        
                        if tipo == 'taller':
                            points_taller = puntos
                            self._add_points(user_points_taller, owner, puntos)
                        elif tipo == 'visita':
                            points_visita = puntos
                            self._add_points(user_points_visita, owner, puntos)
                        elif tipo == 'llamada':
                            points_llamada = puntos
                            self._add_points(user_points_llamada, owner, puntos)
                        
                        self._add_points(user_points, owner, puntos)
                        self._track_top_service(user_top_service, user_top_marca, owner, servicio, marca, puntos, servicio_string)
                        
                    elif assistant_1 and not assistant_2:
                        
                        if porcentaje_1:
                            p_dueño = 1 - porcentaje_1
                            if tipo == 'taller':
                                points_taller = puntos
                                self._add_points(user_points_taller, owner, puntos * p_dueño)
                                self._add_points(user_points_taller, assistant_1, puntos * porcentaje_1)
                            elif tipo == 'visita':
                                points_visita = puntos 
                                self._add_points(user_points_visita, owner, puntos * p_dueño)
                                self._add_points(user_points_visita, assistant_1, puntos * porcentaje_1)
                            elif tipo == 'llamada':
                                points_llamada = puntos
                                self._add_points(user_points_llamada, owner, puntos * p_dueño)
                                self._add_points(user_points_llamada, assistant_1, puntos * porcentaje_1)
                            
                            self._add_points(user_points, owner, puntos * p_dueño)
                            self._add_points(user_points, assistant_1, puntos * porcentaje_1)
                            self._track_top_service(user_top_service, user_top_marca, owner, servicio, marca, puntos * p_dueño, servicio_string)
                            self._track_top_service(user_top_service, user_top_marca, assistant_1, servicio, marca, puntos * porcentaje_1, servicio_string)
                            
                    elif assistant_1 and assistant_2:
                        if porcentaje_1 and porcentaje_2:
                            if porcentaje_1 + porcentaje_2 <= 0.5:
                                p_dueño = 1 - (porcentaje_1 + porcentaje_2)
                                if tipo == 'taller':
                                    points_taller = puntos
                                    self._add_points(user_points_taller, owner, puntos * p_dueño)
                                    self._add_points(user_points_taller, assistant_1, puntos * porcentaje_1)
                                    self._add_points(user_points_taller, assistant_2, puntos * porcentaje_2)
                                elif tipo == 'visita':
                                    points_visita = puntos
                                    self._add_points(user_points_visita, owner, puntos * p_dueño)
                                    self._add_points(user_points_visita, assistant_1, puntos * porcentaje_1)
                                    self._add_points(user_points_visita, assistant_2, puntos * porcentaje_2)
                                elif tipo == 'llamada':
                                    points_llamada = puntos
                                    self._add_points(user_points_llamada, owner, puntos * p_dueño)
                                    self._add_points(user_points_llamada, assistant_1, puntos * porcentaje_1)
                                    self._add_points(user_points_llamada, assistant_2, puntos * porcentaje_2)
                                
                                self._add_points(user_points, owner, puntos * p_dueño)
                                self._add_points(user_points, assistant_1, puntos * porcentaje_1)
                                self._add_points(user_points, assistant_2, puntos * porcentaje_2)
                                self._track_top_service(user_top_service, user_top_marca, owner, servicio, marca, puntos * p_dueño, servicio_string)
                                self._track_top_service(user_top_service, user_top_marca, assistant_1, servicio, marca, puntos * porcentaje_1, servicio_string)
                                self._track_top_service(user_top_service, user_top_marca, assistant_2, servicio, marca, puntos * porcentaje_2, servicio_string)
                            else:
                                if porcentaje_1 > porcentaje_2:
                                    porcentaje_2 = 0.5 -porcentaje_1
                                    p_dueño = 1 - (porcentaje_1 + porcentaje_2)
                                    if tipo == 'taller':
                                        points_taller = puntos
                                        self._add_points(user_points_taller, owner, puntos * p_dueño)
                                        self._add_points(user_points_taller, assistant_1, puntos * porcentaje_1)
                                        self._add_points(user_points_taller, assistant_2, puntos * porcentaje_2)
                                    elif tipo == 'visita':
                                        points_visita = puntos
                                        self._add_points(user_points_visita, owner, puntos * p_dueño)
                                        self._add_points(user_points_visita, assistant_1, puntos * porcentaje_1)
                                        self._add_points(user_points_visita, assistant_2, puntos * porcentaje_2)
                                    elif tipo == 'llamada':
                                        points_llamada = puntos
                                        self._add_points(user_points_llamada, owner, puntos * p_dueño)
                                        self._add_points(user_points_llamada, assistant_1, puntos * porcentaje_1)
                                        self._add_points(user_points_llamada, assistant_2, puntos * porcentaje_2)
                                    
                                    self._add_points(user_points, owner, puntos * p_dueño)
                                    self._add_points(user_points, assistant_1, puntos * porcentaje_1)
                                    self._add_points(user_points, assistant_2, puntos * porcentaje_2)
                                    self._track_top_service(user_top_service, user_top_marca, owner, servicio, marca, puntos * p_dueño, servicio_string)
                                    self._track_top_service(user_top_service, user_top_marca, assistant_1, servicio, marca, puntos * porcentaje_1, servicio_string)
                                    self._track_top_service(user_top_service, user_top_marca, assistant_2, servicio, marca, puntos * porcentaje_2, servicio_string)
                                else:
                                    porcentaje_1 = 0.5 - porcentaje_2
                                    p_dueño = 1 - (porcentaje_1 + porcentaje_2)
                                    if tipo == 'taller':
                                        points_taller = puntos
                                        self._add_points(user_points_taller, owner, puntos * p_dueño)
                                        self._add_points(user_points_taller, assistant_1, puntos * porcentaje_1)
                                        self._add_points(user_points_taller, assistant_2, puntos * porcentaje_2)
                                    elif tipo == 'visita':
                                        points_visita = puntos
                                        self._add_points(user_points_visita, owner, puntos * p_dueño)
                                        self._add_points(user_points_visita, assistant_1, puntos * porcentaje_1)
                                        self._add_points(user_points_visita, assistant_2, puntos * porcentaje_2)
                                    elif tipo == 'llamada':
                                        points_llamada = puntos
                                        self._add_points(user_points_llamada, owner, puntos * p_dueño)
                                        self._add_points(user_points_llamada, assistant_1, puntos * porcentaje_1)
                                        self._add_points(user_points_llamada, assistant_2, puntos * porcentaje_2)
                                    
                                    self._add_points(user_points, owner, puntos * p_dueño)
                                    self._add_points(user_points, assistant_1, puntos * porcentaje_1)
                                    self._add_points(user_points, assistant_2, puntos * porcentaje_2)
                                    self._track_top_service(user_top_service, user_top_marca, owner, servicio, marca, puntos * p_dueño, servicio_string)
                                    self._track_top_service(user_top_service, user_top_marca, assistant_1, servicio, marca, puntos * porcentaje_1, servicio_string)
                                    self._track_top_service(user_top_service, user_top_marca, assistant_2, servicio, marca, puntos * porcentaje_2, servicio_string)
                
                    lines_tickets.append((0, 0,{
                            'sistema_puntaje': self.id,
                            'tecnico_id': owner.id,
                            'rol': 'Tecnico',
                            'marcas_id': dict(ticket._fields['marca'].selection)[marca],
                            'servicio_id': dict(ticket._fields[servicio_str].selection)[servicio],
                            'taller_id': points_taller,
                            'visita_id': points_visita,
                            'llamada_id': points_llamada,
                            'ticket_id': ticket.id,
                        }))
                    
                    if assistant_1:
                        lines_tickets.append((0, 0,{
                            'sistema_puntaje': self.id,
                            'tecnico_id': assistant_1.id,
                            'rol': 'Asistente 1',
                            'marcas_id': dict(ticket._fields['marca'].selection)[marca],
                            'servicio_id': dict(ticket._fields[servicio_str].selection)[servicio],
                            'taller_id': points_taller * porcentaje_1,
                            'visita_id': points_visita * porcentaje_1,
                            'llamada_id': points_llamada * porcentaje_1,
                            'ticket_id': ticket.id,
                        }))
                    
                    if assistant_2:
                        lines_tickets.append((0, 0,{
                            'sistema_puntaje': self.id,
                            'tecnico_id': assistant_2.id,
                            'rol': 'Asistente 2',
                            'marcas_id': dict(ticket._fields['marca'].selection)[marca],
                            'servicio_id': dict(ticket._fields[servicio_str].selection)[servicio],
                            'taller_id': points_taller * porcentaje_2,
                            'visita_id': points_visita * porcentaje_2,
                            'llamada_id': points_llamada * porcentaje_2,
                            'ticket_id': ticket.id,
                        }))
                    
                    #ticket.sudo().write({'puntuado': True})                 

            lines = []
            for user in self.users_ids:
                
                total_points = user_points.get(user, 0)
                
                top_marca = user_top_marca.get(user, {'marca': '', 'points': 0})['marca']
                service_str = user_top_service.get(user, {'service': '', 'points': 0, 'service_str': ''})['service_str']
                
                # Agregar entrada a tabla_puntaje
                lines.append((0, 0,{
                    'sistema_puntaje': self.id,
                    'tecnico_id': user.id,
                    'marcas_id': top_marca,
                    'servicio_id':  service_str,
                    'taller_id': user_points_taller.get(user, 0),
                    'visita_id': user_points_visita.get(user, 0),
                    'llamada_id': user_points_llamada.get(user, 0),
                    'total': total_points,
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
        rules = self._load_puntaje_rules()

        domain = [
            ('date_deadline', '>=', self.fecha_inicio),
            ('date_deadline', '<=', self.fecha_final),
            ('puntuado', '=', False),
            ('user_id', 'in', self.users_ids.ids),
            ('stage_id', '=', 4)
        ]
            
        tickets_list = self.env['crm.lead'].search(domain)

        if tickets_list:
            
            for ticket_item in tickets_list:
                marca = ticket_item.marca
                servicios = [ticket_item.servicio_evolis, ticket_item.servicio_zebra, ticket_item.servicio_pos, 
                            ticket_item.servicio_etiquetas, ticket_item.servicio_ploter, ticket_item.servicio_traslado]
                
                servicio = ""       
                
                for item in servicios:
                    if item:
                        servicio = item

                if marca in rules and servicio in rules[marca]:
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
        encabezados_lines_puntaje = ['Tecnico', 'Marca mas atendida', 'Servicio mas solicitado', 'Puntos taller', 'Puntos visita', 'Puntos llamada', 'Total puntos']
        col_widths_lines_puntaje = [45, 35, 35, 20, 20, 20, 20]  # Ajusta estos valores según sea necesario
        
        encabezados_reports_detalles = ['Tecnico', 'Rol', 'Marca', 'Servicio', 'Puntos taller', 'Puntos visita', 'Puntos llamada']
        col_widths_reports_detalles = [45, 25, 35, 35, 25, 25, 25]  # Ajusta estos valores según sea necesario
        
        # Preparar los datos
        datos_lines_from_puntaje = [
            (
                record.tecnico_id.name,
                record.marcas_id,
                record.servicio_id,
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
