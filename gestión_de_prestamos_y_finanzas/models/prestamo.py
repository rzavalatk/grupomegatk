from odoo import models, fields, api
import math

class Prestamo(models.Model):
    _name = 'prestamo'
    _description = 'Modelo de Préstamo'

    name = fields.Char(string='Número de Préstamo', required=True, copy=False, readonly=True, default='Nuevo')
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
    monto = fields.Float(string='Monto del Préstamo', required=True)
    tasa_interes = fields.Float(string='Tasa de Interés', required=True)
    duracion = fields.Integer(string='Duración (meses)', required=True)
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True)
    frecuencia_pago = fields.Selection([
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual')
    ], string='Frecuencia de Pago', default='mensual', required=True)
    tipo_prestamo = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('comprado', 'Comprado'),
        ('refinanciado', 'Refinanciado'),
        ('adquirido', 'Adquirido')
    ], string='Tipo de Préstamo', required=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('pagado', 'Pagado')
    ], string='Estado', default='borrador', required=True)
    cuota_ids = fields.One2many('cuota', 'prestamo_id', string='Cuotas')
    contrato_id = fields.Many2one('contrato', string='Contrato')
    #garantia_ids = fields.One2many('garantia', 'prestamo_id', string='Garantías')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('prestamo') or 'Nuevo'
        result = super(Prestamo, self).create(vals)
        result.calcular_cuotas()
        return result

    def calcular_cuotas(self):
        for prestamo in self:
            cantidad_cuotas = prestamo.duracion
            monto_cuota = self.calcular_monto_cuota(prestamo.monto, prestamo.tasa_interes, prestamo.duracion)
            fecha_cuota = prestamo.fecha_inicio
            for i in range(1, cantidad_cuotas + 1):
                self.env['cuota'].create({
                    'prestamo_id': prestamo.id,
                    'monto': monto_cuota,
                    'fecha_vencimiento': fecha_cuota,
                })
                fecha_cuota = self.sumar_periodo(fecha_cuota, prestamo.frecuencia_pago)

    def calcular_monto_cuota(self, monto, tasa, duracion):
        tasa_mensual = (tasa / 100) / 12
        return monto * tasa_mensual / (1 - (1 + tasa_mensual) ** -duracion)

    def sumar_periodo(self, fecha, frecuencia):
        if frecuencia == 'diario':
            return fields.Date.add(fecha, days=1)
        elif frecuencia == 'semanal':
            return fields.Date.add(fecha, weeks=1)
        elif frecuencia == 'quincenal':
            return fields.Date.add(fecha, days=15)
        elif frecuencia == 'mensual':
            return fields.Date.add(fecha, months=1)
        elif frecuencia == 'bimestral':
            return fields.Date.add(fecha, months=2)
        elif frecuencia == 'trimestral':
            return fields.Date.add(fecha, months=3)
        elif frecuencia == 'anual':
            return fields.Date.add(fecha, years=1)

    def exportar_excel(self):
        # Crear un archivo en memoria
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Escribir datos en el archivo Excel
        worksheet.write(0, 0, 'Número de Préstamo')
        worksheet.write(0, 1, 'Cliente')
        worksheet.write(0, 2, 'Monto')
        worksheet.write(0, 3, 'Tasa de Interés')
        worksheet.write(0, 4, 'Duración (meses)')
        worksheet.write(0, 5, 'Fecha de Inicio')
        worksheet.write(0, 6, 'Frecuencia de Pago')
        worksheet.write(0, 7, 'Tipo de Préstamo')

        row = 1
        for prestamo in self:
            worksheet.write(row, 0, prestamo.name)
            worksheet.write(row, 1, prestamo.cliente_id.name)
            worksheet.write(row, 2, prestamo.monto)
            worksheet.write(row, 3, prestamo.tasa_interes)
            worksheet.write(row, 4, prestamo.duracion)
            worksheet.write(row, 5, str(prestamo.fecha_inicio))
            worksheet.write(row, 6, dict(prestamo._fields['frecuencia_pago'].selection).get(prestamo.frecuencia_pago))
            worksheet.write(row, 7, dict(prestamo._fields['tipo_prestamo'].selection).get(prestamo.tipo_prestamo))
            row += 1

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        # Crear el adjunto en Odoo y devolver el enlace de descarga
        attachment = self.env['ir.attachment'].create({
            'name': f'Prestamo_{self.name}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'store_fname': f'Prestamo_{self.name}.xlsx',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }