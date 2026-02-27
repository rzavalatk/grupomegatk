/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export const marksListViewExtension = {
  dependencies: ["action"],

  async start(env, { action }) {
    // Exportar plantilla Excel
    async function exportTemplate() {
      const columns = [
        { Fecha: "", Nombre: "", Hora: "" },
      ];
      
      // Convertir datos a CSV
      const headers = Object.keys(columns[0]);
      const csvContent = [
        headers.join(","),
        ...columns.map((row) => headers.map((h) => row[h] || "").join(",")),
      ].join("\n");

      // Descargar CSV como Excel
      const blob = new Blob([csvContent], {
        type: "text/csv;charset=utf-8;",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "plantilla-para-importar.csv";
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      link.remove();
    }

    // Generar reporte de horas extras
    async function generateHoursReport() {
      try {
        const response = await rpc({
          model: "hr.employee.markings",
          method: "open_generate_hours_xtra",
          args: [],
        });
        if (response) {
          await action.doAction(response);
        }
      } catch (error) {
        console.error("Error generando reporte de horas:", error);
      }
    }

    // Generar reporte Camarón Cuatrero
    async function generateCamaronReport() {
      try {
        const response = await rpc({
          model: "hr.employee.markings",
          method: "open_generate_camaron_cuatrero",
          args: [],
        });
        if (response) {
          await action.doAction(response);
        }
      } catch (error) {
        console.error("Error generando reporte camarón:", error);
      }
    }

    return {
      exportTemplate,
      generateHoursReport,
      generateCamaronReport,
    };
  },
};

registry.category("services").add("marksListExtension", marksListViewExtension);
