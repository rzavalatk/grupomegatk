from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import pdf
from datetime import date, datetime
import logging
import pytz

_logger = logging.getLogger(__name__)

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre')
    fecha = fields.Date(string='Fecha', compute='_compute_fecha', store=True)
    hora = fields.Char(string='Hora', compute='_compute_hora', store=True)
    region = fields.Char(string='Region', compute='_compute_region', store=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    registro_visita = fields.Many2one('registro.visitas', string='Visitas Diarias')
    
    @api.depends('user_id')
    def _compute_region(self):
        for record in self:
            if record.user_id.ubicacion_vendedor == '3':
                record.region = 'TGU'
            if record.user_id.ubicacion_vendedor == '2':
                record.region = 'SPS'

    @api.depends('user_id')
    def _compute_fecha(self):
        for record in self:
            record.fecha = date.today()
            
    @api.depends('user_id')
    def _compute_hora(self):
        for record in self:
            hora_utc = datetime.now(pytz.utc)
            
            zona_horaria_usuario = self.env.user.tz or 'UTC'
            
            if hasattr(zona_horaria_usuario, 'zone'):
                zona_horaria = zona_horaria_usuario
            else:
                zona_horaria = pytz.timezone(zona_horaria_usuario)
            
            hora_local = hora_utc.astimezone(zona_horaria).strftime('%H:%M:%S')
            _logger.warning(f"Hora local: {zona_horaria_usuario}")
            record.hora = hora_local
 
    @api.model
    def create(self, vals):
         user = self.env.user
         if user.ubicacion_vendedor == "2" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
             raise ValidationError("No se puede registrar esta visita en SPS")
         return super(Visitas, self).create(vals)  
      
    @api.model   
    def visita_administracion(self, admin):
        self.create({'name': 'Visita Administración'})
            
    @api.model
    def visita_tienda_megatk(self, vals):
        self.create({'name': 'Visita Tienda Megatk'})

    @api.model
    def visita_tienda_meditek(self, vals):    
        self.create({'name': 'Visita Tienda Meditek'})
    
    @api.model
    def visita_lenka(self, vals):    
        self.create({'name': 'Visita Lenka'})
    
    @api.model
    def visita_clinica(self, vals):
        self.env['control.visitas'].create({'name': 'Visita Clínica'})
    
    @api.model
    def visita_gerencia(self, vals):
        self.env['control.visitas'].create({'name': 'Visita Gerencia'})
    
    @api.model
    def visita_soporte(self, vals):
        self.env['control.visitas'].create({'name': 'Visita Soporte'})
    
    @api.model
    def visita_otros(self, vals):
        self.env['control.visitas'].create({'name': 'Visita Otros'})
        
    @api.model    
    def send_email(self, email=None, cc="", contexto={}):
        template = self.env.ref(
            'control_visitas.email_template_registro_visitas')
        email_values = {
            'email_to': email,
            'email_cc': cc, 
            'body_html': contexto
        }
            
        template.send_mail(self.id, email_values=email_values, force_send=True)
        self.write({
            'state': 'done'
        })
        return True
    
    @api.model
    def datos(self):
        html = ""
        registros = self.env['control.visitas'].search([('fecha', '=', date.today())])
        
        admin_TGU = self.env['control.visitas'].search_count([('name', '=', "Visita Administración"),('fecha', '=', date.today()),('region', '=', 'TGU')])
        megatk_TGU = self.env['control.visitas'].search_count([('name', '=', "Visita Tienda Megatk"),('fecha', '=', date.today()),('region', '=', 'TGU')])
        meditek_TGU = self.env['control.visitas'].search_count([('name', '=', "Visita Tienda Meditek"),('fecha', '=', date.today()),('region', '=', 'TGU')])
        lenka_TGU = self.env['control.visitas'].search_count([('name', '=', "Visita Lenka"),('fecha', '=', date.today()),('region', '=', 'TGU')])
        clinica_TGU = self.env['control.visitas'].search_count([('name', '=', "Visita Clínica"),('fecha', '=', date.today()),('region', '=', 'TGU')])
        gerencia_TGU = self.env['control.visitas'].search_count([('name', '=', "Visita Gerencia"),('fecha', '=', date.today()),('region', '=', 'TGU')])
        soporte_TGU = self.env['control.visitas'].search_count([('name', '=', "Visita Soporte"),('fecha', '=', date.today()),('region', '=', 'TGU')])
        otros_TGU = self.env['control.visitas'].search_count([('name', '=', "Visita Otros"),('fecha', '=', date.today()),('region', '=', 'TGU')])
        total_TGU = self.env['control.visitas'].search_count([('fecha', '=', date.today()),('region', '=', 'TGU')])
        
        
        admin_SPS = self.env['control.visitas'].search_count([('name', '=', "Visita Administración"),('fecha', '=', date.today()),('region', '=', 'SPS')])
        megatk_SPS = self.env['control.visitas'].search_count([('name', '=', "Visita Tienda Megatk"),('fecha', '=', date.today()),('region', '=', 'SPS')])
        meditek_SPS = self.env['control.visitas'].search_count([('name', '=', "Visita Tienda Meditek"),('fecha', '=', date.today()),('region', '=', 'SPS')])
        lenka_SPS = self.env['control.visitas'].search_count([('name', '=', "Visita Lenka"),('fecha', '=', date.today()),('region', '=', 'SPS')])
        clinica_SPS = self.env['control.visitas'].search_count([('name', '=', "Visita Clínica"),('fecha', '=', date.today()),('region', '=', 'SPS')])
        gerencia_SPS = self.env['control.visitas'].search_count([('name', '=', "Visita Gerencia"),('fecha', '=', date.today()),('region', '=', 'SPS')])
        soporte_SPS = self.env['control.visitas'].search_count([('name', '=', "Visita Soporte"),('fecha', '=', date.today()),('region', '=', 'SPS')])
        otros_SPS = self.env['control.visitas'].search_count([('name', '=', "Visita Otros"),('fecha', '=', date.today()),('region', '=', 'SPS')])
        total_SPS = self.env['control.visitas'].search_count([('fecha', '=', date.today()),('region', '=', 'SPS')])
        
        if not registros:
             raise UserError("No hay registros de visitas en esa fecha 1")
        
        html += """ 
            <style>
                    .cuadro {
                    border-color: #000;
                    border-width: 1px;
                    border-style: solid;
                    }

                    .tamaño_del_cuadro {
                    width: 900px;
                    height: 300px;
                    margin: 0px;
                    padding: 0px;
                    }

                    .texto_centro {
                    text-align: center;
                    }

                    .tabla_centrada{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    }

                    .th_total{
                        width: 25%;
                    }

                    table {
                    width: 100%;
                    border: 1px solid #000;
                    background-color: black;
                    }

                    th,
                    td {
                    width: 5%;
                    text-align: left;
                    vertical-align: top;
                    border: 1px solid #000;
                    border-collapse: collapse;
                    padding: 0.1em;
                    background-color: white;
                    }

                    caption {
                    padding: 0.3em;
                    }
                </style>
                """
        
        conteo = {
            'admin_TGU': admin_TGU,
            'megatk_TGU': megatk_TGU,
            'meditek_TGU': meditek_TGU,
            'lenka_TGU': lenka_TGU,
            'clinica_TGU': clinica_TGU,
            'gerencia_TGU': gerencia_TGU,
            'soporte_TGU': soporte_TGU,
            'otros_TGU': otros_TGU,
            'total_TGU': total_TGU,
            'admin_SPS': admin_SPS,
            'megatk_SPS': megatk_SPS,
            'meditek_SPS': meditek_SPS,
            'lenka_SPS': lenka_SPS,
            'clinica_SPS': clinica_SPS,
            'gerencia_SPS': gerencia_SPS,
            'soporte_SPS': soporte_SPS,
            'otros_SPS': otros_SPS,
            'total_SPS': total_SPS
        }
                
        html += f"""
                <h2 class="texto_centro">Conteo de visitas por sucursal</h2>
                <div class="tabla_centrada">
                    <table>
                        <thead>
                            <th>Sucursal</th>
                            <th>Tegucigalpa</th>
                            <th>San Pedro Sula</th>
                        </thead>
                        <tbody>
                            <tr>
                                <th>
                                    Administración
                                </th>
                                <th>
                                    {conteo['admin_TGU']}
                                </th>
                                <th>
                                    {conteo['admin_SPS']}
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    Tienda MegaTK
                                </th>
                                <th>
                                    {conteo['megatk_TGU']}
                                </th>
                                <th>
                                    {conteo['megatk_SPS']}
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    Tienda Meditek
                                </th>
                                <th>
                                    {conteo['meditek_TGU']}
                                </th>
                                <th>
                                    {conteo['meditek_SPS']}
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    Lenka
                                </th>
                                <th>
                                    {conteo['lenka_TGU']}
                                </th>
                                <th>
                                    {conteo['lenka_SPS']}
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    Clínica
                                </th>
                                <th>
                                    {conteo['clinica_TGU']}
                                </th>
                                <th>
                                    {conteo['clinica_SPS']}
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    Gerencia
                                </th>
                                <th>
                                    {conteo['gerencia_TGU']}
                                </th>
                                <th>
                                    {conteo['gerencia_SPS']}
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    Soporte
                                </th>
                                <th>
                                    {conteo['soporte_TGU']}
                                </th>
                                <th>
                                    {conteo['soporte_SPS']}
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    Otros
                                </th>
                                <th>
                                    {conteo['otros_TGU']}
                                </th>
                                <th>
                                    {conteo['otros_SPS']}
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    TOTAL
                                </th>
                                <th>
                                    {conteo['total_TGU']}
                                </th>
                                <th>
                                    {conteo['total_SPS']}
                                </th>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <br/>
                <br/>
                <br/>
                <h2 class="texto_centro">Registro de Visitas</h2>
                <div>
                <p class="texto_centro">
                    Reporte de los registros de las visitas del dia.
                </p>
                </div>
                <div class="tabla_centrada">
                    <table>
                        <thead>
                            <th>Nombre</th>
                            <th>Fecha</th>
                            <th>Hora</th>
                            <th>Region</th>
                            <th>Usuario</th>
                        </thead>
                        <tbody>
                        """
         
        visitas = []
        conteo = {}
        for visita in registros:
            visitas.append({
                'nombre': visita.name,
                'fecha': visita.fecha,
                'hora': visita.hora,
                'region': visita.region,
                'usuario': visita.user_id.name
            })
            
        contexto = {}
        for visita in visitas:
            html += "<tr>"
            html += f"""
                <th>{visita['nombre']}</th>
                <th>{visita['fecha']}</th>
                <th>{visita['hora']}</th>
                <th>{visita['region']}</th>
                <th>{visita['usuario']}</th>
            """
            html += "</tr>"
            
        html += f"""
                        </tbody>
                    </table>
                </div>
                <br/>
                <br/>
                <br/>
                <br/>
                <div class="footer">
                    <span>**** Mensaje automático de Odoo, no responder. ****</span>
                </div>
            """
            
        correo = "dvasquez@megatk.com,jmoran@meditekhn.com,lmoran@megatk.com,nfuentes@meditekhn.com,yalvarado@megatk.com,dcolindres@megatk.com"
        cc = "soporte@megatk.com"
        # correo = "alexdreyesmt@gmail.com"
        # cc = ""
        
        contexto['body'] = html
        
        _logger.warning(f"body: {contexto['body']}")
        
        self.send_email(correo, cc, html)
        