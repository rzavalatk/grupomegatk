odoo.define('multi_chatbot_connector.composer', function (require) {
	"use strict";
	
	var Widget = require('web.Widget');
	var Composer = require('mail.composer.Basic');
	var dom = require('web.dom');
	
	Composer.include({
		start: function () {
			var self = this;
			this._$attachmentButton = this.$('.o_composer_button_add_attachment');
			this._$attachmentsList = this.$('.o_composer_attachments_list');
			this.$input = this.$('.o_composer_input textarea');
			this.$input.focus(function () {
				self.trigger('input_focused');
			});
			this.$input.val(this.options.defaultBody);
			dom.autoresize(this.$input, {
				parent: this,
				min_height: this.options.inputMinHeight
			});
			// Attachments
			this._renderAttachments();
			$(window).on(this.fileuploadID, this._onAttachmentLoaded.bind(this));
			this.on('change:attachment_ids', this, this._renderAttachments);
			// Mention
			this._mentionManager.prependTo(this.$('.o_composer'));
			return this._super();
		},
	});
	
});
