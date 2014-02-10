/*global jQuery Model _ $ CType*/

"use strict";

jQuery.fn.TypesPage = function(params) {
    return new TypesPage(this[0], params);
};

var TypesPage = Model.extend({
    constructor : function(el, params) {
	this.el = $(el);
	this.el_all_type_view = this.el.find('#view-all-types').first();
	this.template_all_type_view = $('#view-all-types-template').html();
	this.el_begin_type = this.el.find('#begin-new-type').first();
	this.el_create_type = this.el.find('#create-new-type').first();
	this.el_one_type_view = this.el.find('#view-type').first();
	this.initializePage();
    },
    initializePage : function() {
	var self = this;
	this.retrieveTypeNames(function(data) {
	    self.el_all_type_view.html(_.template(self.template_all_type_view, { type_names : data }));
	    self.el_all_type_view.find('a').click(function(evt) {
		evt.preventDefault();
		$.get('/types/view/'+$(this).html(), function(type_json) {
		    self.initializeTypeView(type_json);
		});
	    });
	});
	this.el_begin_type.find('button:first').click(function(evt) {
	    evt.preventDefault();
	    self.initializeCreateForm();
	});
	this.el_all_type_view.show();
	this.el_begin_type.show();
	this.el_create_type.hide();
	this.el_one_type_view.hide();

    },
    retrieveTypeNames : function(callback) {
	$.get('/types/all', function(data) { callback(data); });
    },
    createNewType : function(data, callback) {
	$.post('/types/new', {ctype : JSON.stringify(data)}, callback);
    },
    initializeCreateForm : function() {
	var self = this;
	var name = this.el_begin_type.find('input:first').val();
	this.el_create_type.children().empty();
	this.el_begin_type.find('input:first').val('');
	var ctype = new CType(undefined, {onCreate : self.createNewType, type_name : name});
	ctype.renderEdit(this.el_create_type.find('.new-type-edit:first'));
	ctype.renderDisplay(this.el_create_type.find('.new-type-display:first'));
	this.el_all_type_view.hide();
	this.el_begin_type.hide();
	this.el_one_type_view.hide();
	this.el_create_type.show();
    },
    initializeTypeView : function(data) {
	var self = this;
	var name = this.el_begin_type.find('input:first').val();
	this.el_begin_type.find('input:first').val('');
	this.el_one_type_view.empty();
	var ctype = new CType(undefined, {});
	ctype.renderDisplay(this.el_one_type_view);
	ctype.deserialize(data);
	var back_button = $(document.createElement('button')).addClass('btn btn-default').html('Back');
	back_button.click(function(evt) {
	    evt.preventDefault();
	    self.initializePage();
	});
	this.el_one_type_view.append(back_button);
	this.el_all_type_view.hide();
	this.el_begin_type.hide();
	this.el_create_type.hide();
	this.el_one_type_view.show();
    }
});
