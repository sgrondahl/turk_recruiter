/*global jQuery Model _ $*/

"use strict";

jQuery.fn.CType = function(typeGroup, params) {
    return new CType(this[0], typeGroup, params);
};

var CTypeGroup = Model.extend({
    constructor : function () {
	      this.types = [];
    },
    addType : function (ctype) {
	      this.types.push(ctype);
    },
    showType : function (ctype) {
	      ctype = ctype || this.types[0];
	      _.each(this.types, function (t) {
	          if (t === ctype) {
		            t.show();
	          } else {
		            t.hide();
	          }
	      });
    },
    serialize : function () {
        return _.invoke(this.types, 'serialize');
    },
    validate : function () {
        function isInvalid(type) {
            return !type.validate();
        }
        var type = _.find(this.types, isInvalid);
        if (type) {
            this.showType(type);
            return false;
        } else {
            return true;
        }
    }
});

var CType = Model.extend({
    constructor : function(el, typeGroup, params) {
	      params = params || {};
	      this.el = $(el);
	      this.typeGroup = typeGroup;
	      typeGroup.addType(this);
	      this.display_template = $('#ctype-display-template').html();
	      this.name = params.name || '';
	      this.header = params.header || '';
	      this.questionlist = new QuestionList(params.questions || []);
	      this.el.empty();
    },
    renderDisplay : function() {
	      var self = this;
	      var sub_disp = $(document.createElement('div'));
	      sub_disp.html(self.display_template);
	      this.el_display_props = sub_disp.find('[data-prop]');
	      this.question_container = sub_disp.find('.question-display-container:first');
	      this.questionlist.renderDisplay(this.question_container);
	      this.el.append(sub_disp);
	      this.hide(true); // updatesdisplay, too
	      this.el.find(".ctype-when-hidden").on("click", function () {
	          self.typeGroup.showType(self);
	      });
	      this.el.find("form").on("change", function () {
	          $(".question-invalid").removeClass("question-invalid");
	      });
    },
    objectifyDisplay : function() {
	      return {
	          name : this.name,
	          header : this.header,
	          numQuestions : this.questionlist.numQuestions(),
	          numCompleted : this.questionlist.numCompleted()
	      };
    },
    serialize : function() {
	      return {
	          name : this.name,
	          responses : this.questionlist.serialize()
	      };	    
    },
    hide : function (fast) {
	      if (fast) {
	          this.el.find(".ctype-when-visible").hide();
	      } else {
	          this.el.find(".ctype-when-visible").slideUp();
	      }
	      this.el.find(".ctype-when-hidden").show();
	      this.updateDisplay();
    },
    show : function () {
	      this.el.find(".ctype-when-visible").slideDown();
	      this.el.find(".ctype-when-hidden").hide();
	      this.updateDisplay();
    },
    validate : function () {
	      return this.questionlist.validate();
    }
});


var QuestionList = Model.extend({
    constructor : function(questions) {
	      this.questions = questions || [];
	      this.display_template = $('#questionlist-display-template').html();
	      this.renderedquestions = [];
	      this.holders = [];
    },
    renderDisplay : function(el) {
        this.el = $(el);
	      this.el.empty();
        _.each(this.questions, function (q) {
	          var question_holder = $(document.createElement('li'));	    
	          var question = new Question(question_holder, q);
	          question.renderDisplay();
	          this.el.append(question_holder);
	          this.holders.push(question_holder);
	          this.renderedquestions.push(question);
	      }, this);
    },
    serialize : function() {
        return _.invoke(this.renderedquestions, 'serialize');
    },
    numQuestions : function () {
	      return this.renderedquestions.length;
    },
    numCompleted : function () {
        return _.chain(this.renderedquestions)
                .invoke('validate')
                .filter(_.identity) // keep true ones
                .size()
                .value();
    },
    validate : function () {
	      for (var i = 0; i < this.renderedquestions.length; i++) {
	          if (!this.renderedquestions[i].validate()) {
		            this.holders[i].addClass("question-invalid");
		            return false;
	          }
	      }
	      return true;
    }
});

var Question = Model.extend({
    constructor : function(el, question) {
	      var new_question = undefined;
	      switch (question.valuetype) {
	      case 'numeric':
            new_question = new NumericQuestion(el, question);
	          break;
	      case 'categorical':
	    	    new_question = new CategoricalQuestion(el, question);
	          break;
	      case 'text':
	          new_question = new TextQuestion(el, question);
	          break;
	      }

	      if (new_question === undefined)
          throw "Error: could not find type " + question.valuetype;

	      new_question.valuetype = question.valuetype;
	      new_question.questiontext = question.questiontext;
	      new_question.helptext = question.helptext;
	      new_question.varname = question.varname;
	      new_question.content = question.content;
	      new_question.options = question.options;
	      return new_question;
    },
    serialize : function() {
	      return { 
	          varname : this.varname,
	          response : this.response()
	      };
    },
    serializeForDisplay : function() {
	      return {
	          questiontext : this.questiontext,
	          valuetype : this.valuetype,
	          varname : this.varname,
	          content : this.content,
	          helptext : this.helptext,
	          options : this.options
	      };
    },
    validate : function () {
	      if (this.response() === undefined) {
	          return false;
	      } else {
	          return true;
	      }
    },
    renderHelpText : function() {
	      var self = this;
	      if (this.helptext) {
	          this.el.find('.help:first').popover({ placement : 'bottom',
						                                      title : undefined,
						                                      content : self.helptext,
						                                      trigger : 'manual' });
	          this.el.find('.help:first').click(function() {
		            $(this).popover('toggle');
	          });
	      }
    }
});

