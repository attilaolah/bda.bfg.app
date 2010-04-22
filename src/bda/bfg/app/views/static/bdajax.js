jQuery(document).ready(function() {
	jQuery('#ajax-spinner')
        .hide()
        .ajaxStart(function() {
            jQuery(this).show();
        })
        .ajaxStop(function() {
            jQuery(this).hide();
        })
    ;
	jQuery(document).bdajax();
});

// bind bdajax behaviour to context
jQuery.fn.bdajax = function() {
	jQuery('[ajax\\:bind]', this).each(function() {
		var events = jQuery(this).attr('[ajax\\:bind]');
		jQuery('[ajax\\:event]', this).bind(events, bdajax.event);
		jQuery('[ajax\\:call]', this).bind(events, bdajax.call);
		jQuery('[ajax\\:action]', this).bind(events, bdajax.action);
		jQuery('[ajax\\:actions]', this).bind(events, bdajax.actions);
	});
}

bdajax = {
	
    // Display System message as overlay.
    // @param message: Message to display as String or DOM element.
    message: function(message) {
        jQuery('#ajax-message').overlay({
            expose: {
                color: '#fff',
                loadSpeed: 200
            },
            onBeforeLoad: function() {
                var overlay = this.getOverlay();
                jQuery('.message', overlay).html(message);
            },
            closeOnClick: false,
            api: true
        }).load();
    },
    
    // Display Error message as overlay.
    // @param message: Message to display as String or DOM element.
    error: function(message) {
        jQuery("#ajax-message .message")
            .removeClass('error warning info')
            .addClass('error')
        ;
        bdajax.message(message);
    },
    
    // Display Info message as overlay.
    // @param message: Message to display as String or DOM element.
    info: function(message) {
        jQuery("#ajax-message .message")
            .removeClass('error warning info')
            .addClass('info')
        ;
        bdajax.message(message);
    },
    
    // Display Warning message as overlay.
    // @param message: Message to display as String or DOM element.
    warning: function(message) {
        jQuery("#ajax-message .message")
            .removeClass('error warning info')
            .addClass('warning')
        ;
        bdajax.message(message);
    },
	
	// Strip query from URL if existent and return.
	// @param url: Request URL as string.
	parseurl: function(url) {
        var idx = url.indexOf('?');
        if (idx != -1) {
            url = url.substring(0, idx);
        }
		return url;
	},
	
    // Parse query string from URL if existent and return query parameters as
    // object.
    // @param url: Request URL as string.
	parsequery: function(url) {
		var params = {};
		var idx = url.indexOf('?');
        if (idx != -1) {
            var parameters = url.slice(idx + 1).split('&');
            for (var i = 0;  i < parameters.length; i++) {
                var param = parameters[i].split('=');
                params[param[0]] = param[1];
            }
        }
		return params;
	},
	
    // Error messages.
    ajaxerrors: {
        timeout: 'The request has timed out. Pleasae try again.',
        error: 'An error occoured while processing the request. Aborting.',
        parsererror: 'The Response could not be parsed. Aborting.',
        unknown: 'An unknown error occoured while request. Aborting.'
    },
    
    // Get error message.
    // @param status: ``jQuery.ajax`` error callback status
    ajaxerror: function(status) {
        if (status == 'notmodified') { return; }
        if (status == null) { status = 'unknown' }
        return bdajax.ajaxerrors[status];
    },
	
	// Perform an ajax request.
	// @param config: object containing request configuration.
	//     Configuration fields:
	//         success: Callback if request is successful.
	//         url: Request url as string.
	//         params: Query parameters for request as Object (optional). 
	//         type: ``xml``, ``json``, ``script``, or ``html`` (optional).
	//         error: Callback if request fails (optional).
	request: function(config) {
		if (config.url.indexOf('?') != -1) {
			var addparams = config.params;
			config.params = bdajax.parsequery(url);
			url = bdajax.parseurl(url);
			for (var key in addparams) {
                config.params[key] = addparams[key];
            }
		} else {
			if (!config.params) { config.params = {}; }
		}
		if (!config.type) { config.type = 'html'; }
	    if (!config.error) {
	        config.error = function(request, status) {
				var err = bdajax.ajaxerror(status);
				if (err) { bdajax.error(err); }
	        }
	    }
	    jQuery.ajax({
	        url: config.url,
	        dataType: config.type,
	        data: config.params,
	        success: config.success,
	        error: config.error
	    });
	},
	
    // Callback handler for event triggering.
    event: function(event) {
        var attr = jQuery(this).attr('[ajax\\:event]');
        var defs = attr.split(' ');
        for (def in defs) {
            def = def.split(':');
            jQuery(def[1]).trigger(jQuery.Event(def[0]));
        }
    },
	
    // Callback handler for javascript function calls.
    call: function(event) {
        var attr = jQuery(this).attr('[ajax\\:call]');
        var defs = attr.split(' ');
        for (def in defs) {
            def = def.split(':');
			func = eval(def[0]);
			func(jQuery(def[1]));
        }
    },
    
    // Callback handler for an action binding.
    action: function(event) {
        bdajax._action({
            name: jQuery(this).attr('ajax:action'),
            element: this,
            event: event
        });
    },
    
    // Callback handler for an actions binding.
    actions: function(event) {
        bdajax._actions({
            name: jQuery(this).attr('ajax:actions'),
            element: this,
            event: event
        });
    },
	
	// Perform JSON request to server and alter element(s).
	// This function expects as response an array containing a name
	// mapping to class and/or id attributes of the dom element to alter
	// and the html payload which is used as data replacement.
	// @param config: object containing action configuration.
    //     Configuration fields:
    //         name: Action name.
    //         element: Dom element the event is bound to. 
    //         event: thrown event.
	//         mode: action mode
	//         selector: result selector
	_action: function(config) {
		var target = jQuery(config.element).attr('ajax:target');
        var url = bdajax.parseurl(target);
        var params = bdajax.parsequery(target);
        params['bdajax.action'] = config.name;
		params['bdajax.mode'] = config.mode;
		params['bdajax.selector'] = config.selector;
		var error = function(req, status, exception) {
            bdajax.error(exception);
        };
		bdajax.request({
            url: bdajax.parseurl(config.url) + '/' + config.view,
            type: 'json',
            params: config.params,
            success: function(data) {
				var mode = data.mode;
				var selector = data.selector;
				if (mode == 'replace') {
					jQuery(selector).replaceWith(data.payload);
					jQuery(selector).bdajax();
				} else if (mode == 'inner') {
					jQuery(selector).html(data.payload);
					jQuery(selector).each(function() {
						jQuery(this).bdajax();
					});
				}
            },
            error: error
        });
		config.event.preventDefault();
	},
	
	// Perform JSON request to server and perform specified action(s).
	// This function expects as response an array containing the action name(s)
    // mapping to given actions name.
	// @param config: object containing action configuration.
    //     Configuration fields:
    //         name: Actions name.
    //         element: Dom element the event is bound to. 
    //         event: thrown event.
	_actions: function(config) {
        var target = jQuery(config.element).attr('ajax:target');
        var url = bdajax.parseurl(target);
        var params = bdajax.parsequery(target);
        params.name = config.name;
        var error = function(req, status, exception) {
            bdajax.error(exception);
        };
        bdajax.request({
            url: url + '/ajaxactions',
            type: 'json',
            params: params,
            success: function(data) {
                if (!data) {
                    bdajax.error('Server response empty.');
                    return;
                }
                for (var i = 0; i < data.length; i++) {
                    params.name = data[i];
					bdajax.request({
			            url: bdajax.parseurl(url) + '/ajaxaction',
			            type: 'json',
			            params: params,
			            success: function(data) {
			                var name = data[0];
			                jQuery('#' + name).replaceWith(data[1]);
			                jQuery('.' + name).replaceWith(data[1]);
							jQuery('#' + name + ' a[ajax\\:action]').action();
                            jQuery('#' + name + ' a[ajax\\:actions]').actions();
							jQuery('.' + name + ' a[ajax\\:action]').action();
                            jQuery('.' + name + ' a[ajax\\:actions]').actions();
			            },
			            error: error
			        });
                }
            },
            error: error
        });
        config.event.preventDefault();
    }
};