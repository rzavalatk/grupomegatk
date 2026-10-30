/** @odoo-module **/

import { onWillUnmount, useEffect, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { financialValidationErrors } from "./financial_validation";

export class LenkaOperationFormController extends FormController {
    setup() {
        super.setup();
        this.guidanceFrame = null;
        this.clearGuidance = () => {};
        this.financialValidation = useState({ enabled: false });
        this.clearFinancialGuidance = () => {};
        useEffect(() => {
            this.paintFinancialValidation();
        }, () => [this.model.root.id, this.financialValidation.enabled,
            JSON.stringify(this.financialErrors())]);
        onWillUnmount(() => {
            cancelAnimationFrame(this.guidanceFrame);
            this.clearGuidance();
            this.clearFinancialGuidance();
        });
    }

    financialErrors() {
        return this.model.root.resModel === "lenka.financial.operation"
            ? financialValidationErrors(this.model.root.data) : [];
    }

    onWillLoadRoot(...args) {
        if (this.financialValidation) {
            this.financialValidation.enabled = false;
            this.clearFinancialGuidance();
        }
        return super.onWillLoadRoot(...args);
    }

    validateFinancialInputs() {
        if (this.model.root.resModel !== "lenka.financial.operation") {
            return true;
        }
        this.financialValidation.enabled = true;
        const errors = this.financialErrors();
        this.paintFinancialValidation(true);
        if (errors.length) {
            this.model.notification.add("Revise los campos marcados en rojo. Debajo de cada uno se indica cómo corregirlo.", {
                title: "Hay datos que corregir", type: "danger",
            });
            return false;
        }
        return true;
    }

    paintFinancialValidation(focus = false) {
        this.clearFinancialGuidance();
        const root = this.rootRef.el;
        if (!root || !this.financialValidation.enabled) {
            return;
        }
        const cleanup = [];
        let firstInput;
        for (const { field: fieldName, message } of this.financialErrors()) {
            for (const field of root.querySelectorAll(`.o_field_widget[name="${fieldName}"]`)) {
                const input = field.querySelector("input, select, textarea");
                const hint = document.createElement("span");
                hint.className = "o_lenka_financial_validation_hint";
                hint.textContent = message;
                hint.setAttribute("role", "alert");
                hint.id = `lenka_error_${this.model.root.id}_${fieldName}`;
                field.classList.add("o_lenka_financial_error");
                field.appendChild(hint);
                const previousInvalid = input?.getAttribute("aria-invalid");
                const previousDescribedby = input?.getAttribute("aria-describedby");
                input?.setAttribute("aria-invalid", "true");
                input?.setAttribute("aria-describedby", [previousDescribedby, hint.id].filter(Boolean).join(" "));
                if (!firstInput && input && field.getClientRects().length) {
                    firstInput = input;
                }
                cleanup.push(() => {
                    field.classList.remove("o_lenka_financial_error");
                    hint.remove();
                    for (const [attribute, previous] of [["aria-invalid", previousInvalid], ["aria-describedby", previousDescribedby]]) {
                        if (previous == null) {
                            input?.removeAttribute(attribute);
                        } else {
                            input?.setAttribute(attribute, previous);
                        }
                    }
                });
            }
        }
        this.clearFinancialGuidance = () => cleanup.forEach((clear) => clear());
        if (focus && firstInput) {
            firstInput.scrollIntoView({ block: "center", behavior: "smooth" });
            firstInput.focus({ preventScroll: true });
        }
    }

    async onWillSaveRecord(...args) {
        if (!this.validateFinancialInputs()) {
            return false;
        }
        return super.onWillSaveRecord(...args);
    }

    async save(params) {
        if (!this.validateFinancialInputs()) {
            return false;
        }
        return super.save(params);
    }

    async discard() {
        this.financialValidation.enabled = false;
        this.clearFinancialGuidance();
        return super.discard();
    }

    async beforeExecuteActionButton(params) {
        const record = this.model.root;
        if (params.special !== "cancel" && !this.validateFinancialInputs()) {
            return false;
        }
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
