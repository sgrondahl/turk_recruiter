/*global jQuery Model _ $*/

"use scrict";

jQuery.fn.CType = function(params) {
    return new CType(this[0], params);
};

var CType = Model.extend({
    constructor : function(el, params) {
	params = params || {};
	this.onCreate = typeof params.onCreate === 'function' ? 
	    params.onCreate : 
	    function(ser) {
		console.log(JSON.stringify(ser));
	    };
	this.el = $(el);
	this.questionlist = new QuestionList();
	this.edit_template = $('#ctype-template').html();
	this.display_template = $('#ctype-display-template').html();
//	this.el.append(this.renderEdit()).append(this.renderDisplay());
	this.type_name = params.type_name || '';
	this.type_title = '<Title>';
	this.type_description = '';
    },
    renderEdit : function(el) {
	var self = this;
	this.el_edit = $(el);
	var sub_edit = $(document.createElement('div')).html(self.edit_template);
	sub_edit.find('.question-container:first').append(this.questionlist.renderEdit());
	sub_edit.find('input[name="type-name"]').val(this.type_name).keyup(function() {
	    self.onEdit();
	});
	sub_edit.find('button.create-new-type').click(function(evt) {
	    evt.preventDefault();
	    self.onCreate(self.serialize());
	});
	sub_edit.find('textarea').textareaAutoExpand().keyup(function() {
	    self.onEdit();
	});
	this.el_edit.append(sub_edit);
	this.updateDisplay();
    },
    renderDisplay : function(el) {
	var self = this;
	if (this.el_display !== undefined) {
	    throw "Error: CType renderDisplay called multiple times!!";
	} 
	this.el_display = $(el);
	var sub_disp = $(document.createElement('div'));
	sub_disp.html(self.display_template);
	this.el_display_props = sub_disp.find('[data-prop]');
	this.questionlist.renderDisplay(sub_disp.find('div.question-display-container:first'));
	this.el_display.append(sub_disp);
	this.updateDisplay();
    },
    objectifyDisplay : function() {
	return {
	    name : this.type_name,
	    title : this.type_title,
	    description : this.type_description
	};
    },
    onEdit : function() {
	if (this.el_edit !== undefined) {
	    this.type_name = this.el_edit.find('[name="type-name"]:first').val();
	    this.type_title = this.el_edit.find('[name="type-title"]:first').val();
	    this.type_description = this.el_edit.find('[name="type-description"]:first').val();
	}
	this.updateDisplay();
    },
    serialize : function() {
	return {
	    name : this.type_name,
	    title : this.type_title,
	    description: this.type_description,
	    questions : this.questionlist.serialize()
	};
    },
    deserialize : function(data) {
	if (typeof data !== 'object') throw "Error: CType.deserialize must be passed an object argument.";
	if (typeof data.name !== 'string') throw "Error: CType.deserialize must be passed a string name.";
	if (!data.questions instanceof Array) throw "Error: CType.deserialize must be passed an array questions.";
	this.type_name = data.name;
	this.updateDisplay();
	this.questionlist.deserialize(data.questions);
    }
});


var QuestionList = Model.extend({
    constructor : function() {
	this.questions = [];
	this.edit_template = $('#questionlist-template').html();
	this.display_template = $('#questionlist-display-template').html();
    },
    renderEdit : function() {
	if (this.el_edit !== undefined) {
	    throw "Error: trying to call renderEdit in QuestionList multiple times.";
	}
	var self = this;
	this.el_edit = $(document.createElement('div')).html(self.edit_template);
	this.question_holder = this.el_edit.find('div.all-questions');
	this.el_edit.find('.add-another-question a').click(function (evt) {
	    evt.preventDefault();
	    self.add($(this).attr('data-question-type'));
	});
	return this.el_edit;
    },
    renderDisplay : function(el) {
	if (this.el_display !== undefined) {
	    throw "Error: el_display redefined in QuestionList";
	}
	this.el_display = $(el);
	this.el_display.html(this.display_template);
    },
    add : function(q_type) {
	var self = this;
	var new_question = new Question(q_type);
	new_question.on('destroy', function(question) {
	    var live_questions = [];
	    for (var i = 0; i < self.questions.length; i++) {
		if (self.questions[i] !== question) live_questions.push(self.questions[i]);
	    }
	    self.questions = live_questions;
	});
	this.questions.push(new_question);
	this.question_holder.append(new_question.renderEdit());
	this.el_display.append(new_question.renderDisplay());
    },
    serialize : function() {
	var all_q_serialization = [];
	for (var i = 0; i < this.questions.length; i++) {
	    all_q_serialization.push(this.questions[i].serialize());
	}
	return all_q_serialization;
    },
    deserialize : function(data) {
	if (this.question_holder !== undefined) this.question_holder.empty();
	if (this.el_display !== undefined) this.el_display.empty();
	this.questions = [];
	for (var i = 0; i < data.length; i++) {
	    var new_question = new Question(data[i].type);
	    new_question.deserialize(data[i]);
	    this.questions.push(new_question);
	    if (this.question_holder !== undefined) this.question_holder.append(new_question.renderEdit());
	    if (this.el_display !== undefined) this.el_display.append(new_question.renderDisplay());
	}
    }
});

