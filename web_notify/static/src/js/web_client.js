/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Servicio mejorado para notificaciones web en tiempo real
 * Escucha los canales de notificación del bus y muestra mensajes al usuario
 */
export const webNotificationService = {
    dependencies: ["bus_service", "notification"],

    start(env, { bus_service, notification: notificationService }) {
        const uid = env.uid || 1;
        
        const NotificationChannels = {
            success: `notify_success_${uid}`,
            danger: `notify_danger_${uid}`,
            warning: `notify_warning_${uid}`,
            info: `notify_info_${uid}`,
            default: `notify_default_${uid}`,
        };

        // Iniciar polling del bus
        bus_service.start();

        // Agregar canales de notificación
        Object.values(NotificationChannels).forEach((channel) => {
            bus_service.subscribe(channel, (message) => {
                notificationService.add(message.message, {
                    type: message.type || "info",
                    title: message.title,
                    sticky: message.sticky || false,
                    className: message.className,
                });
            });
        });

        return {};
    },
};

registry.category("services").add("webNotificationLegacy", webNotificationService);
