/** @odoo-module **/

import { onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";

export class LenkaOperationFormController extends FormController {
    setup() {
        super.setup();
        this.guidanceFrame = null;
        this.clearGuidance = () => {};
        onWillUnmount(() => {
            cancelAnimationFrame(this.guidanceFrame);
            this.clearGuidance();
        });
    }

    async beforeExecuteActionButton(params) {
        const record = this.model.root;
        if (params.name === "action_mark_contracted" &&
            record.data.state === "approved" && record.resId) {
            const signedContracts = await this.orm.searchCount("lenka.generated.document", [
                ["operation_id", "=", record.resId],
                ["document_type", "=", "contract"],
                ["state", "=", "signed"],
                ["attachment_id", "!=", false],
            ]);
            if (!signedContracts) {
                const guide = () => this.showContractGuidance(
                    "contract_documents", "generated_document_ids",
                    "Pendiente: abrí el contrato, descargá el PDF, gestioná la firma, subí la copia firmada y pulsá Marcar firmado."
                );
                this.dialogService.add(AlertDialog, {
                    title: "Falta el contrato firmado y adjunto",
                    body: "En Contratos y documentos, abrí el documento de tipo Contrato. Si no existe, usá Generar documentos. En el documento, usá Descargar contrato PDF, gestioná la firma, subí la copia firmada y pulsá Marcar firmado. Después volvé a esta operación y pulsá Marcar contratado.",
                    confirmLabel: "Cerrar e ir a los documentos",
                    confirm: guide,
                    dismiss: guide,
                });
                return false;
            }
        }
        return super.beforeExecuteActionButton(params);
    }

    showContractGuidance(page = "approval_contract", fieldName = "contract_signed",
        message = "Pendiente: confirmar que el contrato está firmado.") {
        this.clearGuidance();
        const root = this.rootRef.el;
        if (!root) {
            return;
        }
        root.querySelector(`[role="tab"][name="${page}"]`)?.click();
        // Allow the notebook and closing dialog to render before moving focus.
        cancelAnimationFrame(this.guidanceFrame);
        this.guidanceFrame = requestAnimationFrame(() => {
            this.guidanceFrame = requestAnimationFrame(() => {
                const field = root.querySelector(`.o_field_widget[name="${fieldName}"]`);
                const input = fieldName === "contract_signed"
                    ? field?.querySelector('input[type="checkbox"]') : field;
                if (!field || !input) {
                    return;
                }
                field.classList.add("o_lenka_needs_attention");
                input.setAttribute("aria-invalid", "true");
                const hint = document.createElement("span");
                hint.className = "o_lenka_validation_hint";
                hint.textContent = message;
                hint.setAttribute("role", "alert");
                field.appendChild(hint);
                const originalTabindex = input.getAttribute("tabindex");
                if (fieldName !== "contract_signed") {
                    input.setAttribute("tabindex", "-1");
                }
                this.clearGuidance = () => {
                    field.classList.remove("o_lenka_needs_attention");
                    input.removeAttribute("aria-invalid");
                    hint.remove();
                    input.removeEventListener("change", clearWhenCorrected);
                    if (originalTabindex === null) {
                        input.removeAttribute("tabindex");
                    } else {
                        input.setAttribute("tabindex", originalTabindex);
                    }
                };
                const clearWhenCorrected = () => {
                    if (input.checked) {
                        this.clearGuidance();
                    }
                };
                input.addEventListener("change", clearWhenCorrected);
                field.scrollIntoView({ block: "center", behavior: "smooth" });
                input.focus({ preventScroll: true });
            });
        });
    }
}

registry.category("views").add("lenka_operation_form", {
    ...formView,
    Controller: LenkaOperationFormController,
});


export class LenkaDocumentFormController extends LenkaOperationFormController {
    async beforeExecuteActionButton(params) {
        const record = this.model.root;
        if (params.name === "action_mark_signed" && record.data.state === "generated" &&
            record.data.document_type === "contract" &&
            !record.data.signed_file && !record.data.attachment_id) {
            const guide = () => this.showContractGuidance(
                "", "signed_file", "Subí aquí la copia del contrato que ya fue firmada."
            );
            this.dialogService.add(AlertDialog, {
                title: "Falta adjuntar el contrato firmado",
                body: "Primero descargá el contrato PDF y gestioná la firma. Después subí la copia firmada en Subir contrato firmado y pulsá Marcar firmado.",
                confirmLabel: "Ir a subir el archivo",
                confirm: guide,
                dismiss: guide,
            });
            return false;
        }
        return super.beforeExecuteActionButton(params);
    }
}

registry.category("views").add("lenka_document_form", {
    ...formView,
    Controller: LenkaDocumentFormController,
});
