/** @odoo-module **/

import { AccountReport } from "@account_reports/components/account_report/account_report";
import { AccountReportLine } from "@account_reports/components/account_report/line/line";
import { AccountReportLineName } from "@account_reports/components/account_report/line_name/line_name";

export class CashflowAgedPartnerLineName extends AccountReportLineName {
    static template = "megatk_cash_flow_forecast.CashflowAgedPartnerLineName";

    get isCashflowPartnerLine() {
        return Boolean(this.props.line.cashflow_partner_id);
    }

    async cashflowAction(actionName) {
        const result = await this.orm.call(
            "cashflow.portfolio.snapshot",
            "action_from_aged_report",
            [
                this.props.line.cashflow_partner_id,
                this.props.line.cashflow_direction,
                actionName,
            ],
            { context: this.controller.context },
        );
        return this.action.doAction(result, {
            onClose: async () => {
                this.controller.incrementCallNumber();
                await this.controller.reload("", this.controller.cachedFilterOptions);
            },
        });
    }
}

export class CashflowAgedPartnerLine extends AccountReportLine {
    static template = "megatk_cash_flow_forecast.CashflowAgedPartnerLine";
    static components = {
        ...AccountReportLine.components,
        CashflowAgedPartnerLineName,
    };
}

AccountReport.registerCustomComponent(CashflowAgedPartnerLine);
