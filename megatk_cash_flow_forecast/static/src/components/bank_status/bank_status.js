/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


export class CashflowBankStatus extends Component {
    static template = "megatk_cash_flow_forecast.CashflowBankStatus";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({ loading: true, data: null, capturing: false });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "cashflow.plan", "get_bank_status_dashboard_data", [],
        );
        this.state.loading = false;
    }

    async captureNow() {
        this.state.capturing = true;
        try {
            await this.orm.call(
                "cashflow.bank.reconciliation.snapshot",
                "action_capture_current_company",
                [],
            );
            await this.load();
            this.notification.add("Se generó el corte bancario actual.", { type: "success" });
        } finally {
            this.state.capturing = false;
        }
    }

    openDetail() {
        return this.action.doAction(
            "megatk_cash_flow_forecast.action_cashflow_statistics",
        );
    }

    money(value) {
        const currency = this.state.data?.currency || "HNL";
        return this.moneyCurrency(value, currency);
    }

    moneyCurrency(value, currency) {
        return new Intl.NumberFormat("es-HN", {
            style: "currency",
            currency,
            maximumFractionDigits: 2,
        }).format(value || 0);
    }

    percent(value) {
        return `${Number(value || 0).toFixed(1)}%`;
    }

    get maxBalance() {
        const values = (this.state.data?.accounts || []).flatMap(
            (account) => [Math.abs(account.real), Math.abs(account.accounting)],
        );
        return Math.max(...values, 1);
    }

    barWidth(value) {
        return `${Math.max(1, Math.abs(value || 0) / this.maxBalance * 100)}%`;
    }

    get trendPoints() {
        const history = this.state.data?.history || [];
        if (!history.length) {
            return [];
        }
        const maxValue = Math.max(
            ...history.map((item) => item.absolute_difference), 1,
        );
        const width = 680;
        const height = 190;
        return history.map((item, index) => ({
            ...item,
            x: history.length === 1 ? width / 2 : index * width / (history.length - 1),
            y: height - (item.absolute_difference / maxValue * 160) - 15,
        }));
    }

    get trendPath() {
        return this.trendPoints.map(
            (point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`,
        ).join(" ");
    }

    statusLabel(status) {
        return {
            reconciled: "Conciliada",
            review: "Revisar",
            critical: "Crítica",
        }[status] || status;
    }
}

registry.category("actions").add("cashflow_bank_status_dashboard", CashflowBankStatus);
