odoo.define('multi_chatbot_connector.im_livechat', function (require) {
	"use strict";
	
	var Widget = require('web.Widget');
	var dom = require('web.dom');
	var Imlivechat = require('im_livechat.im_livechat');
	
	Imlivechat.LivechatButton.include({
		close_waiting_screen: function (history,res_msg) {
			$('#waitingscreen').remove();
		},
	});
});
