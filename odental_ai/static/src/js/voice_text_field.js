/** @odoo-module **/

import { Component, onWillUnmount, onWillUpdateProps, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";


export class ODentalVoiceTextField extends Component {
    static template = "odental_ai.VoiceTextField";
    static props = {
        ...standardFieldProps,
        placeholder: { type: String, optional: true },
    };

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            listening: false,
            supported: Boolean(window.SpeechRecognition || window.webkitSpeechRecognition),
            value: this.props.record.data[this.props.name] || "",
        });
        this.recognition = null;
        this.baseValue = this.state.value;
        onWillUpdateProps((nextProps) => {
            if (!this.state.listening) {
                this.state.value = nextProps.record.data[nextProps.name] || "";
            }
        });
        onWillUnmount(() => {
            if (this.recognition) {
                this.recognition.abort();
                this.recognition = null;
            }
        });
    }

    async commit(value, fromVoice = false) {
        this.state.value = value;
        const changes = { [this.props.name]: value };
        if ("input_source" in this.props.record.data && fromVoice) {
            changes.input_source = "voice";
        }
        await this.props.record.update(changes);
    }

    onInput(event) {
        this.commit(event.target.value);
    }

    startListening() {
        if (this.props.readonly || !this.state.supported || this.state.listening) {
            return;
        }
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new Recognition();
        this.recognition.lang = this.props.record.data.language_code || "es-HN";
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.baseValue = (this.state.value || "").trim();
        if (this.baseValue) {
            this.baseValue += "\n";
        }
        this.recognition.onresult = (event) => {
            let finalText = "";
            let interimText = "";
            for (let index = event.resultIndex; index < event.results.length; index++) {
                const transcript = event.results[index][0].transcript;
                if (event.results[index].isFinal) {
                    finalText += transcript.trim() + " ";
                } else {
                    interimText += transcript;
                }
            }
            if (finalText) {
                this.baseValue += finalText.trim() + "\n";
                this.commit(this.baseValue.trimEnd(), true);
            } else {
                this.state.value = this.baseValue + interimText;
            }
        };
        this.recognition.onerror = (event) => {
            this.state.listening = false;
            this.notification.add(
                `No fue posible continuar el dictado (${event.error}). Puede escribir la instrucción.`,
                { type: "warning" }
            );
        };
        this.recognition.onend = () => {
            this.state.listening = false;
            this.recognition = null;
        };
        try {
            this.recognition.start();
            this.state.listening = true;
        } catch {
            this.state.listening = false;
            this.notification.add("El micrófono no está disponible en este navegador.", {
                type: "warning",
            });
        }
    }

    stopListening() {
        if (this.recognition) {
            this.recognition.stop();
        }
        this.state.listening = false;
        if (this.state.value !== (this.props.record.data[this.props.name] || "")) {
            this.commit(this.state.value, true);
        }
    }
}

registry.category("fields").add("odental_voice_text", {
    component: ODentalVoiceTextField,
    supportedTypes: ["text"],
    extractProps: ({ attrs }) => ({ placeholder: attrs.placeholder }),
});
