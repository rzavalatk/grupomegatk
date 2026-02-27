/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class AccountComisionesAction extends Component {
  static template = "account_comisiones.AccountComisionesTemplate";

  setup() {
    this.notification = useService("notification");
  }

  async generateExcel(recordId) {
    try {
      const response = await rpc({
        model: "account.comisiones",
        method: "generate_excel",
        args: [[recordId]],
      });

      if (response && response.data) {
        // Decodificar base64 y crear blob
        const byteCharacters = atob(response.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        });

        // Descargar archivo
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = response.name || "comisiones.xlsx";
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        link.remove();

        // Recargar página
        location.reload();
      }
    } catch (error) {
      this.notification.add(
        `Error: ${error.message || "Error desconocido"}`,
        { type: "danger" }
      );
    }
  }
}

// Registrar como acción cliente
registry.category("actions").add("account_comisiones_action", AccountComisionesAction);