var Question = Model.extend({
    constructor : function(question_type) {
	var self;
	switch (question_type) {
	case 'radio':
	case 'checkbox':
	case 'select':
            self = new MCQuestion();
	    break;
	case 'scale':
	    self = new ScaleQuestion();
	    break;
	case 'grid':
	    self = new GridQuestion();
	    break;
	case 'text':
	    self = new TextQuestion();
	    break;
	default:
	    throw "Error: question given of odd type: " + question_type;
	}
	self.question_type = question_type;
	self.edit_template = $('#question-template').html();
	self.display_template = $('#question-display-template').html();
	self.question_text = '';
	return self;
    },
    objectifyDisplay : function() {
	return {
	    question_text : this.question_text
	};
    },
    renderEdit : function() {
	var self = this;
	this.el_edit = $(document.createElement('div'))
	    .html(self.edit_template)
	    .append(self.subrenderEdit());
	this.el_edit.find('textarea[name="question-text"]')
	    .keyup(function(evt) {
		evt.preventDefault();
		self.onQuestionChange($(this).val());
	    })
	    .textareaAutoExpand();
	this.el_edit.find('a.remove-question:first').click(function(evt) {
	    evt.preventDefault();
	    self.el_display.remove();
	    self.el_edit.remove();
	    self.trigger('destroy', self);
	});
	this.el_edit.find('.question-header-info').html(self.question_type);
	this.el_edit.append('<div><hr></div>');
	return this.el_edit;
    },
    renderDisplay : function() {
	if (this.el_display !== undefined) return this.el_display;
	this.el_display = $(document.createElement('div')).html(this.display_template);
	this.el_display_props = this.el_display.find('[data-prop]');
	var question_content_area = this.el_display_props.filter('[data-prop="question_content"]').first();
	this.subrenderDisplay(question_content_area);
	return this.el_display;
    },
    onQuestionChange : function(val) {
	this.question_text = val;
	this.updateDisplay();
    },
    serialize : function() {
	return {
	    content : this.subserialize(),
	    type : this.question_type,
	    text : this.question_text
	};
    },
    deserialize : function(data) {
	this.question_text = data.text;
	this.renderDisplay();
	this.updateDisplay();
	this.subdeserialize(data.content);
    }
});

