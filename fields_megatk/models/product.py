# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Product(models.Model):
    _inherit = "product.template"

    # x_marcatk = fields.Selection([('3M','3M'),('3NSTAR','3NSTAR'),('Accesorios_Identificación','ACCESORIOS IDENTIFICACIÓN'),('ANVIZ','ANVIZ'),('BORDEAUX','BORDEAUX'),('BRITOMATICS','BRITOMATICS'),('BROTHER','BROTHER'),('CELUPAL','CELUPAL'),('CITIZEN','CITIZEN'),('DATACARD','DATACARD'),('DATAMAX','DATAMAX'),('DIGITAL_PERSONA','DIGITAL PERSONA'),('Digital_Solution','DIGITAL SOLUTION')
    # 	,('ELO_TOUCH_SYSTEM','ELO TOUCH SYSTEM'),('EPSON','EPSON'),('EPSON_POS','EPSON POS'),('EVOLIS','EVOLIS'),('EXTECH','EXTECH'),('FARGO','FARGO'),('GOLDENSIGN','GOLDENSIGN'),('HEATPRESS','HEATPRESS')    	,('HID_FARGO','HID FARGO'),('HONGDA','HONGDA'),('KONICA_MINOLTA','KONICA MINOLTA'),('MAGICARD','MAGICARD'),('mckako','MCKAKO'),('MICROTEC','MICROTEC'),('MIMAKI','MIMAKI')
    # 	,('MUTOH','MUTOH'),('PBS','PBS'),('PLASCO','PLASCO')    	,('PVC','PVC'),('SCANGLE','SCANGLE'),('SIODROID','SIODROID'),('SOYANG','SOYANG'),('STAR_MICRONICS','STAR MICRONICS'),('STS_INK','STS INK'),('TECRE','TECRE'),('UNITECH','UNITECH'),('WASATCH','WASATCH'),('ZEBRA','ZEBRA'),('HID_GLOBAL','HID GLOBAL'),('MATICA','MATICA'),('DATALOGIC','DATALOGIC')], string = 'Marca')
    # x_marcame = fields.Selection([('airtechnique','AIR TECHNIQUE'),('bioart','BIOART'),('blossom','BLOSSOM'),('buffalo','BUFFALO'),('dentalusa','DENTAL USA'),('dentsply','DENTSPLY'),('dharma','DHARMA'),('diadent','DIADENT'),('diaswiss','DIASWISS'),('eufar','EUFAR'),('fkg','FKG'),('flowx-ray','FLOW X-RAY'),('fona','FONA'),('formulaeacao','FORMULA E ACAO'),('futurais','FUTURA IS')
    # 	,('helse','HELSE'),('lares','LARES'),('ritedent','RITEDENT'),('lumadent','LUMADENT'),('bioart','BIOART'),('mdcdental','MDC DENTAL'),('mdk','MDK'),('smiledt','SMILE DT'),('medeco','MEDECO'),('mediceptuk','MEDICEPT UK'),('medimax','MEDIMAX'),('medico','MEDICO'),('metabiomed','METABIOMED'),('midmark','MIDMARK'),('mti','MTI'),('nsk','NSK'),('pacdent','PACDENT')
    # 	,('pulpdent','PULPDENT'),('scipharm','SCI PHARM'),('tehnodent','TEHNODENT'),('vistadental','VISTA DENTAL'),('ritdent','RITDENT'),('dfs','DFS'),('biolectronics','BIOELECTRONICS'),('etal','ETAL'),('tribest','TRIBEST'),('mc_dental','MC DENTAL'),('importadoragil','IMPORTADORA Y EXPORTADORA GIL'),('dromeinter','DROMEINTER'),('vdw','VDW'),('henryshe','HENRY SCHEIN')
    # 	,('odontotech','ODONTOTECH')],string = 'Marca')
    x_tipo = fields.Selection([('producto','Producto'),('suministro','Suministro')],string = 'Tipo')
    x_ingresotk = fields.Selection([('energia','Ingreso Energía'),('grafica','Ingreso Linea Gráfica'),('identificacion','Ingreso Linea Identificación')
    	,('movil','Ingreso Linea Móvil'),('pos','Ingreso Linea POS'),('seguridad','Ingreso Linea Seguridad'),('soporte','Ingreso Soporte'),('varios','Ingreso Varios')],string = 'Ingreso/Linea')
    x_ingresome = fields.Selection([('odontologia','Ingreso Odontología'),('manejoenvio','Ingreso Manejo y Envió'),('varios','Ingreso Varios')],string='Ingreso/Linea')
    x_arancel = fields.Char(string='Arancel',store=True)
    x_costo_real = fields.Float(string='Costo Honduras',store=True)
    x_ponderacion = fields.Char(string='Ponderación',store=True)
    x_comisiones = fields.One2many('lista.precios.megatk.line', 'product_id', domain=[('obj_padre.state','=','valida')])
    marca_id = fields.Many2one('product.marca', string='Marca',)
    x_comisiones_a=fields.Integer(string='Comision A',store=True)
    x_comisiones_m=fields.Integer(string='Comision M',store=True)

    @api.onchange('list_price')
    def _onchange_precio_lista(self):
        for list_precio in self.x_comisiones:
            list_precio.write({'precio_publico': self.list_price, 'precio_descuento': self.list_price + ((self.list_price*list_precio.x_descuento)/100)})

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange('lst_price')
    def _onchange_precio_lista(self):
        for list_precio in self.product_tmpl_id.x_comisiones:
            list_precio.write({'precio_publico': self.lst_price, 'precio_descuento': self.lst_price + ((self.lst_price*list_precio.x_descuento)/100)})


class ProductMarca(models.Model):
    _name = 'product.marca'
    _order = 'name asc'

    name = fields.Char("Nombre")
    company_id = fields.Many2one("res.company", "Empresa", default=lambda self: self.env.user.company_id, required=True)
    active = fields.Boolean(string='Activo', default=True)