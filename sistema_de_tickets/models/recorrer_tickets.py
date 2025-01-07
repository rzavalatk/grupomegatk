from odoo import models, fields
from collections import defaultdict
from odoo.exceptions import UserError
import logging
import math
import json
import time

class RecorrerTickets(models.Model):
    _name = 'recorrer.tickets'
    _description = 'Modelo para recorrer tickets'

    start_date = fields.Date(string='Fecha Inicio', required=True)
    end_date = fields.Date(string='Fecha Fin', required=True)

    def recorrer_tickets(self):
        """
        Método que será ejecutado al presionar el botón.
        """
        for record in self:
            if record.start_date > record.end_date:
                raise UserError("La fecha de inicio no puede ser mayor a la fecha de fin.")

            # Realizar la búsqueda de facturas
            facturas = self.env['account.move'].search([
                ('state', '=', 'posted'),  # Solo facturas publicadas
                ('move_type', '=', 'out_invoice'),  # Solo facturas de clientes
                ('invoice_date', '>=', record.start_date),  # Fecha de inicio
                ('invoice_date', '<=', record.end_date),  # Fecha de fin
                ('amount_total', '>', 1000),  # Monto mayor a 1000
            ])
            
            sorteo_id = self.env['sorteo.sorteo'].search([('name', '=', 'RIFA CLINICA DENTAL 2024')])
            
            
            
            
            
            #if self.sorteo_id and self.sorteo_id.compañia.id == self.company_id.id:
            if facturas:
                
                for factura in facturas:
                    
                    tickets = 0
                    flag = False
                    dia_festivo = False
            
                    if record.start_date <= factura.invoice_date <= record.end_date:
                        
                        if factura.amount_total >= 1000:
                            #({'ticket': "ticket x1"})
                            
                            tickets = math.floor(factura.amount_total / 1000)
                            
                            for fechas in sorteo_id.fechas_festivas:
                                if factura.invoice_date == fechas.fecha:
                                    #({'ticket': "ticket x2"})
                                    tickets = tickets * 2
                                    flag = True
                                    dia_festivo = True
                                    break
                            
                            #_logger.warning("Generando ticket 1")  

                            for move_line in factura.line_ids:
                                if not flag:
                                    for marca in sorteo_id.marcas:
                                        if not flag:
                                            if move_line.product_id.marca_id.name:
                                                if marca.marcas.name:
                                                    if move_line.product_id.marca_id.name == marca.marcas.name:
                                                        
                                                        if marca.fecha_inicial <= factura.invoice_date <= marca.fecha_final:
                                                            #({'ticket': "ticket x2"})
                                                            tickets = tickets* 2
                                                            flag = True
                                                            break
                                        
                                    for producto in sorteo_id.productos:
                                        if not flag:
                                            if move_line.product_id.name == producto.product.name:
                                                if producto.fecha_inicial <= factura.invoice_date <= producto.fecha_final:
                                                    tickets = tickets* 2
                                                    flag = True
                                                    break
                                            
                            if factura.x_student:
                                #({'ticket': "ticket 3"})
                                tickets = tickets * 3

                        # Crear los registros de tickets
                        for ticket_data in range(tickets):
                            # Cambiar 'move_line_id' por 'name' o algún otro campo significativo
                            self.env['sorteo.ticket'].create({
                                'move_id': factura.id,
                                'name': sorteo_id.sequence_id.prefix + '%%0%sd' % sorteo_id.sequence_id.padding % sorteo_id.sequence_id.number_next_actual,
                                'sorteo': sorteo_id.id,
                                'customer_id': factura.partner_id.id,
                                'fecha': factura.invoice_date,
                            })
                            
                            # Incrementa el número de la secuencia para el próximo ticket
                            sorteo_id.sequence_id.sudo().write({'number_next_actual': sorteo_id.sequence_id.number_next_actual + 1})
                
                
