$(document).ready(function () {

  function open_menu(self) {
    if (self.hasClass("hola")) {
      // expand the panel
      self.parents(".active").find(".menu-social-link").slideDown();
      self
        .find("i")
        .removeClass("glyphicon-chevron-down")
        .addClass("glyphicon-chevron-up");
    } else {
      // collapse the panel
      self.parents(".active").find(".menu-social-link").slideUp();
      self
        .find("i")
        .removeClass("glyphicon-chevron-up")
        .addClass("glyphicon-chevron-down");
    }
  }

  let $button = $("#click");
  let $button2 = $("#click2");

  $button.on("click", function (e) {
    open_menu($(this));
    $(this).context.style.display='none'
  });

  $button2.on("click", function (e) {
    open_menu($(this));
    $button[0].style.display='block'

  });
});
