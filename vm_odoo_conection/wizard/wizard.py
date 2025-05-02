from odoo import models, fields

class vm_actualizacion(models.TransientModel):
    _name = 'wizard.vm_actualizacion'
    
    recargar_credito = fields.Float()

    def credito_a_recargar(self):
        # Obtener todos los empleados
        empleados = self.env['hr.employee'].search([])
        
        # Actualizar el campo 'credito' de cada empleado
        for empleado in empleados:
            empleado.write({'credito': self.recargar_credito})
        
        # Cerrar el wizard después de la actualización
        return {'type': 'ir.actions.act_window_close'}



    
