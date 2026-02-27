/** @odoo-module **/

// Módulo de compatibilidad para código legado que usa web.* en Odoo 18.
// Define wrappers mínimos alrededor de la nueva API JS.

odoo.define("web.rpc", ["@web/core/network/rpc"], function (require) {
    "use strict";
    const { rpc } = require("@web/core/network/rpc");

    function withCsrfToken(params) {
        const token = typeof odoo !== "undefined" ? odoo.csrf_token : null;
        if (!token || !params || typeof params !== "object" || Array.isArray(params)) {
            return params || {};
        }
        if (!Object.prototype.hasOwnProperty.call(params, "csrf_token")) {
            return {
                ...params,
                csrf_token: token,
            };
        }
        return params;
    }

    function query(params) {
        // Emular web.rpc.query para llamadas a modelos (call_kw)
        const promise = rpc("/web/dataset/call_kw", withCsrfToken(params));
        // Añadir helpers .done() / .fail() estilo jQuery
        promise.done = function (cb) {
            promise.then(cb);
            return promise;
        };
        promise.fail = function (cb) {
            promise.catch(cb);
            return promise;
        };
        return promise;
    }

    return {
        query,
    };
});

odoo.define("web.ajax", ["@web/core/network/rpc"], function (require) {
    "use strict";
    const { rpc } = require("@web/core/network/rpc");

    function withCsrfToken(params) {
        const token = typeof odoo !== "undefined" ? odoo.csrf_token : null;
        if (!token || !params || typeof params !== "object" || Array.isArray(params)) {
            return params || {};
        }
        if (!Object.prototype.hasOwnProperty.call(params, "csrf_token")) {
            return {
                ...params,
                csrf_token: token,
            };
        }
        return params;
    }

    // Implementación simple de ajax.jsonRpc basada en el nuevo rpc()
    function jsonRpc(url, method, params) {
        // "method" se ignora; la mayoría del código legado usa siempre 'call'
        return rpc(url, withCsrfToken(params));
    }

    return {
        jsonRpc,
    };
});

// Shim para el “composer” legacy del chat (mail.composer.Basic)
// Solo expone include/extend para permitir parches suaves; la lógica real
// del discus moderno sigue en los módulos core de Odoo 18.
odoo.define("mail.composer.Basic", [], function (require) {
    "use strict";

    class BasicComposer {}

    BasicComposer.include = function (props) {
        Object.assign(BasicComposer.prototype, props || {});
        return BasicComposer;
    };

    BasicComposer.extend = function (props) {
        class ExtendedComposer extends BasicComposer {}
        Object.assign(ExtendedComposer.prototype, props || {});
        return ExtendedComposer;
    };

    return BasicComposer;
});

odoo.define("web.core", [
    "@web/core/l10n/translation",
    "@web/core/registry",
    "@web/core/qweb",
], function (require) {
    "use strict";
    const { _t } = require("@web/core/l10n/translation");
    const { registry } = require("@web/core/registry");
    const { qweb } = require("@web/core/qweb");

    const core = {
        _t,
        qweb,
        action_registry: registry.category("actions"),
    };

    return core;
});

// Shim mínimo para el WebClient legacy, basado en el nuevo webclient.
odoo.define("web.WebClient", ["@web/webclient/webclient"], function (require) {
    "use strict";
    const { WebClient } = require("@web/webclient/webclient");
    // Añadimos helpers include/extend para código antiguo que parchea WebClient
    if (!WebClient.include) {
        WebClient.include = function (props) {
            Object.assign(WebClient.prototype, props || {});
            return WebClient;
        };
    }
    if (!WebClient.extend) {
        WebClient.extend = function (props) {
            class ExtendedWebClient extends WebClient {}
            Object.assign(ExtendedWebClient.prototype, props || {});
            return ExtendedWebClient;
        };
    }
    return WebClient;
});

odoo.define("web.FormController", ["@web/views/form/form_controller"], function (require) {
    "use strict";
    const { FormController } = require("@web/views/form/form_controller");

    if (!FormController.include) {
        FormController.include = function (props) {
            Object.assign(FormController.prototype, props || {});
            return FormController;
        };
    }

    if (!FormController.extend) {
        FormController.extend = function (props) {
            class ExtendedFormController extends FormController {}
            Object.assign(ExtendedFormController.prototype, props || {});
            return ExtendedFormController;
        };
    }

    return FormController;
});