var TextQuestion = Question.extend({
    constructor : function(el, question) {
        this.el = $(el);
	      this.display_template = $('#textquestion-display-template').html();
    },
    renderDisplay : function() {
        this.el.empty();
        this.el.html(_.template(this.display_template, this.serializeForDisplay()));
	      this.renderHelpText();
    },
    validate : function () {
        return this.response() != "";
    },
    response : function() {
	      return this.el.find('textarea:first').val();
    }
});

var NumericQuestion = Question.extend({
    constructor : function(el, question) {
        this.el = $(el);
	      this.display_template = $('#numericquestion-display-template').html();
    },
    renderDisplay : function() {
        this.el.empty();
        this.el.html(_.template(this.display_template, this.serializeForDisplay()));
	      this.renderHelpText();
    },
    validate : function () {
        return this.response() && !isNaN(+this.response());
    },
    response : function() {
	      return this.el.find('input:first').val();
    }
});

var CategoricalQuestion = Question.extend({
    constructor : function(el, question) {
        this.el = $(el);
	      this.display_template = $('#catquestion-display-template').html();
	      this.display_template_sideways = $('#catquestionsideways-display-template').html();
	      this.nested_display_template = $('#catquestionsnested-display-template').html();
	      this.nesting_delimiter = '|';
    },
    shouldBeSideways : function () {
	      return this.options.layout === 'horizontal' || (this.content.length >= 5
		                                                    && _.all(this.content, function (choice) { return choice.text.length <= 2; }));
    },
    renderDisplay : function() {
        this.el.empty();
	      var self = this;
	      if (this.nest === undefined && this.isNested()) {
	          this.constructNesting();
	      } else {
	          this.nest = false;
	      }
	      if (this.nest) {
	          var rendered_nest = $(this.drawNesting(this.nest, 
						                                       this.nested_display_template, 
						                                       0, 
						                                       this.questiontext, 
						                                       this.varname));
	          rendered_nest
		            .find('input[type="radio"]')
		            .change(function() {
		                self.expandNest($(this), rendered_nest);
		            });
	          this.el.html(rendered_nest);
	      } else {
	          var t = this.shouldBeSideways() ? this.display_template_sideways : this.display_template;
            this.el.html(_.template(t, this.serializeForDisplay()));
	      }
	      this.renderHelpText();
    },
    isNested : function() {
	      return _.some(this.content, function(c) {
          return _.contains(c.text, this.nesting_delimiter);
        }, this);
    },
    constructNesting : function() {
	      this.nest = {};
	      var nest = {};
	      _.each(this.content, function(c) {
	          var n_pointer = this.nest;
	          _.each(c.text.split(/\s*\|\s*/), function(ordered_token) {
		            n_pointer = n_pointer[ordered_token] || (n_pointer[ordered_token] = {});
	          });
	          n_pointer['__val__'] = c.value;
	      }, this);
    },
    expandNest : function(el, top_el) {
	      var el_num = parseInt(el.attr('nesting-level'), 10);
	      // eliminate selections on all descendant radio buttons
	      el.find('input[type="radio"]').prop('checked', false);
	      // eliminate selections on all terminal radio buttons
	      top_el.find('input[type="radio"]').each(function() {
	          if ($(this).val() && $(this).val() !== el.val()) { $(this).prop('checked', false); }
	      });
	      top_el
	          .find('div.form-group')
	          .each(function() {
		            if (parseInt($(this).attr('nesting-level'), 10) > el_num) {
		                $(this).slideUp();
		            }
	          });
	      el.parent().siblings('div.form-group').slideDown();
    },
    drawNesting : function() {
	      return nestedTemplate(this.nest, this.nested_display_template, 0, this.questiontext, this.varname);
    },
    response : function() {
	      // darn selectors... (gross)
	      return this.el.find('input:not([value=""]):checked').val();
    } 
});

function nestedTemplate(nest, template, n, questiontext, varname) {
    if (nest === undefined) return '';

    return _.template(template, { varname : varname,
				                          questiontext : questiontext,
				                          content : nest,
				                          generator : nestedTemplate,
				                          template : template,
				                          n : ++n });
}
