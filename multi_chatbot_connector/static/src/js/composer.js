/** @odoo-module **/

import { Component, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ChatbotComposerExtension extends Component {
	static template = "multi_chatbot_connector.ComposerTemplate";

	setup() {
		this.inputRef = useRef("input");
		this.attachmentRef = useRef("attachments");

		onMounted(() => {
			this._setupComposer();
		});
	}

	_setupComposer() {
		const input = this.inputRef.el;
		if (input) {
			// Auto-resize del textarea
			input.addEventListener("input", () => {
				input.style.height = "auto";
				input.style.height = input.scrollHeight + "px";
			});

			// Evento de enfoque
			input.addEventListener("focus", () => {
				this.trigger("input_focused");
			});
		}
	}

	onAttachmentClick() {
		const attachmentList = this.attachmentRef.el;
		if (attachmentList) {
			attachmentList.click();
		}
	}

	trigger(event) {
		// Emitir evento personalizado
		const customEvent = new CustomEvent(event, { bubbles: true });
		this.el.dispatchEvent(customEvent);
	}
}

registry.category("components").add("ChatbotComposer", ChatbotComposerExtension);
