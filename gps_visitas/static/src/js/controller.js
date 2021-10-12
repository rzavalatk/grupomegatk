try {
  let str = "";
  let abc = "abcdefghijklmnopqrstuvwxyz";
  for (let i = 0; i < 4; i++) {
    str += abc.charAt(Math.floor(Math.random() * abc.length));
  }
  odoo.define(`gps_visitas.crm_lead-${str}`, function (require) {
    "use strict";
    const rpc = require("web.rpc");

    $(document).ready(function () {
      function getPoitionUser(field_lat, field_lng, field_date, method) {
        var options = {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0,
        };

        function success(pos) {
          let id = document.getElementsByName("id");
          if (id.length > 0) {
            id = id.item(0);
          } else {
            id = false;
          }
          let idInt = id.innerHTML.replace(/[,]/g, "");
          let date = new Date(pos.timestamp);
          rpc
            .query({
              model: "crm.lead",
              method: method,
              args: [
                [parseInt(idInt)],
                {
                  [field_lat]: pos.coords.latitude,
                  [field_lng]: pos.coords.longitude,
                  [field_date]: date,
                },
              ],
            })
            .done(function (data) {
              if (data) {
                location.reload();
              }
            })
            .fail(function (err) {
              console.warn("ERROR QUERY: (" + err.code + "): " + err.message);
            });
        }

        function error(err) {
          console.warn("ERROR POSITION: (" + err.code + "): " + err.message);
          $("#hidden_box").modal("show");
        }

        navigator.geolocation.getCurrentPosition(success, error, options);
      }

      const init_visit = $("#init_visit");
      const end_visit = $("#end_visit");
      const close = $("#buton-close");

      $("#go").click(function (e) {
        e.preventDefault();
        rpc
            .query({
              model: "crm.lead",
              method: "open_wizard",
              args: [[],],
            })
            .done(function (data) {
              window.location.href = $.param.querystring(location.origin + '/', {'fw': data});
            })
            .fail(function (err) {
              console.warn("ERROR QUERY: (" + err.code + "): " + err.message);
            });
      });

      if (close) {
        close.click(function (e) {
          e.preventDefault();
          location.reload();
        });
      }

      if (end_visit) {
        end_visit.click(function (e) {
          e.preventDefault();
          getPoitionUser(
            "lat_end_visit",
            "lng_end_visit",
            "timestamp_end_visit",
            "write_end"
          );
        });
      }
      if (init_visit) {
        init_visit.click(function (e) {
          e.preventDefault();
          getPoitionUser(
            "lat_init_visit",
            "lng_init_visit",
            "timestamp_init_visit",
            "write_init"
          );
        });
      }
    });
  });
} catch (error) {
  // console.log(error);
  location.reload();
}
