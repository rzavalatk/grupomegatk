# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#CAMPOS EN INVENTARIO/PŔODUCTO/INFORMACION GENERAL
class Product(models.Model):
    _inherit = "product.template"

    # x_marcatk = fields.Selection([('3M','3M'),('3NSTAR','3NSTAR'),('Accesorios_Identificación','ACCESORIOS IDENTIFICACIÓN'),('ANVIZ','ANVIZ'),('BORDEAUX','BORDEAUX'),('BRITOMATICS','BRITOMATICS'),('BROTHER','BROTHER'),('CELUPAL','CELUPAL'),('CITIZEN','CITIZEN'),('DATACARD','DATACARD'),('DATAMAX','DATAMAX'),('DIGITAL_PERSONA','DIGITAL PERSONA'),('Digital_Solution','DIGITAL SOLUTION')
    # 	,('ELO_TOUCH_SYSTEM','ELO TOUCH SYSTEM'),('EPSON','EPSON'),('EPSON_POS','EPSON POS'),('EVOLIS','EVOLIS'),('EXTECH','EXTECH'),('FARGO','FARGO'),('GOLDENSIGN','GOLDENSIGN'),('HEATPRESS','HEATPRESS')    	,('HID_FARGO','HID FARGO'),('HONGDA','HONGDA'),('KONICA_MINOLTA','KONICA MINOLTA'),('MAGICARD','MAGICARD'),('mckako','MCKAKO'),('MICROTEC','MICROTEC'),('MIMAKI','MIMAKI')
    # 	,('MUTOH','MUTOH'),('PBS','PBS'),('PLASCO','PLASCO')    	,('PVC','PVC'),('SCANGLE','SCANGLE'),('SIODROID','SIODROID'),('SOYANG','SOYANG'),('STAR_MICRONICS','STAR MICRONICS'),('STS_INK','STS INK'),('TECRE','TECRE'),('UNITECH','UNITECH'),('WASATCH','WASATCH'),('ZEBRA','ZEBRA'),('HID_GLOBAL','HID GLOBAL'),('MATICA','MATICA'),('DATALOGIC','DATALOGIC')], string = 'Marca')
    # x_marcame = fields.Selection([('airtechnique','AIR TECHNIQUE'),('bioart','BIOART'),('blossom','BLOSSOM'),('buffalo','BUFFALO'),('dentalusa','DENTAL USA'),('dentsply','DENTSPLY'),('dharma','DHARMA'),('diadent','DIADENT'),('diaswiss','DIASWISS'),('eufar','EUFAR'),('fkg','FKG'),('flowx-ray','FLOW X-RAY'),('fona','FONA'),('formulaeacao','FORMULA E ACAO'),('futurais','FUTURA IS')
    # 	,('helse','HELSE'),('lares','LARES'),('ritedent','RITEDENT'),('lumadent','LUMADENT'),('bioart','BIOART'),('mdcdental','MDC DENTAL'),('mdk','MDK'),('smiledt','SMILE DT'),('medeco','MEDECO'),('mediceptuk','MEDICEPT UK'),('medimax','MEDIMAX'),('medico','MEDICO'),('metabiomed','METABIOMED'),('midmark','MIDMARK'),('mti','MTI'),('nsk','NSK'),('pacdent','PACDENT')
    # 	,('pulpdent','PULPDENT'),('scipharm','SCI PHARM'),('tehnodent','TEHNODENT'),('vistadental','VISTA DENTAL'),('ritdent','RITDENT'),('dfs','DFS'),('biolectronics','BIOELECTRONICS'),('etal','ETAL'),('tribest','TRIBEST'),('mc_dental','MC DENTAL'),('importadoragil','IMPORTADORA Y EXPORTADORA GIL'),('dromeinter','DROMEINTER'),('vdw','VDW'),('henryshe','HENRY SCHEIN')
    # 	,('odontotech','ODONTOTECH')],string = 'Marca')

    
    @api.depends('list_price', 'currency_id', 'company_id', 'x_costo_real', 'standard_price')
    def _compute_amount_vt(self):
        for product in self:
            if product.standard_price != 0:
                if product.x_costo_real == 0:
                    product.x_ganancia = ((product.list_price - product.standard_price) * 100) / product.standard_price
                else:
                    product.x_ganancia = ((product.list_price - product.x_costo_real) * 100) / product.x_costo_real

    x_tipo = fields.Selection([('producto','Producto'),('suministro','Suministro')],string = 'Tipo')
    x_ingresotk = fields.Selection([('energia','Ingreso Energía'),('grafica','Ingreso Linea Gráfica'),('identificacion','Ingreso Linea Identificación')
    	,('movil','Ingreso Linea Móvil'),('pos','Ingreso Linea POS'),('seguridad','Ingreso Linea Seguridad'),('soporte','Ingreso Soporte'),('varios','Ingreso Varios')],string = 'Ingreso/Linea')
    x_ingresome = fields.Selection([('odontologia','Ingreso Odontología'),('manejoenvio','Ingreso Manejo y Envió'),('varios','Ingreso Varios')],string='Ingreso/Linea')
    x_arancel = fields.Char(string='Arancel',store=True)
    x_costo_real = fields.Float(string='Costo Nacionalizado',store=True)
    x_ponderacion = fields.Float(string='Ponderación',store=True)
    marca_id = fields.Many2one('product.marca', string='Marca',)
    x_comisiones_a=fields.Integer(string='Comision A',store=True)
    x_comisiones_m=fields.Integer(string='Comision M',store=True)
    x_ingresonic = fields.Selection([('energia','Ingreso Energía'),('grafica','Ingreso Linea Gráfica'),('identificacion','Ingreso Linea Identificación')
        ,('movil','Ingreso Linea Móvil'),('pos','Ingreso Linea POS'),('seguridad','Ingreso Linea Seguridad'),('soporte','Ingreso Soporte')
        ,('odontologia','Ingreso Odontología'),('manejoenvio','Ingreso Manejo y Envió'),('varios','Ingreso Varios')],string='Ingreso/Linea')
    x_ganancia = fields.Float(string='Ganancia', compute='_compute_amount_vt', store=True)

#Formulario al crear una marca
class ProductMarca(models.Model):
    _name = 'product.marca'
    _order = 'name asc'

    name = fields.Char("Nombre")
    company_id = fields.Many2one("res.company", "Empresa", default=lambda self: self.env.user.company_id, required=True)
    active = fields.Boolean(string='Activo', default=True)
