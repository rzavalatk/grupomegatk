odoo.define("ks_ecommerce_theme.search_autocomplete", function (require) {
  "use strict";

  $(document).ready(function () {
    var options = {
      url: function (query) {
        return "/get/search/suggestions/" + unescape(encodeURIComponent(query));
      },
      listLocation: "result",
      theme: "plate-dark",
      getValue: function (element) {
        if (element.currency_position == "before") {
          return "<div>" + element.name + "</div>";
          // +'<div>'+element.currency_symbol+element.prod_price+'</div>';
        } else if (
          typeof element.prod_price !== "undefined" &&
          typeof element.currency_symbol !== "undefined"
        ) {
          return "<div>" + element.name + "</div>";
          // +'<div>'+element.prod_price+element.currency_symbol+'</div>';
        } else {
          return element.name;
        }
      },
      template: {
        type: "iconLeft",
        fields: {
          iconSrc: "prod_url",
        },
      },
      list: {
        match: {
          enabled: true,
        },
        onChooseEvent: function (ev) {
          $('input[name="search"]').val(
            $('input[name="search"]').getSelectedItemData().name
          );
          if ($("header.affixed").length)
            window.location = $(
              'input[name="search"]:eq(1)'
            ).getSelectedItemData().url;
          else
            window.location = $(
              'input[name="search"]'
            ).getSelectedItemData().url;
        },
        maxNumberOfElements: 10,
      },
    };
    $('input[name="search"]').easyAutocomplete(options);
  });
});
