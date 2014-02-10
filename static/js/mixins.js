/*global jQuery _ $*/

var SuperModel = function() {};

SuperModel.extend = function(protoProps, staticProps) {
    var parent = this;
    var child;

    if (protoProps && _.has(protoProps, 'constructor')) {
      child = protoProps.constructor;
    } else {
      child = function(){ return parent.apply(this, arguments); };
    }

    // Add static properties to the constructor function, if supplied.
    _.extend(child, parent, staticProps);

    // Set the prototype chain to inherit from `parent`, without calling
    // `parent`'s constructor function.
    var Surrogate = function(){ this.constructor = child; };
    Surrogate.prototype = parent.prototype;
    child.prototype = new Surrogate;

    // Add prototype properties (instance properties) to the subclass,
    // if supplied.
    if (protoProps) _.extend(child.prototype, protoProps);

    // Set a convenience property in case the parent's prototype is needed
    // later.
    child.__super__ = parent.prototype;

    return child;
};

var Model = SuperModel.extend({
    trigger : function(event_name, args) {
	if (typeof this.event_listeners === undefined) return;
	if (!_.has(this.event_listeners, event_name)) return;
	
	for (var i = 0; i < this.event_listeners[event_name].length; i++) {
	    try {
		this.event_listeners[event_name][i](args);
	    } catch (x) {
		if (x === "removeHandler") {
		    this.event_listeners[event_name].splice(i, 1); // really works
		} else {
		    throw x;
		}
	    }
	}
    },
    on : function(event_name, callback) {
	if (typeof callback !== 'function') throw new Exception("Callback should be a function");
	this.event_listeners = this.event_listeners || {};
	if (!_.has(this.event_listeners, event_name)) {
	    this.event_listeners[event_name] = [callback];
	} else {
	    this.event_listeners[event_name].push(callback);
	}
    },
    updateDisplay : function() {
	var disp_obj = this.objectifyDisplay();
	try {
	    for (var key in disp_obj) {
		this.el_display_props.filter('[data-prop="'+key+'"]').html(disp_obj[key]);
	    }
	} catch (e) {
	    console.log(e.stack);
	}
    }
});
