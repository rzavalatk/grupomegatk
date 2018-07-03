# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Product(models.Model):
    _inherit = "product.template"

    x_marcatk = fields.Selection([('3M','3M'),('3NSTAR','3NSTAR'),('Accesorios_Identificación','ACCESORIOS IDENTIFICACIÓN'),('ANVIZ','ANVIZ'),('BORDEAUX','BORDEAUX'),('BRITOMATICS','BRITOMATICS'),('BROTHER','BROTHER'),('CELUPAL','CELUPAL'),('CITIZEN','CITIZEN'),('DATACARD','DATACARD'),('DATAMAX','DATAMAX'),('DIGITAL_PERSONA','DIGITAL PERSONA'),('Digital_Solution','DIGITAL SOLUTION')
    	,('ELO_TOUCH_SYSTEM','ELO TOUCH SYSTEM'),('EPSON','EPSON'),('EPSON_POS','EPSON POS'),('EVOLIS','EVOLIS'),('EXTECH','EXTECH'),('FARGO','FARGO'),('GOLDENSIGN','GOLDENSIGN'),('HEATPRESS','HEATPRESS')    	,('HID_FARGO','HID FARGO'),('HONGDA','HONGDA'),('KONICA_MINOLTA','KONICA MINOLTA'),('MAGICARD','MAGICARD'),('mckako','MCKAKO'),('MICROTEC','MICROTEC'),('MIMAKI','MIMAKI')
    	,('MUTOH','MUTOH'),('PBS','PBS'),('PLASCO','PLASCO')    	,('PVC','PVC'),('SCANGLE','SCANGLE'),('SIODROID','SIODROID'),('SOYANG','SOYANG'),('STAR_MICRONICS','STAR MICRONICS'),('STS_INK','STS INK'),('TECRE','TECRE'),('UNITECH','UNITECH'),('WASATCH','WASATCH'),('ZEBRA','ZEBRA'),('HID_GLOBAL','HID GLOBAL'),('MATICA','MATICA'),('DATALOGIC','DATALOGIC')], string = 'Marca')
    x_marcame = fields.Selection([('airtechnique','AIR TECHNIQUE'),('bioart','BIOART'),('blossom','BLOSSOM'),('buffalo','BUFFALO'),('dentalusa','DENTAL USA'),('dentsply','DENTSPLY'),('dharma','DHARMA'),('diadent','DIADENT'),('diaswiss','DIASWISS'),('eufar','EUFAR'),('fkg','FKG'),('flowx-ray','FLOW X-RAY'),('fona','FONA'),('formulaeacao','FORMULA E ACAO'),('futurais','FUTURA IS')
    	,('helse','HELSE'),('lares','LARES'),('ritedent','RITEDENT'),('lumadent','LUMADENT'),('bioart','BIOART'),('mdcdental','MDC DENTAL'),('mdk','MDK'),('smiledt','SMILE DT'),('medeco','MEDECO'),('mediceptuk','MEDICEPT UK'),('medimax','MEDIMAX'),('medico','MEDICO'),('metabiomed','METABIOMED'),('midmark','MIDMARK'),('mti','MTI'),('nsk','NSK'),('pacdent','PACDENT')
    	,('pulpdent','PULPDENT'),('scipharm','SCI PHARM'),('tehnodent','TEHNODENT'),('vistadental','VISTA DENTAL'),('ritdent','RITDENT'),('dfs','DFS'),('biolectronics','BIOELECTRONICS'),('etal','ETAL'),('tribest','TRIBEST'),('mc_dental','MC DENTAL'),('importadoragil','IMPORTADORA Y EXPORTADORA GIL'),('dromeinter','DROMEINTER'),('vdw','VDW'),('henryshe','HENRY SCHEIN')
    	,('odontotech','ODONTOTECH')],string = 'Marca')
    x_tipo = fields.Selection([('producto','Producto'),('suministro','Suministro')],string = 'Tipo')
    x_ingresotk = fields.Selection([('energia','Ingreso Energía'),('grafica','Ingreso Linea Gráfica'),('identificacion','Ingreso Linea Identificación')
    	,('movil','Ingreso Linea Móvil'),('pos','Ingreso Linea POS'),('seguridad','Ingreso Linea Seguridad'),('soporte','Ingreso Soporte'),('varios','Ingreso Varios')],string = 'Ingreso/Linea')
    x_ingresome = fields.Selection([('odontologia','Ingreso Odontología'),('manejoenvio','Ingreso Manejo y Envió'),('varios','Ingreso Varios')],string='Ingreso/Linea')
