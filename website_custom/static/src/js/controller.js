odoo.define("breadcum_custom.front", ["web.ajax"], (require) => {
  "use strict";
  const ajax = require("web.ajax");

  $(document).ready(() => {
    ajax.jsonRpc("/get_images_breadcum").then((data) => {
      let section = document.getElementById("section_breadcum");
      if (section && data.image) {
        section.style.backgroundImage = `url('data:image/png;base64,${data.image}')`;
        section.style.backgroundRepeat = "no-repeat";
        section.style.backgroundPosition = "center center";
        section.style.backgroundSize = "cover";
      }
    });
  });
});
