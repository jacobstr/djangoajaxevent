/**
 * @depends JSON2.js
 * @depends jQuery 1.4.2
 */
(function(jQuery)
{

var DjangoAjax = window.DjangoAjax = { instances: {} };

DjangoAjax.makeClass = // makeClass - By John Resig (MIT Licensed)
	function makeClass(){
		return function(args){
			if ( this instanceof arguments.callee ) {
				if ( typeof this.init == "function" )
					this.init.apply( this, args.callee ? args : arguments );
			} else
				return new arguments.callee( arguments );
		};
	};

// See http://forum.jquery.com/topic/jquery-post-1-4-1-is-appending-to-vars-when-posting-from-array-within-array
jQuery.ajaxSettings.traditional = true;

// Used as a convention in our ajax calls.
window.DjangoAjax.isException = function(data) {
	if(data && data.isException && data.type.length)
	{
		return true;
	}
	else
	{
		return false;
	}
}

function ajaxUrl(method, name, url_args, url_kwargs, data) {
	var ret;
	if(!data)
		data = {};
	if(url_args)
		data['djangoajax_args'] = JSON.stringify(url_args);
	if(url_kwargs)
		data['djangoajax_kwargs'] = JSON.stringify(url_kwargs);
    
    /*
    var c = 0;

    // Convert args to keyed dictionary
    for (i in args) {
        arguments[c] = args[i];
        c++;
    }*/

    $.ajax({
        async: false,
        url: '/ajax_event/'+method+'/' + name + '/',
        data: data,
        success: function(html) {
            ret = html;
        }
    });

    if (ret && (ret.length > 0) ) {
        return ret;
    }
    else {
        return null;
    }
};

window.DjangoAjax.reverse = function(name, url_args, url_kwargs, data) {
    return ajaxUrl('reverse',name, url_args, url_kwargs, data);
}

window.DjangoAjax.resolve = function(name, url_args, url_kwargs, data) {
    return ajaxUrl('resolve',name, url_args, url_kwargs, data);
}

var DjangoResponse = window.DjangoAjax.DjangoResponse =  DjangoAjax.makeClass();

DjangoResponse.prototype.init = function(data){
	if(typeof data == 'string')
	{
		data = JSON.parse(data);
	}

	this.validate(data);

	// The namespace default here should match what we've defined in Django.
	this.data = data;
};

/**
 * Trigger events for this DjangoResponse. I.E. if the DjangoResponse has a type of 'Messages' then
 * you can listen for it via jQuery(document).bind('Messages.django') - Notice the namespacing of the event.
 */
DjangoResponse.prototype.trigger = function(element){
	var self = this;

	if(!element) {
		element = document;
	}

	jQuery.each(this.data.payload,function(k, el){
		var nsparts = [el.type, 'django'];
		self.validate(el);
		// Trigger once without custom namespace
		jQuery(element).trigger(nsparts.join('.'), el);
		if(self.data.namespace) {
			nsparts = [el.type, self.data.namespace];
			// Trigger again with custom namspace
			jQuery(element).trigger(nsparts.join('.'), el);
		}
	});
};

DjangoResponse.prototype.validate = function(data){
	if(!data.djangoPayload){
		throw new TypeError('Item is not a Django payload.');
	}

	if(!data.type){
		throw new TypeError('Item is missing a payload type.');
	}
};

// Global listener than handles machinery of inspecting incoming Ajax data
// for DjangoMessages (which we generate on the Python side).
// Helps route these responses to interested parties on the Javascript (client) side
// by trigger global events. I.E. "Messages.django". 
var DjangoListener = window.DjangoAjax.DjangoListener = DjangoAjax.makeClass();

DjangoListener.prototype.startListening = function(){
	var self = this;

	jQuery(document).bind('ajaxComplete',function(evt,request){
		try {
			var data = JSON.parse(request.responseText);
		} catch (e) {
			return;
		}

		// Only trigger on AjaxItems that have the correct type.
		if(!self.isValid(data)){
			return false;
		}

		// If we've made it here we have a DjangoResponse.
		// Instantiate and trigger it.
		response = new DjangoResponse(data);
		console.log('DjangoResponse obtained',response);
		response.trigger();
	});
};

DjangoListener.prototype.isValid = function(data){
	if(data.type != 'Response') {
		return false;
	} else {
		return true;
	}
};

// Handles the nested payload of the Messages.django payload.
// Which contains individual message items. Complicated to explain, probably best de-nested.
// Listen to the zen of python next time.
var DjangoMessage = window.DjangoAjax.DjangoMessage =  DjangoAjax.makeClass();

DjangoMessage.prototype.init = function(data){
	this.$notifications = jQuery(data);
};

// Shares a similar interface to top level AjaxEvents.
// IsValid determines if this object is capable of handling the message
// we're trying to give it.
DjangoMessage.prototype.isValid = function(message){
	return message.type = 'MessageItem';
};

/**
 * @param selector An optional selector to filter elements with.
 * @param invert Whether to invert the selector.
 */
DjangoMessage.prototype.notifications = function(selector, invert){
	if(!selector)
	{
		return this.$notifications;
	}
	else
	{
		if(invert)
		{
			return this.$notifications.not(selector);
		}
		else
		{
			return this.$notifications.filter(selector);
		}
	}
};

// Validation / integration with uni-form

var DjangoValidator = window.DjangoAjax.DjangoValidator = DjangoAjax.makeClass();

function uniform_callback(data, form) {
    var field_divs = $(form).find(".ctrlHolder").filter(".error");
    field_divs.removeClass("error");
    field_divs.find(".errorField").remove();

    $.each(data.errors, function(key, val) {
        var field_div = $(form).find(".ctrlHolder").filter("#div_" + key);
        field_div.addClass("error");
        field_div.prepend('<p id="error_1_' + key + '" class="errorField">'
            + val + '</p>');
    });
}

DjangoValidator.prototype.init = function($form, data, settings){
	this.settings = jQuery.extend({
        type: 'uniform',
        callback: false,
        fields: false,
        dom: jQuery($form),
        event: 'submit',
        submitHandler: null
    }, settings);

	this.data = data;
	// Track open listeners
	this.listenerCount = 0;
};

// Because there might be multiple simulateous forms undergoing validation
DjangoValidator.prototype.startListening = function(){
	var self = this

	jQuery(document).one('Validation.django',function(evt, data){
		self.validate(data.payload);
	});
};

DjangoValidator.prototype.clearErrors = function(){
	if(settings.type == 'uniform'){

	}
};

DjangoValidator.prototype.validate = function(){
	var data = this.data;
	var settings = this.settings;

	this.settings.dom.each(function(){
		var form = jQuery(this);
		status = data.valid;
	    if (!status)    {
	        if (settings.callback)  {
	            settings.callback(data, form);
	        }
	        else if(settings.type == 'uniform') {
	        		uniform_callback(data,form);
	        }
	        else    {
	            var get_form_error_position = function(key) {
	                key = key || '__all__';
	                if (key == '__all__') {
	                    var filter = ':first';
	                } else {
	                    var filter = ':first[id^=id_' + key.replace('__all__', '') + ']';
	                }
	                return inputs(form).filter(filter).parent();
	            };
	            if (settings.type == 'p')    {
	                form.find('ul.errorlist').remove();
	                $.each(data.errors, function(key, val)  {
	                    if (key.indexOf('__all__') >= 0)   {
	                        var error = get_form_error_position(key);
	                        if (error.prev().is('ul.errorlist')) {
	                            error.prev().before('<ul class="errorlist"><li>' + val + '</li></ul>');
	                        }
	                        else    {
	                            error.before('<ul class="errorlist"><li>' + val + '</li></ul>');
	                        }
	                    }
	                    else    {
	                        $('#' + key).parent().before('<ul class="errorlist"><li>' + val + '</li></ul>');
	                    }
	                });
	            }
	            if (settings.type == 'table')   {
	                inputs(form).prev('ul.errorlist').remove();
	                form.find('tr:has(ul.errorlist)').remove();
	                $.each(data.errors, function(key, val)  {
	                    if (key.indexOf('__all__') >= 0)   {
	                        get_form_error_position(key).parent().before('<tr><td colspan="2"><ul class="errorlist"><li>' + val + '.</li></ul></td></tr>');
	                    }
	                    else    {
	                        $('#' + key).before('<ul class="errorlist"><li>' + val + '</li></ul>');
	                    }
	                });
	            }
	            if (settings.type == 'ul')  {
	                inputs(form).prev().prev('ul.errorlist').remove();
	                form.find('li:has(ul.errorlist)').remove();
	                $.each(data.errors, function(key, val)  {
	                    if (key.indexOf('__all__') >= 0)   {
	                        get_form_error_position(key).before('<li><ul class="errorlist"><li>' + val + '</li></ul></li>');
	                    }
	                    else    {
	                        $('#' + key).prev().before('<ul class="errorlist"><li>' + val + '</li></ul>');
	                    }
	                });
	            }
	        }
	    }
    });

};

// Initialize a global DjangoListener instance

jQuery(document).ready(function(){
	var djangoListener = new DjangoListener();
	djangoListener.startListening();
	window.DjangoAjax.instances.djangoListener = djangoListener;
});

})(jQuery);