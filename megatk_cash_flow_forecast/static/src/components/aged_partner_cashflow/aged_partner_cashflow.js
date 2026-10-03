/** @odoo-module **/

import { AccountReportLineName } from "@account_reports/components/account_report/line_name/line_name";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

patch(AccountReportLineName.prototype, {
    setup() {
        super.setup(...arguments);
        this.cashflowOrm = useService("orm");
        this.cashflowActionService = useService("action");
    },

    get isCashflowPartnerLine() {
        return Boolean(this.props.line.cashflow_partner_id);
    },

    async cashflowAction(actionName) {
        const result = await this.cashflowOrm.call(
            "cashflow.portfolio.snapshot",
            "action_from_aged_report",
            [
                this.props.line.cashflow_partner_id,
                this.props.line.cashflow_direction,
                actionName,
            ],
            { context: this.controller.context },
        );
        return this.cashflowActionService.doAction(result, {
            onClose: async () => {
                this.controller.incrementCallNumber();
                await this.controller.reload("", this.controller.cachedFilterOptions);
            },
        });
    },
});
