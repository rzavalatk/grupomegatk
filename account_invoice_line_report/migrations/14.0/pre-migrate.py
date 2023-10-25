from odoo import api, SUPERUSER_ID

def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    @api.model
    def custom_query(self):
        # Ejecuta la consulta utilizando el ORM de Odoo
        self.env.cr.execute("update ir_ui_view set active ='f' where id in (3601, 3935, 3583, 3584, 4206, 4205);")
        result = self.env.cr.fetchall()
        return result
    
    # Lista de nombres de módulos a desactivarj
    #modulos_a_desactivar = ['auditlog']

    # Desactiva los módulos
    #module_obj = env['ir.module.module']
    #modules_to_deactivate = module_obj.search([('name', 'in', modulos_a_desactivar)])
    #modules_to_deactivate.write({'state': 'uninstalled'})
    
    # Omitir la migración de una plantilla específica
    #template_obj = env['template']  # Reemplaza 'nombre_modelo_de_plantilla' con el nombre del modelo de tu plantilla
    #template_to_skip = template_obj.search([('name', '=', '3601')])
    #if template_to_skip:
    #    template_to_skip.write({'active': False})
    
    #------------------------------------------------------------------
    # Omitir la migración de dos plantillas específicas por sus ID
    #template_ids_to_skip = []  # Reemplaza con los IDs de las vistas que deseas omitir

    # Buscar el modelo de plantilla basado en los IDs de las vistas y desactivarlas
    #template_obj = env['ir.ui.view']
    #templates_to_skip = template_obj.browse(template_ids_to_skip)

    #for template in templates_to_skip:
    #    template.write({'active': False})
