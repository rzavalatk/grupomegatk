/** @odoo-module **/

import { Component, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class LocalDictation extends Component {
    setup() {
        this.state = useState({ listening: false, message: "" });
        this.recognition = null;
        onWillUnmount(() => this.stop());
    }

    get value() { return this.props.record.data[this.props.name] || ""; }

    onInput(event) {
        this.props.record.update({ [this.props.name]: event.target.value });
    }

    stop() {
        if (this.recognition) {
            this.recognition.stop();
            this.recognition = null;
        }
        this.state.listening = false;
    }

    async toggle() {
        if (this.state.listening) {
            this.stop();
            return;
        }
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!Recognition || !("processLocally" in Recognition.prototype)
            || typeof Recognition.available !== "function") {
            this.state.message = "Este navegador no ofrece dictado local. Puede escribir el texto o usar el dictado del teclado.";
            return;
        }
        try {
            let language = null;
            for (const candidate of ["es-MX", "es-ES"]) {
                if (await Recognition.available({ langs: [candidate], processLocally: true }) === "available") {
                    language = candidate;
                    break;
                }
            }
            if (!language) {
                this.state.message = "No hay un paquete de español disponible en este dispositivo. No se activó reconocimiento remoto.";
                return;
            }
            const recognition = new Recognition();
            recognition.processLocally = true;
            recognition.lang = language;
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.onresult = (event) => {
                const words = [];
                for (let index = event.resultIndex; index < event.results.length; index++) {
                    if (event.results[index].isFinal) words.push(event.results[index][0].transcript.trim());
                }
                if (words.length) {
                    this.props.record.update({
                        [this.props.name]: [this.value, ...words].filter(Boolean).join(" "),
                    });
                }
            };
            recognition.onerror = (event) => {
                this.state.message = `El dictado se detuvo (${event.error}). Revise el texto antes de interpretarlo.`;
            };
            recognition.onend = () => {
                this.state.listening = false;
                this.recognition = null;
            };
            recognition.start();
            this.recognition = recognition;
            this.state.listening = true;
            this.state.message = "Escuchando en este dispositivo. Pulse Detener cuando termine.";
        } catch (error) {
            this.state.listening = false;
            this.state.message = "El navegador no pudo iniciar dictado local. Puede escribir el hallazgo.";
        }
    }
}

LocalDictation.template = "odental_diagnostics.LocalDictation";
LocalDictation.props = { ...standardFieldProps };
registry.category("fields").add("odental_local_dictation", {
    component: LocalDictation,
    supportedTypes: ["text"],
});
