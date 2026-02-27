/** @odoo-module **/
import { registry } from '@web/core/registry';
//const  { Component, useState } = owl
import { Component, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

/**
 * Componente de menú de recordatorios en el systray.
 * 
 * Muestra un icono de campana en la barra superior que permite:
 * - Ver la lista de recordatorios activos
 * - Seleccionar un recordatorio específico
 * - Ver los registros relacionados con el recordatorio seleccionado
 */
class ReminderMenu extends Component {
    /**
     * Función de configuración que se ejecuta después de construir el componente.
     * Inicializa los servicios y el estado del componente.
     */
    setup(){
        this.action = useService("action");  // Servicio para ejecutar acciones
        this.select = useRef('reminder_menu');  // Referencia al elemento select
        this.reminder = [];  // Array para almacenar datos del recordatorio activo
        this.rpc = this.env.services.rpc  // Servicio RPC para llamadas al backend
        
        // Estado reactivo del componente
        this.state = useState({
            all_remainders:[],  // Lista de todos los recordatorios activos
        })
    }
    
    /**
     * Muestra los recordatorios disponibles al hacer clic en el icono.
     * Carga la lista completa de recordatorios activos desde el servidor.
     * 
     * @param {Event} ev - Evento de clic
     */
    async showReminder(ev){
        ev.stopPropagation();  // Evita la propagación del evento
        ev.preventDefault();   // Previene el comportamiento por defecto
        
        // Llama al backend para obtener todos los recordatorios activos
        const data= await rpc("/hr_reminder/all_reminder")
        this.state.all_remainders = data  // Actualiza el estado con los recordatorios
    }
    
    /**
     * Activa un recordatorio específico y muestra sus registros.
     * Obtiene los detalles del recordatorio seleccionado y abre una vista
     * filtrada con los registros correspondientes.
     * 
     * @param {Event} ev - Evento de clic en el botón "Ver"
     */
    async reminderActive(ev){
        ev.stopPropagation();  // Evita la propagación del evento
        ev.preventDefault();   // Previene el comportamiento por defecto
        
        var self = this;
        // Obtiene el valor seleccionado del dropdown
        console.log((this.select.el.querySelector("#reminder_select")).value)
        var value = (this.select.el.querySelector("#reminder_select")).value;
        
        // Obtiene los detalles del recordatorio seleccionado
        await rpc('/hr_reminder/reminder_active', {'reminder_name':value}).then(function(current){
            self.reminder = current  // Guarda los datos del recordatorio
            
            for (var i=0; i<1; i++){  // Loop para procesar el recordatorio
                // Configuración base de la acción de ventana
                const Action = {
                            type: 'ir.actions.act_window',
                            res_model: self.reminder[i],  // Modelo a mostrar
                            view_mode: 'list',
                            views: [[false, 'list']],
                            target: 'new',  // Abre en ventana nueva
                            context: { create: false}  // Desactiva creación de registros
                        };
                
                // Caso 1: Recordatorio de "Hoy" - muestra registros del día actual
                if (self.reminder[i+2] === 'today') {
                    const domain = [
                                [self.reminder[i+1], '>=', `${self.reminder[i+7]} 00:00:00`],
                                [self.reminder[i+1], '<=', `${self.reminder[i+7]} 23:59:59`]
                            ];
                    return self.action.doAction({ ...Action, domain });
                }
                // Caso 2: Recordatorio por "Fecha Establecida" - muestra registros en el rango
                else if (self.reminder[i+2] == 'set_date'){
                    const domain = [
                            [self.reminder[i+1], '>=', `${self.reminder[i+10]} 00:00:00`],
                            [self.reminder[i+1], '<=', `${self.reminder[i+3]} 23:59:59`]
                        ];
                    return self.action.doAction({ ...Action, domain });
                }
                // Caso 3: Recordatorio por "Período" - muestra registros entre date_from y date_to
                else if (self.reminder[i+2] == 'set_period'){
                    const domain = [
                            [self.reminder[i+1], '>=', `${self.reminder[i+4]} 00:00:00`],
                            [self.reminder[i+1], '<=', `${self.reminder[i+5]} 23:59:59`]
                        ];
                    return self.action.doAction({ ...Action, domain });
                }
            }
        })
    }
}

// Asocia el template XML al componente
ReminderMenu.template = 'owl.reminder_menu'

// Configuración del systray
const Systray = {
    Component: ReminderMenu,
}

// Registra el componente en el systray de Odoo
registry.category("systray").add("reminder_menu", Systray)
