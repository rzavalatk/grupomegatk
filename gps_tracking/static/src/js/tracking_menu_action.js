/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AbstractAction } from "@web/webclient/actions/abstract_action";
import { useService } from "@web/core/utils/hooks";

export class TrackingCardMenu extends AbstractAction {
    static template = "TrackingCardMenu";

    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.current_trip = null;

        this.loadTrip();

        this.onClickIniciarViaje = this.onClickIniciarViaje.bind(this);
        this.onClickFinalizarViaje = this.onClickFinalizarViaje.bind(this);
    }

    async loadTrip() {
        const result = await this.rpc({
            model: "gps.device.trip",
            method: "search_read",
            domain: [["state", "=", "ongoing"]],
            fields: ["check_in", "device_id"],
            limit: 1,
        });
        this.current_trip = result.length ? result[0] : null;
        this.render();
    }

    onClickIniciarViaje(ev) {
        ev.preventDefault();
        this.startTrip();
    }

    onClickFinalizarViaje(ev) {
        ev.preventDefault();
        this.finishTrip();
    }

    async startTrip() {
        const input = this.el.querySelector("#id_device");
        const msg = this.el.querySelector("#msg-text");
        const deviceId = input?.value;

        if (!deviceId) {
            msg.textContent = "Ingrese el ID del dispositivo";
            return;
        }

        if (!/^\d{6}$/.test(deviceId)) {
            msg.textContent = "El ID del dispositivo no es válido";
            return;
        }

        msg.textContent = "";

        try {
            const result = await this.rpc({
                model: "gps.device.trip",
                method: "start_trip",
                args: [deviceId],
            });
            console.log("Inicio de viaje:", result);
            this.loadTrip();
        } catch (error) {
            console.error(error);
            msg.textContent = "Error al iniciar el viaje";
        }
    }

    async finishTrip() {
        const msg = this.el.querySelector("#msg-text");
        try {
            const result = await this.rpc({
                model: "gps.device.trip",
                method: "finish_trip",
                args: [this.current_trip.device_id],
            });
            console.log("Final del viaje:", result);
            this.loadTrip();
        } catch (error) {
            console.error(error);
            msg.textContent = "Error al finalizar el viaje";
        }
    }

    mounted() {
        // Se asegura que los botones estén enlazados después del render
        this.el.querySelector(".btn-success")?.addEventListener("click", this.onClickIniciarViaje);
        this.el.querySelector(".btn-warning")?.addEventListener("click", this.onClickFinalizarViaje);
    }

    willUnmount() {
        console.log("willUnmount: limpiando listeners del widget");
        this.el.querySelector(".btn-success")?.removeEventListener("click", this.onClickIniciarViaje);
        this.el.querySelector(".btn-warning")?.removeEventListener("click", this.onClickFinalizarViaje);
    }

    async willUnmountAndDestroy() {
        console.log("willUnmountAndDestroy: widget destruido");
    }
}

// Registrar la acción personalizada en el registry
registry.category("actions").add("gps_tracking_tag", TrackingCardMenu);
