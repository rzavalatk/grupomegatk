try {
  let str = "";
  let abc = "abcdefghijklmnopqrstuvwxyz";
  for (let i = 0; i < 4; i++) {
    str += abc.charAt(Math.floor(Math.random() * abc.length));
  }
  odoo.define(`hours.xtra.${str}`, function (require) {
    "use strict";
    const rpc = require("web.rpc");
    var FormRenderer = require("web.FormRenderer");
    const myExcelXML = require("excel.xml");
    var Dialog = require("web.Dialog");
    let data = {};

    FormRenderer.include({
      confirmChange: function (state, id, fields, e) {
        if (fields.length > 0) {
          data[fields[0]] = state.data[fields[0]];
        }
        return this._super.apply(this, arguments);
      },
    });

    function rpc_consult(data) {
      rpc
        .query({
          model: "hours.xtras",
          method: "dat_form_custom",
          args: [[data]],
        })
        .done(function (e) {
          if (e) {
            var XML = new myExcelXML(
              e,
              `horas_extra_${data.date.format("DD-MM-YYYY")}`
            );
            XML.downLoad();
            location.reload();
          }
        })
        .fail(function (err) {
          console.warn("ERROR QUERY: (" + err.code + "): " + err.message);
        });
    }

    function rpc_consult_2(data) {
      rpc
        .query({
          model: "camaro.cuatrero",
          method: "filter_camaron_cuatrero",
          args: [[data]],
        })
        .done(function (e) {
          console.log(e);
          if (!e.empty) {
            var XML = new myExcelXML(e.data, "llegadas_tarde");
            XML.downLoad();
            location.reload();
          } else {
            var html = `
              No hay datos a mostrar para la(s) fecha(s) seleccionada(s)

              Sugerencia: Evite seleccionar días libres, vacaciones nacionales o días festivos
            `
            Dialog.alert(this, html,{
              confirm_callback: function() {
                location.reload();
              },
              title: _t('Notificación'),
          });
          }
        })
        .fail(function (err) {
          console.warn("ERROR QUERY: (" + err.code + "): " + err.message);
        });
    }

    let button = $("#generate_button");
    let button2 = $("#generate_excel");

    button2.click(function (e) {
      if (Object.keys(data).length === 3) {
        e.preventDefault();
        rpc_consult_2(data);
      }
    });

    button.click(function (e) {
      e.preventDefault();
      if (data.employee_ids) {
        let temp = [];
        data.employee_ids.data.forEach((element) => {
          temp.push(element.data.id);
        });
        data.employee_ids = temp;
      }
      rpc_consult(data);
    });

    new FormRenderer();
  });
} catch (error) {
  //   console.log(error);
  location.reload();
}
