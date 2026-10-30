/** @odoo-module **/

// Matches the server's financial constraints without changing any loan terms.
export function financialValidationErrors(data) {
    const errors = [];
    const add = (field, message) => errors.push({ field, message });
    const principal = Number(data.principal_amount || 0);
    const down = Number(data.down_payment || 0);
    const term = Number(data.term_months || 0);
    const months = Number(data.interest_only_months || 0);
    if (principal <= 0) {
        add("principal_amount", "Monto / Valor: ingrese un monto mayor que cero.");
    }
    if (down < 0 || down > principal) {
        add("down_payment", "Prima: ingrese un valor entre cero y el Monto / Valor de la operación.");
    }
    if (Number(data.interest_rate || 0) < 0) {
        add("interest_rate", "Tasa de interés: no puede ser negativa. Ingrese 0 o un porcentaje mayor.");
    }
    if (term <= 0) {
        add("term_months", "Plazo (meses): ingrese el plazo total, sumando los meses de intereses y los de cuota nivelada.");
    }
    if (months < 0 || (data.calculation_method === "interest_then_level" && months === 0)) {
        add("interest_only_months", "Meses de solo intereses: ingrese al menos 1 mes. Para 12 meses de intereses y 12 de cuota nivelada, indique 12 aquí y 24 en Plazo (meses).");
    } else if (data.calculation_method === "interest_then_level" && term > 0 && months >= term) {
        add("interest_only_months", `Meses de solo intereses: ${months} no puede ser igual o mayor que el plazo total de ${term}. Debe quedar al menos 1 mes de cuota nivelada.`);
        add("term_months", `Plazo (meses): debe ser mayor que los ${months} meses de solo intereses. Para ${months} meses de intereses y 12 de cuota nivelada, ingrese ${months + 12}.`);
    }
    const residual = Number(data.residual_purchase_percent || 0);
    if (residual < 0 || residual > 100) {
        add("residual_purchase_percent", "Opción de compra: ingrese un porcentaje entre 0 y 100.");
    }
    if (Number(data.balloon_base_payment || 0) < 0) {
        add("balloon_base_payment", "Cuota regular antes de bombas: ingrese cero o un monto positivo.");
    }
    const mora = Number(data.late_fee_rate || 0);
    if (!Number.isFinite(mora) || mora < 0 || mora > 100) {
        add("late_fee_rate", "Mora mensual (%): ingrese un porcentaje entre 0 y 100. Cero significa sin mora.");
    }
    if (Number(data.grace_days || 0) < 0) {
        add("grace_days", "Días de gracia: ingrese cero o un número positivo.");
    }
    return errors;
}