var MCQuestion = Question.extend({
    constructor : function() {
	this.display_subtemplate = $('#mcquestion-display-template').html();
	this.edit_subtemplate = $('#mcquestion-template').html();
	this.optioninput = $('#mcquestion-option-template').html();
	this.group_name = _.uniqueId("mulletchoice_");
    },
    subrenderEdit : function() {
	var self = this;
	this.sub_el_edit = $(document.createElement('div')).html(self.edit_subtemplate);
	this.sub_el_edit.find('button.add-option').click(function(evt) {
		evt.preventDefault();
		self.addOption.call(self);
	    });
	this.options_holder = this.sub_el_edit.find('div.options-holder:first');
	this.addOption();
	return this.sub_el_edit;
    },
    subrenderDisplay : function(el) {
	this.sub_el_display = $(el);
	this.onOptionChange();
    },
    onOptionChange : function() {
	var self = this;
	this.options = [];
	if (this.sub_el_edit !== undefined) {
	    this.sub_el_edit.find('input[name="option-text"]').each(function() {
		self.options.push($(this).val());
	    });
	}
	this.subupdateDisplay();
    },
    subupdateDisplay : function() {
	if (this.sub_el_display !== undefined)
	    this.sub_el_display.html(_.template(this.display_subtemplate, this.objectifyOptions()));	
    },
    addOption : function(val) {
	var self = this;
	var new_option_holder = $(document.createElement('div')).addClass('option-holder');
	var new_option = $(this.optioninput);
	var new_option_input = new_option.find('input:first');
	if (typeof val === 'string') new_option_input.val(val);
	new_option_input.keyup(function() {
	    self.onOptionChange();
	});
	var new_option_close = new_option.find('button.remove-option:first');
	new_option_close
	    .click(function(evt) {
		evt.preventDefault();
		new_option_holder.remove();
		self.onOptionChange();
	    });
	new_option_holder.append(new_option);
	this.options_holder.append(new_option_holder);
	this.onOptionChange();
    },
    objectifyOptions : function() {
	return {
	    options : this.options, 
	    question_type: this.question_type,
	    group_name : this.group_name
	};
    },
    subserialize : function() {
	var all_options = [];
	if (this.sub_el_edit !== undefined) {
	    this.sub_el_edit.find('input[name="option-text"]').each(function() {
		all_options.push($(this).val());
	    });
	}
	return { options : all_options };
    },
    subdeserialize : function(data) {
	this.options = data.options;
	if (this.options_holder !== undefined) {
	    for (var i = 0; i < this.options.length; i++) {
		this.addOption(this.options[i]);
	    }
	} else {
	    this.subupdateDisplay();
	}
    }
});

var ScaleQuestion = Question.extend({
    constructor : function() {
	this.display_subtemplate = $('#scalequestion-display-template').html();
	this.edit_subtemplate = $('#scalequestion-template').html();
	this.group_name = _.uniqueId("slidervals_");
	this.scalecont = '';
	this.scalemin = 0;
	this.scalemax = 0;
	this.scalestep = 0;
    },
    subrenderEdit : function() {
	var self = this;
	this.sub_el_edit = $(document.createElement('div')).html(self.edit_subtemplate);
	this.scalecont_option = this.sub_el_edit.find('select[name=scalecont]').change(function() {
	    self.onChange();
	});
	this.scalemin_option = this.sub_el_edit.find('input[name=scalemin]')
	    .keyup(function() {
		self.onChange();
	    })
	    .change(function() {
		self.onChange();
	    });
	this.scalemax_option = this.sub_el_edit.find('input[name=scalemax]')
	    .keyup(function() {
		self.onChange();
	    })
	    .change(function() {
		self.onChange();
	    });
	this.scalestep_option = this.sub_el_edit.find('input[name=scalestep]')
	    .keyup(function() {
		self.onChange();
	    })
	    .change(function() {
		self.onChange();
	    });
	return this.sub_el_edit;
    },
    subrenderDisplay : function(el) {
	this.sub_el_display = $(el);
	this.subupdateDisplay();
    },
    onChange : function() {
	this.scalecont = this.scalecont_option.val();
	this.scalemin = parseFloat(this.scalemin_option.val());
	this.scalemax = parseFloat(this.scalemax_option.val());
	this.scalestep = parseFloat(this.scalestep_option.val());
	this.subupdateDisplay();
    },
    subupdateDisplay : function() {
	var slider_options = this.objectifyOptions();
	this.sub_el_display.html(_.template(this.display_subtemplate, slider_options));
	if (slider_options.scalecont === 'slider') this.drawSlider(slider_options);	
    },
    drawSlider : function(options) {
	var slider_amt_display_el = this.sub_el_display.find('.slider-amt:first');
	this.sub_el_display.find('.slider:first').slider({
	    value : options.scalemin,
	    min: options.scalemin,
	    max: options.scalemax,
	    step: options.scalestep,
	    slide : function(evt,ui) {
		slider_amt_display_el.html(ui.value);
	    }
	});
    },
    objectifyOptions : function() {
	return {
	    scalecont : this.scalecont,
	    scalemin : this.scalemin,
	    scalemax : this.scalemax,
	    scalestep : this.scalestep,
	    group_name : this.group_name
	};
    },
    subserialize : function() {
	return {
	    scalecont : this.scalecont,
	    scalemin : this.scalemin,
	    scalemax : this.scalemax,
	    scalestep : this.scalestep
	};
    },
    subdeserialize : function(data) {
	this.scalecont = data.scalecont;
	this.scalemin = data.scalemin;
	this.scalemax = data.scalemax;
	this.scalestep = data.scalestep;
	this.subupdateDisplay();
    }
});

