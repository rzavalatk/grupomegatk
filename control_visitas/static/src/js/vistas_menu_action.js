/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class VisitasMenuActionComponent extends Component {
    static template = "VisitasMenuDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.root = useRef("root");
        this.state = useState({
            value_filtro: "reg_tgu",
            filtro_dias: "this_day_reg_tgu",
        });

        onMounted(() => this._initializeDashboard());
    }

    _getRootEl() {
        return this.root && this.root.el ? this.root.el : this.el;
    }

    async _initializeDashboard() {
        try {
            const result = await rpc("/control_visitas_user_reg");
            const isAdmin = result.user_email === 'lmoran@megatk.com' || result.user_email === 'areyes@megatk.com';
            
            if (!isAdmin) {
                if (result.user_reg === "3") {
                    this.state.value_filtro = "reg_tgu";
                } else if (result.user_reg === "2") {
                    this.state.value_filtro = "reg_sps";
                }
            }
            
            const root = this._getRootEl();
            if (!root) {
                return;
            }

            // Set initial filtro_dias
            const filterSelect = root.querySelector("#filter_selection");
            if (filterSelect) {
                this.state.filtro_dias = filterSelect.value + (this.state.value_filtro === "reg_tgu" ? "_tgu" : "_sps");
            }
            
            await this._updateView(this.state.value_filtro);
        } catch (error) {
            console.error("Error initializing dashboard:", error);
        }
    }

    _getResultValue(result, field, reg) {
        if (!result) {
            return 0;
        }
        const withReg = `${field}${reg}`;
        if (Object.prototype.hasOwnProperty.call(result, withReg)) {
            return result[withReg];
        }
        if (Object.prototype.hasOwnProperty.call(result, field)) {
            return result[field];
        }
        return 0;
    }

    _onChangeFilter(ev) {
        ev.preventDefault();
        this.state.value_filtro = ev.target.value;
        this._updateView(this.state.value_filtro);
    }

    async _onClickDeleteRecord(ev) {
        ev.preventDefault();
        const tienda = ev.currentTarget.id;
        await this._deleteRecord(tienda);
    }

    async _deleteRecord(tienda) {
        const reg = this.state.value_filtro === "reg_tgu" ? "_tgu" : "_sps";
        const zona = this.state.value_filtro === "reg_tgu" ? "TGU" : "SPS";

        const methods = {
            administracion: { element: "admin_value", field: "admin", method: "borrar_administracion" },
            tienda_megatk: { element: "megatk_value", field: "megatk", method: "borrar_tienda_megatk" },
            tienda_meditek: { element: "meditek_value", field: "meditek", method: "borrar_tienda_meditek" },
            lenka: { element: "lenka_value", field: "lenka", method: "borrar_lenka" },
            clinica: { element: "clinica_value", field: "clinica", method: "borrar_clinica" },
            gerencia: { element: "gerencia_value", field: "gerencia", method: "borrar_gerencia" },
            soporte: { element: "soporte_value", field: "soporte", method: "borrar_soporte" },
            otros: { element: "otros_value", field: "otros", method: "borrar_otros" },
        };

        if (methods[tienda]) {
            try {
                const result = await this.orm.call('control.visitas', methods[tienda].method, [zona, this.state.filtro_dias]);
                const root = this._getRootEl();
                const el = root ? root.querySelector(`#${methods[tienda].element}`) : null;
                if (el) {
                    el.textContent = this._getResultValue(result, methods[tienda].field, reg);
                }
            } catch (error) {
                console.error(`Error in delete ${tienda}:`, error);
            }
        }
    }

    async _updateView(valueFiltro) {
        const reg = valueFiltro === "reg_tgu" ? "_tgu" : "_sps";
        await this._updateUI(reg);
    }

    async _updateUI(reg) {
        try {
            const response = await rpc(`/control_visitas${reg}`);
            this._updateDashboardValues(response);
            this._attachEventListeners(reg);
        } catch (error) {
            console.error("Error loading dashboard:", error);
        }
    }

    _updateDashboardValues(data) {
        const root = this._getRootEl();
        if (!root) {
            return;
        }
        const fields = ['admin', 'meditek', 'lenka', 'clinica', 'megatk', 'gerencia', 'soporte', 'otros'];
        fields.forEach(field => {
            const el = root.querySelector(`#${field}_value`);
            if (el) {
                el.textContent = data[field] || 0;
            }
        });
    }

    _attachEventListeners(reg) {
        const root = this._getRootEl();
        if (!root) {
            return;
        }
        const bindOnce = (el, eventName, handler) => {
            if (!el) {
                return;
            }
            const key = `bound${eventName}`;
            if (el.dataset[key] === "1") {
                return;
            }
            el.dataset[key] = "1";
            el.addEventListener(eventName, handler);
        };

        // Attach filter change listener
        const filterSelect = root.querySelector("#filter_selection");
        if (filterSelect) {
            bindOnce(filterSelect, "change", (e) => this._onFilterChange(e, reg));
        }

        // Attach button listeners
        const buttons = [
            { id: 'admin_state', method: 'visita_administracion', field: 'admin' },
            { id: 'megatk_state', method: 'visita_tienda_megatk', field: 'megatk' },
            { id: 'meditek_state', method: 'visita_tienda_meditek', field: 'meditek' },
            { id: 'lenka_state', method: 'visita_lenka', field: 'lenka' },
            { id: 'clinica_state', method: 'visita_clinica', field: 'clinica' },
            { id: 'gerencia_state', method: 'visita_gerencia', field: 'gerencia' },
            { id: 'soporte_state', method: 'visita_soporte', field: 'soporte' },
            { id: 'otros_state', method: 'visita_otros', field: 'otros' },
        ];

        buttons.forEach(btn => {
            const el = root.querySelector(`#${btn.id}`);
            bindOnce(el, "click", async () => {
                const zona = this.state.value_filtro === "reg_tgu" ? "TGU" : "SPS";
                try {
                    const result = await this.orm.call('control.visitas', btn.method, [zona, this.state.filtro_dias]);
                    const valueEl = root.querySelector(`#${btn.field}_value`);
                    if (valueEl) {
                        valueEl.textContent = this._getResultValue(result, btn.field, reg);
                    }
                } catch (error) {
                    console.error(`Error calling ${btn.method}:`, error);
                }
            });
        });

        const deleteButtons = [
            "administracion",
            "tienda_megatk",
            "tienda_meditek",
            "lenka",
            "clinica",
            "gerencia",
            "soporte",
            "otros",
        ];

        deleteButtons.forEach((id) => {
            const el = root.querySelector(`#${id}`);
            bindOnce(el, "click", async (ev) => {
                ev.preventDefault();
                await this._deleteRecord(id);
            });
        });
    }

    async _onFilterChange(ev, reg) {
        const value = ev.target.value;
        const valFilter = value + reg;
        this.state.filtro_dias = valFilter;

        let endpoint = `/control_visitas${reg}`;
        if (value === 'this_day') endpoint = `/control_visitas_dia${reg}`;
        else if (value === 'this_week') endpoint = `/control_visitas_semana${reg}`;
        else if (value === 'this_month') endpoint = `/control_visitas_mes${reg}`;
        else if (value === 'this_year') endpoint = `/control_visitas_anio${reg}`;

        try {
            const result = await rpc(endpoint);
            this._updateDashboardValues(result);
        } catch (error) {
            console.error("Error loading filtered data:", error);
        }
    }
}

registry.category("actions").add("control_visitas_tag", VisitasMenuActionComponent);