odoo.define("web.ListController", ["@web/views/list/list_controller"], function (require) {
    "use strict";
    const { ListController } = require("@web/views/list/list_controller");

    if (!ListController.include) {
        ListController.include = function (props) {
            Object.assign(ListController.prototype, props || {});
            return ListController;
        };
    }

    if (!ListController.extend) {
        ListController.extend = function (props) {
            class ExtendedListController extends ListController {}
            Object.assign(ExtendedListController.prototype, props || {});
            return ExtendedListController;
        };
    }

    return ListController;
});

odoo.define("web.AbstractAction", ["@odoo/owl", "@web/core/network/rpc"], function (require) {
    "use strict";
    const { Component } = require("@odoo/owl");
    const { rpc } = require("@web/core/network/rpc");

    function withCsrfToken(params) {
        const token = typeof odoo !== "undefined" ? odoo.csrf_token : null;
        if (!token || !params || typeof params !== "object" || Array.isArray(params)) {
            return params || {};
        }
        if (!Object.prototype.hasOwnProperty.call(params, "csrf_token")) {
            return {
                ...params,
                csrf_token: token,
            };
        }
        return params;
    }

    class AbstractAction extends Component {
        // Pequeño helper para emular this._rpc(...) en acciones antiguas
        _rpc(params) {
            return rpc("/web/dataset/call_kw", withCsrfToken(params));
        }
    }

    // Emular API antigua AbstractAction.extend({...})
    AbstractAction.extend = function (props) {
        class Extended extends AbstractAction {}
        if (props) {
            Object.assign(Extended.prototype, props);
            if (props.template && !Extended.template) {
                Extended.template = props.template;
            }
        }
        return Extended;
    };

    return AbstractAction;
});

// Shim para widgets básicos (web.Widget)
odoo.define("web.Widget", ["@odoo/owl"], function (require) {
    "use strict";
    const { Component } = require("@odoo/owl");

    class Widget extends Component {
        constructor(parent, options) {
            super(...arguments);
            this.parent = parent || null;
            this.options = options || {};
        }
        // Helper jQuery-like
        $(selector) {
            return this.el ? $(this.el).find(selector) : $(selector);
        }
    }

    // API legacy: Widget.extend({...})
    Widget.extend = function (props) {
        class ExtendedWidget extends Widget {}
        Object.assign(ExtendedWidget.prototype, props || {});
        return ExtendedWidget;
    };

    return Widget;
});

// Shim muy ligero para utilidades de DOM usadas en algunos módulos (web.dom)
odoo.define("web.dom", [], function (require) {
    "use strict";

    function autoresize($textarea, options) {
        const el = $textarea && $textarea[0] ? $textarea[0] : null;
        if (!el) {
            return;
        }
        const minHeight = options && options.min_height ? options.min_height : el.offsetHeight;
        function resize() {
            el.style.height = "auto";
            el.style.height = Math.max(minHeight, el.scrollHeight) + "px";
        }
        $textarea.on("input", resize);
        resize();
    }

    return {
        autoresize,
    };
});

// Shim para widgets públicos de sitio web (web.public.widget)
odoo.define("web.public.widget", ["@web/legacy/js/public/public_widget"], function (require) {
    "use strict";
    const publicWidget = require("@web/legacy/js/public/public_widget");
    return publicWidget;
});

// Shim para cuadros de diálogo clásicos (web.Dialog)
odoo.define("web.Dialog", ["@web/core/dialog/dialog"], function (require) {
    "use strict";
    const { Dialog } = require("@web/core/dialog/dialog");
    return Dialog;
});

// Shim para la sesión (web.session)
odoo.define("web.session", ["@web/session"], function (require) {
    "use strict";
    const { session } = require("@web/session");
    return session;
});

// Stubs mínimos para módulos de bus legacy usados por algunos addons
odoo.define("bus.Longpolling", [], function (require) {
    "use strict";
    // El bus real ya está gestionado por el core en Odoo 18;
    // devolvemos un objeto vacío solo para satisfacer los require() legacy.
    return {};
});

odoo.define("bus.BusService", [], function (require) {
    "use strict";
    // Stub sin comportamiento: el servicio de bus se inicializa por el core.
    return {};
});