var GridQuestion = Question.extend({
    constructor : function() {
	this.display_subtemplate = $('#gridquestion-display-template').html();
	this.edit_subtempate = $('#gridquestion-template').html();
	this.optioninput = $('#gridquestion-option-template').html();
	this.group_name =  _.uniqueId("gridchoice_");
	this.rowoptions = [];
	this.coloptions = [];
    },
    subrenderEdit : function() {
	var self = this;
	this.sub_el_edit = $(document.createElement('div')).html(self.edit_subtempate);
	this.sub_el_edit.find('button.add-rowoption').click(function(evt) {
	    evt.preventDefault();
	    self.addRowOption();
	});
	this.rowoptions_holder = this.sub_el_edit.find('div.rowoptions-holder:first');
	this.sub_el_edit.find('button.add-columnoption').click(function(evt) {
	    evt.preventDefault();
	    self.addColOption();
	});
	this.coloptions_holder = this.sub_el_edit.find('div.columnoptions-holder:first');
	this.addRowOption();
	this.addColOption();
	return this.sub_el_edit;
    },
    subrenderDisplay : function(el) {
	this.sub_el_display = $(el);
	this.onOptionChange();
    },
    generateOption : function() {
	var self = this;
	var new_option_holder = $(document.createElement('div')).addClass('option-holder');
	var new_option = $(self.optioninput);
	var new_option_input = new_option.find('input:first');
	new_option_input.keyup(function() {
	    self.onOptionChange();
	});
	var new_option_close = new_option.find('button.remove-option:first');
	new_option_close
	    .click(function(evt) {
		evt.preventDefault();
		new_option_holder.remove();
		self.onOptionChange();
	    });
	new_option_holder.append(new_option);
	return new_option_holder;
    },
    addRowOption : function() {
	this.rowoptions_holder.append(this.generateOption());
	this.onOptionChange();
    },
    addColOption : function() {
	this.coloptions_holder.append(this.generateOption());
	this.onOptionChange();
    },
    onOptionChange : function() {
	var self = this;
	this.rowoptions = [];
	this.coloptions = [];
	if (this.rowoptions_holder !== undefined && this.coloptions_holder !== undefined) {
	    this.rowoptions_holder.find('input[name="option-text"]').each(function() {
		self.rowoptions.push($(this).val());
	    });
	    this.coloptions_holder.find('input[name="option-text"]').each(function() {
		self.coloptions.push($(this).val());
	    });
	}
	this.subupdateDisplay();
    },
    subupdateDisplay : function() {
	if (this.sub_el_display !== undefined)
	    this.sub_el_display.html(_.template(this.display_subtemplate, this.objectifyOptions()));
    },
    objectifyOptions : function() {
	return {
	    rowoptions : this.rowoptions, 
	    coloptions : this.coloptions,
	    group_name : this.group_name
	};
    },
    subserialize : function() {
	return {
	    rowoptions : this.rowoptions, 
	    coloptions : this.coloptions
	};
    },
    subdeserialize : function(data) {
	this.rowoptions = data.rowoptions;
	this.coloptions = data.coloptions;
	this.subupdateDisplay();
    }
});


var TextQuestion = Question.extend({
    constructor : function() {
	this.display_subtemplate = $('#textquestion-display-template').html();
	this.edit_subtemplate = $('#textquestion-template').html();
    },
    subrenderEdit : function() {
	var self = this;
	this.sub_el_edit = $(document.createElement('div')).html(self.edit_subtemplate);
	this.textlength_el = this.sub_el_edit.find('select[name=textlength]');
	this.textlength_el.change(function() {
	    self.onChange();
	});
	return this.sub_el_edit;
    },
    subrenderDisplay : function(el) {
	this.sub_el_display = $(el);
	this.onChange();
    },
    onChange : function() {
	var self = this;
	if (this.sub_el_display !== undefined) 
	    this.sub_el_display.html(_.template(self.display_subtemplate, self.objectifyOptions()));
    },
    objectifyOptions : function() {
	return { textlength : this.textlength_el.val() };
    },
    subserialize : function() {
	return this.objectifyOptions();
    },
    subdeserialize : function() {
	throw "DIDNT DO TEXT YET!!!";
    }
});
