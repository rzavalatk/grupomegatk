/** @odoo-module **/

import { Component, onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

const LABELS = {
    caries: "Caries", restoration: "Restauración", temporary_restoration: "Restauración temporal",
    missing: "Ausente", unerupted: "No erupcionada", crown: "Corona", bridge_abutment: "Pilar",
    pontic: "Póntico", implant: "Implante", root_canal: "Endodoncia",
    extraction_indicated: "Extracción indicada", fracture: "Fractura", mobility: "Movilidad dental (signo clínico)",
    sealant: "Sellante", prosthesis: "Prótesis", healthy: "Sana", other: "Otro",
};
const SURFACES = { whole: "Pieza", occlusal: "Oclusal", incisal: "Incisal", mesial: "Mesial", distal: "Distal", buccal: "Vestibular", lingual: "Lingual", palatal: "Palatina", cervical: "Cervical", root: "Raíz" };
const STATUSES = { existing: "Presente al examinar", planned: "Tratamiento planificado", completed: "Tratamiento realizado", monitor: "En seguimiento" };
const SEVERE = new Set(["caries", "fracture", "extraction_indicated", "missing"]);
const ROOT_PATHS = {
    1: "M17 27 C16 19 19 5 23 2 Q24 1 25 2 C29 5 32 19 31 27 Z",
    2: "M9 27 C7 13 10 4 15 3 C20 2 20 21 24 21 C28 21 28 2 33 3 C38 4 41 13 39 27 Z",
    3: "M7 27 C5 15 6 5 11 4 C17 3 18 18 19 27 Z M17 27 C17 13 21 2 24 2 C27 2 31 13 31 27 Z M29 27 C30 18 31 3 37 4 C42 5 43 15 41 27 Z",
};

export class OdontogramChart extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ teeth: [], findings: [], loading: true, error: false });
        onWillStart(() => this.load());
        onWillUpdateProps((nextProps) => {
            if (nextProps.record.resId !== this.props.record.resId) {
                return this.load(nextProps);
            }
        });
    }

    get chartId() { return this.props.record.resId; }
    get editable() { return Boolean(this.chartId) && this.props.record.data.state === "draft"; }
    get dentition() { return this.props.record.data.dentition || "permanent"; }
    get notation() { return this.props.record.data.numbering_system || "fdi"; }
    displayCode(tooth) { return this.notation === "ada" ? (tooth.ada_code || tooth.code) : tooth.code; }

    rootCount(tooth) {
        const position = Number(tooth.code[1]);
        const upper = "1256".includes(tooth.code[0]);
        if (position <= 3) return 1; // Incisivos y caninos.
        if (tooth.dentition === "permanent" && position <= 5) {
            return upper && position === 4 ? 2 : 1;
        }
        return upper ? 3 : 2; // Molares; forma típica, no diagnóstico de raíces reales.
    }
    rootPath(tooth) { return ROOT_PATHS[this.rootCount(tooth)]; }

    async load(props = this.props) {
        this.state.loading = true;
        this.state.error = false;
        try {
            const chartId = props.record.resId;
            const [teeth, findings] = await Promise.all([
                // Keep both catalogues in memory so changing dentition updates the arcs immediately.
                this.orm.searchRead("odental.tooth", [], ["code", "ada_code", "name", "dentition", "tooth_type"]),
                chartId ? this.orm.searchRead("odental.odontogram.finding", [["odontogram_id", "=", chartId]],
                    ["tooth_id", "surface", "condition", "status", "notes"]) : Promise.resolve([]),
            ]);
            this.state.teeth = teeth;
            this.state.findings = findings;
        } catch (error) {
            this.state.error = true;
        } finally {
            this.state.loading = false;
        }
    }

    get arcs() {
        const codes = this.dentition === "mixed" ? ["permanent", "primary"] : [this.dentition];
        return codes.map((kind) => {
            const upper = kind === "permanent" ? ["1", "2"] : ["5", "6"];
            const lower = kind === "permanent" ? ["4", "3"] : ["8", "7"];
            const by = (q) => this.state.teeth.filter((t) => t.code.startsWith(q));
            return {
                kind,
                title: kind === "permanent" ? "Dentición permanente" : "Dentición temporal",
                upper: [...by(upper[0]).sort((a, b) => b.code.localeCompare(a.code)),
                    ...by(upper[1]).sort((a, b) => a.code.localeCompare(b.code))],
                lower: [...by(lower[0]).sort((a, b) => b.code.localeCompare(a.code)),
                    ...by(lower[1]).sort((a, b) => a.code.localeCompare(b.code))],
            };
        });
    }

    findingsAt(tooth, surface) {
        return this.state.findings.filter((finding) => finding.tooth_id[0] === tooth.id && finding.surface === surface);
    }

    leftSurface(tooth) { return "1468".includes(tooth.code[0]) ? "distal" : "mesial"; }
    rightSurface(tooth) { return this.leftSurface(tooth) === "mesial" ? "distal" : "mesial"; }
    innerSurface(tooth) { return "1256".includes(tooth.code[0]) ? "palatal" : "lingual"; }
    centralSurface(tooth) { return ["incisor", "canine"].includes(tooth.tooth_type) ? "incisal" : "occlusal"; }

    zoneClass(tooth, surface) {
        const findings = this.findingsAt(tooth, surface);
        if (!findings.length) return "odt-zone";
        const className = findings.some((item) => item.status === "planned") ? "planned"
            : findings.some((item) => SEVERE.has(item.condition) && item.status !== "completed") ? "alert"
            : findings.some((item) => item.status === "completed") ? "completed" : "existing";
        return `odt-zone odt-zone--${className}`;
    }

    zoneTitle(tooth, surface) {
        const findings = this.findingsAt(tooth, surface);
        const detail = findings.map((f) => `${LABELS[f.condition] || f.condition} (${STATUSES[f.status] || f.status})`).join(", ");
        const roots = this.rootCount(tooth);
        return `${this.displayCode(tooth)} · ${tooth.name} · ${SURFACES[surface]}${surface === "root" ? ` · esquema de ${roots} ${roots === 1 ? "raíz" : "raíces"}` : ""}${detail ? `: ${detail}` : ""}`;
    }

    async openZone(tooth, surface) {
        if (!this.editable) return;
        // Keep the clinical record's regular save workflow and validation intact.
        const findings = this.findingsAt(tooth, surface);
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "odental.odontogram.finding",
            res_id: findings.length === 1 ? findings[0].id : undefined,
            views: [[false, "form"]],
            target: "new",
            context: {
                default_odontogram_id: this.chartId,
                default_tooth_id: tooth.id,
                default_surface: surface,
                odental_notation: this.notation,
            },
        }, { onClose: async () => {
            await this.load();
            await this.props.record.load();
        } });
    }
}

OdontogramChart.template = "odental_diagnostics.OdontogramChart";
OdontogramChart.props = { ...standardFieldProps };

registry.category("fields").add("odental_tooth_chart", {
    component: OdontogramChart,
    supportedTypes: ["char"],
});
