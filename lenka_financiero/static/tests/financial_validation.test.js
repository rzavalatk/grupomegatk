import { expect, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-mock";
import { contains, defineModels, fields, models, mountView, onRpc } from "@web/../tests/web_test_helpers";
import { financialValidationErrors } from "@lenka_financiero/views/financial_validation";
import "@lenka_financiero/views/operation_form";

class LenkaOperation extends models.Model {
    _name = "lenka.financial.operation";
    principal_amount = fields.Float({ default: 100000 });
    down_payment = fields.Float();
    interest_rate = fields.Float({ default: 3 });
    term_months = fields.Integer({ default: 12 });
    interest_only_months = fields.Integer();
    calculation_method = fields.Selection({ selection: [["level", "Cuota nivelada"], ["interest_then_level", "Solo intereses y luego cuota nivelada"]], default: "interest_then_level" });
    _records = [{ id: 1, principal_amount: 100000, interest_rate: 3, term_months: 12,
        interest_only_months: 0, calculation_method: "interest_then_level" }];
}
defineModels([LenkaOperation]);

const valid = { principal_amount: 100000, interest_rate: 3, down_payment: 0,
    term_months: 24, interest_only_months: 12, calculation_method: "interest_then_level" };
const arch = `<form js_class="lenka_operation_form"><header><button name="action_generate_schedule" type="object" string="Calcular plan"/></header><sheet><group>
    <field name="principal_amount"/><field name="down_payment"/><field name="interest_rate"/>
    <field name="term_months"/><field name="interest_only_months"/><field name="calculation_method"/>
    </group></sheet></form>`;
const mount = () => mountView({ type: "form", resModel: "lenka.financial.operation", resId: 1, arch });

test("valid phases and zero interest remain allowed", () => {
    expect(financialValidationErrors(valid)).toEqual([]);
    expect(financialValidationErrors({ ...valid, interest_rate: 0 })).toEqual([]);
    expect(financialValidationErrors({ ...valid, calculation_method: "level", interest_only_months: 0 })).toEqual([]);
});

test("zero months identifies the precise correction", () => {
    const errors = financialValidationErrors({ ...valid, term_months: 12, interest_only_months: 0 });
    expect(errors.map(e => e.field)).toEqual(["interest_only_months"]);
    expect(errors[0].message).toInclude("24 en Plazo");
});

test("phases consuming the whole term identify both fields", () => {
    expect(financialValidationErrors({ ...valid, term_months: 12 }).map(e => e.field))
        .toEqual(["interest_only_months", "term_months"]);
});

test("negative interest and excessive down payment identify their fields", () => {
    expect(financialValidationErrors({ ...valid, interest_rate: -3, down_payment: 200000 }).map(e => e.field))
        .toEqual(["down_payment", "interest_rate"]);
});

test("save blocks invalid months and removes red marks when corrected", async () => {
    let saves = 0;
    onRpc("web_save", () => { saves++; });
    await mount();
    await contains('[name="principal_amount"] input').edit("100001");
    await contains(".o_form_button_save").click();
    await animationFrame();
    expect(saves).toBe(0);
    expect('[name="interest_only_months"]').toHaveClass("o_lenka_financial_error");
    expect('[name="interest_only_months"] input').toHaveAttribute("aria-invalid", "true");
    expect(".o_lenka_financial_validation_hint").toHaveText(/Meses de solo intereses/);
    await contains('[name="term_months"] input').edit("24");
    await contains('[name="interest_only_months"] input').edit("12");
    await animationFrame();
    expect(".o_lenka_financial_error").toHaveCount(0);
    await contains(".o_form_button_save").click();
    expect(saves).toBe(1);
});

test("calculate stops before a server request for invalid phases", async () => {
    let calculates = 0;
    onRpc("action_generate_schedule", () => { calculates++; return true; });
    await mount();
    await contains('button[name="action_generate_schedule"]').click();
    await animationFrame();
    expect(calculates).toBe(0);
    expect('[name="interest_only_months"]').toHaveClass("o_lenka_financial_error");
    expect(".o_dialog").toHaveCount(0);
});

test("equal phases highlight both term and interest months", async () => {
    await mount();
    await contains('[name="interest_only_months"] input').edit("12");
    await contains(".o_form_button_save").click();
    await animationFrame();
    expect('[name="interest_only_months"]').toHaveClass("o_lenka_financial_error");
    expect('[name="term_months"]').toHaveClass("o_lenka_financial_error");
});
