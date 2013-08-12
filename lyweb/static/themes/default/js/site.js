/*
    json2.js
    2012-10-08

    Public Domain.

    NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.

    See http://www.JSON.org/js.html


    This code should be minified before deployment.
    See http://javascript.crockford.com/jsmin.html

    USE YOUR OWN COPY. IT IS EXTREMELY UNWISE TO LOAD CODE FROM SERVERS YOU DO
    NOT CONTROL.


    This file creates a global JSON object containing two methods: stringify
    and parse.

        JSON.stringify(value, replacer, space)
            value       any JavaScript value, usually an object or array.

            replacer    an optional parameter that determines how object
                        values are stringified for objects. It can be a
                        function or an array of strings.

            space       an optional parameter that specifies the indentation
                        of nested structures. If it is omitted, the text will
                        be packed without extra whitespace. If it is a number,
                        it will specify the number of spaces to indent at each
                        level. If it is a string (such as '\t' or '&nbsp;'),
                        it contains the characters used to indent at each level.

            This method produces a JSON text from a JavaScript value.

            When an object value is found, if the object contains a toJSON
            method, its toJSON method will be called and the result will be
            stringified. A toJSON method does not serialize: it returns the
            value represented by the name/value pair that should be serialized,
            or undefined if nothing should be serialized. The toJSON method
            will be passed the key associated with the value, and this will be
            bound to the value

            For example, this would serialize Dates as ISO strings.

                Date.prototype.toJSON = function (key) {
                    function f(n) {
                        // Format integers to have at least two digits.
                        return n < 10 ? '0' + n : n;
                    }

                    return this.getUTCFullYear()   + '-' +
                         f(this.getUTCMonth() + 1) + '-' +
                         f(this.getUTCDate())      + 'T' +
                         f(this.getUTCHours())     + ':' +
                         f(this.getUTCMinutes())   + ':' +
                         f(this.getUTCSeconds())   + 'Z';
                };

            You can provide an optional replacer method. It will be passed the
            key and value of each member, with this bound to the containing
            object. The value that is returned from your method will be
            serialized. If your method returns undefined, then the member will
            be excluded from the serialization.

            If the replacer parameter is an array of strings, then it will be
            used to select the members to be serialized. It filters the results
            such that only members with keys listed in the replacer array are
            stringified.

            Values that do not have JSON representations, such as undefined or
            functions, will not be serialized. Such values in objects will be
            dropped; in arrays they will be replaced with null. You can use
            a replacer function to replace those with JSON values.
            JSON.stringify(undefined) returns undefined.

            The optional space parameter produces a stringification of the
            value that is filled with line breaks and indentation to make it
            easier to read.

            If the space parameter is a non-empty string, then that string will
            be used for indentation. If the space parameter is a number, then
            the indentation will be that many spaces.

            Example:

            text = JSON.stringify(['e', {pluribus: 'unum'}]);
            // text is '["e",{"pluribus":"unum"}]'


            text = JSON.stringify(['e', {pluribus: 'unum'}], null, '\t');
            // text is '[\n\t"e",\n\t{\n\t\t"pluribus": "unum"\n\t}\n]'

            text = JSON.stringify([new Date()], function (key, value) {
                return this[key] instanceof Date ?
                    'Date(' + this[key] + ')' : value;
            });
            // text is '["Date(---current time---)"]'


        JSON.parse(text, reviver)
            This method parses a JSON text to produce an object or array.
            It can throw a SyntaxError exception.

            The optional reviver parameter is a function that can filter and
            transform the results. It receives each of the keys and values,
            and its return value is used instead of the original value.
            If it returns what it received, then the structure is not modified.
            If it returns undefined then the member is deleted.

            Example:

            // Parse the text. Values that look like ISO date strings will
            // be converted to Date objects.

            myData = JSON.parse(text, function (key, value) {
                var a;
                if (typeof value === 'string') {
                    a =
/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}(?:\.\d*)?)Z$/.exec(value);
                    if (a) {
                        return new Date(Date.UTC(+a[1], +a[2] - 1, +a[3], +a[4],
                            +a[5], +a[6]));
                    }
                }
                return value;
            });

            myData = JSON.parse('["Date(09/09/2001)"]', function (key, value) {
                var d;
                if (typeof value === 'string' &&
                        value.slice(0, 5) === 'Date(' &&
                        value.slice(-1) === ')') {
                    d = new Date(value.slice(5, -1));
                    if (d) {
                        return d;
                    }
                }
                return value;
            });


    This is a reference implementation. You are free to copy, modify, or
    redistribute.
*/

/*jslint evil: true, regexp: true */

/*members "", "\b", "\t", "\n", "\f", "\r", "\"", JSON, "\\", apply,
    call, charCodeAt, getUTCDate, getUTCFullYear, getUTCHours,
    getUTCMinutes, getUTCMonth, getUTCSeconds, hasOwnProperty, join,
    lastIndex, length, parse, prototype, push, replace, slice, stringify,
    test, toJSON, toString, valueOf
*/


// Create a JSON object only if one does not already exist. We create the
// methods in a closure to avoid creating global variables.

if (typeof JSON !== 'object') {
    JSON = {};
}

(function () {
    'use strict';

    function f(n) {
        // Format integers to have at least two digits.
        return n < 10 ? '0' + n : n;
    }

    if (typeof Date.prototype.toJSON !== 'function') {

        Date.prototype.toJSON = function (key) {

            return isFinite(this.valueOf())
                ? this.getUTCFullYear()     + '-' +
                    f(this.getUTCMonth() + 1) + '-' +
                    f(this.getUTCDate())      + 'T' +
                    f(this.getUTCHours())     + ':' +
                    f(this.getUTCMinutes())   + ':' +
                    f(this.getUTCSeconds())   + 'Z'
                : null;
        };

        String.prototype.toJSON      =
            Number.prototype.toJSON  =
            Boolean.prototype.toJSON = function (key) {
                return this.valueOf();
            };
    }

    var cx = /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        escapable = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        gap,
        indent,
        meta = {    // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        },
        rep;


    function quote(string) {

// If the string contains no control characters, no quote characters, and no
// backslash characters, then we can safely slap some quotes around it.
// Otherwise we must also replace the offending characters with safe escape
// sequences.

        escapable.lastIndex = 0;
        return escapable.test(string) ? '"' + string.replace(escapable, function (a) {
            var c = meta[a];
            return typeof c === 'string'
                ? c
                : '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
        }) + '"' : '"' + string + '"';
    }


    function str(key, holder) {

// Produce a string from holder[key].

        var i,          // The loop counter.
            k,          // The member key.
            v,          // The member value.
            length,
            mind = gap,
            partial,
            value = holder[key];

// If the value has a toJSON method, call it to obtain a replacement value.

        if (value && typeof value === 'object' &&
                typeof value.toJSON === 'function') {
            value = value.toJSON(key);
        }

// If we were called with a replacer function, then call the replacer to
// obtain a replacement value.

        if (typeof rep === 'function') {
            value = rep.call(holder, key, value);
        }

// What happens next depends on the value's type.

        switch (typeof value) {
        case 'string':
            return quote(value);

        case 'number':

// JSON numbers must be finite. Encode non-finite numbers as null.

            return isFinite(value) ? String(value) : 'null';

        case 'boolean':
        case 'null':

// If the value is a boolean or null, convert it to a string. Note:
// typeof null does not produce 'null'. The case is included here in
// the remote chance that this gets fixed someday.

            return String(value);

// If the type is 'object', we might be dealing with an object or an array or
// null.

        case 'object':

// Due to a specification blunder in ECMAScript, typeof null is 'object',
// so watch out for that case.

            if (!value) {
                return 'null';
            }

// Make an array to hold the partial results of stringifying this object value.

            gap += indent;
            partial = [];

// Is the value an array?

            if (Object.prototype.toString.apply(value) === '[object Array]') {

// The value is an array. Stringify every element. Use null as a placeholder
// for non-JSON values.

                length = value.length;
                for (i = 0; i < length; i += 1) {
                    partial[i] = str(i, value) || 'null';
                }

// Join all of the elements together, separated with commas, and wrap them in
// brackets.

                v = partial.length === 0
                    ? '[]'
                    : gap
                    ? '[\n' + gap + partial.join(',\n' + gap) + '\n' + mind + ']'
                    : '[' + partial.join(',') + ']';
                gap = mind;
                return v;
            }

// If the replacer is an array, use it to select the members to be stringified.

            if (rep && typeof rep === 'object') {
                length = rep.length;
                for (i = 0; i < length; i += 1) {
                    if (typeof rep[i] === 'string') {
                        k = rep[i];
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            } else {

// Otherwise, iterate through all of the keys in the object.

                for (k in value) {
                    if (Object.prototype.hasOwnProperty.call(value, k)) {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            }

// Join all of the member texts together, separated with commas,
// and wrap them in braces.

            v = partial.length === 0
                ? '{}'
                : gap
                ? '{\n' + gap + partial.join(',\n' + gap) + '\n' + mind + '}'
                : '{' + partial.join(',') + '}';
            gap = mind;
            return v;
        }
    }

// If the JSON object does not yet have a stringify method, give it one.

    if (typeof JSON.stringify !== 'function') {
        JSON.stringify = function (value, replacer, space) {

// The stringify method takes a value and an optional replacer, and an optional
// space parameter, and returns a JSON text. The replacer can be a function
// that can replace values, or an array of strings that will select the keys.
// A default replacer method can be provided. Use of the space parameter can
// produce text that is more easily readable.

            var i;
            gap = '';
            indent = '';

// If the space parameter is a number, make an indent string containing that
// many spaces.

            if (typeof space === 'number') {
                for (i = 0; i < space; i += 1) {
                    indent += ' ';
                }

// If the space parameter is a string, it will be used as the indent string.

            } else if (typeof space === 'string') {
                indent = space;
            }

// If there is a replacer, it must be a function or an array.
// Otherwise, throw an error.

            rep = replacer;
            if (replacer && typeof replacer !== 'function' &&
                    (typeof replacer !== 'object' ||
                    typeof replacer.length !== 'number')) {
                throw new Error('JSON.stringify');
            }

// Make a fake root object containing our value under the key of ''.
// Return the result of stringifying the value.

            return str('', {'': value});
        };
    }


// If the JSON object does not yet have a parse method, give it one.

    if (typeof JSON.parse !== 'function') {
        JSON.parse = function (text, reviver) {

// The parse method takes a text and an optional reviver function, and returns
// a JavaScript value if the text is a valid JSON text.

            var j;

            function walk(holder, key) {

// The walk method is used to recursively walk the resulting structure so
// that modifications can be made.

                var k, v, value = holder[key];
                if (value && typeof value === 'object') {
                    for (k in value) {
                        if (Object.prototype.hasOwnProperty.call(value, k)) {
                            v = walk(value, k);
                            if (v !== undefined) {
                                value[k] = v;
                            } else {
                                delete value[k];
                            }
                        }
                    }
                }
                return reviver.call(holder, key, value);
            }


// Parsing happens in four stages. In the first stage, we replace certain
// Unicode characters with escape sequences. JavaScript handles many characters
// incorrectly, either silently deleting them, or treating them as line endings.

            text = String(text);
            cx.lastIndex = 0;
            if (cx.test(text)) {
                text = text.replace(cx, function (a) {
                    return '\\u' +
                        ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
                });
            }

// In the second stage, we run the text against regular expressions that look
// for non-JSON patterns. We are especially concerned with '()' and 'new'
// because they can cause invocation, and '=' because it can cause mutation.
// But just to be safe, we want to reject all unexpected forms.

// We split the second stage into 4 regexp operations in order to work around
// crippling inefficiencies in IE's and Safari's regexp engines. First we
// replace the JSON backslash pairs with '@' (a non-JSON character). Second, we
// replace all simple value tokens with ']' characters. Third, we delete all
// open brackets that follow a colon or comma or that begin the text. Finally,
// we look to see that the remaining characters are only whitespace or ']' or
// ',' or ':' or '{' or '}'. If that is so, then the text is safe for eval.

            if (/^[\],:{}\s]*$/
                    .test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@')
                        .replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']')
                        .replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {

// In the third stage we use the eval function to compile the text into a
// JavaScript structure. The '{' operator is subject to a syntactic ambiguity
// in JavaScript: it can begin a block or an object literal. We wrap the text
// in parens to eliminate the ambiguity.

                j = eval('(' + text + ')');

// In the optional fourth stage, we recursively walk the new structure, passing
// each name/value pair to a reviver function for possible transformation.

                return typeof reviver === 'function'
                    ? walk({'': j}, '')
                    : j;
            }

// If the text is not JSON parseable, then a SyntaxError is thrown.

            throw new SyntaxError('JSON.parse');
        };
    }
}());



/*

  scrollUp v1.1.0
  Author: Mark Goodyear - http://www.markgoodyear.com
  Git: https://github.com/markgoodyear/scrollup

  Copyright 2013 Mark Goodyear
  Licensed under the MIT license
  http://www.opensource.org/licenses/mit-license.php

  Twitter: @markgdyr

*/

;(function($) {

	$.scrollUp = function (options) {

		// Defaults
		var defaults = {
			scrollName: 'scrollUp', // Element ID
			topDistance: 300, // Distance from top before showing element (px)
			topSpeed: 300, // Speed back to top (ms)
			animation: 'fade', // Fade, slide, none
			animationInSpeed: 200, // Animation in speed (ms)
			animationOutSpeed: 200, // Animation out speed (ms)
			scrollText: 'Scroll to top', // Text for element
			scrollImg: false, // Set true to use image
			activeOverlay: false // Set CSS color to display scrollUp active point, e.g '#00FFFF'
		};

		var o = $.extend({}, defaults, options),
		scrollId = '#' + o.scrollName;

		// Create element
		$('<a/>', {
			id: o.scrollName,
			href: '#top',
			title: o.scrollText
		}).appendTo('body');

		// If not using an image display text
		if (!o.scrollImg) {
			$(scrollId).text(o.scrollText);
		}

		// Minium CSS to make the magic happen
		$(scrollId).css({'display':'none','position': 'fixed','z-index': '2147483647'});

		// Active point overlay
		if (o.activeOverlay) {
			$("body").append("<div id='"+ o.scrollName +"-active'></div>");
			$(scrollId+"-active").css({ 'position': 'absolute', 'top': o.topDistance+'px', 'width': '100%', 'border-top': '1px dotted '+o.activeOverlay, 'z-index': '2147483647' });
		}

		// Scroll function
		$(window).scroll(function(){	
			switch (o.animation) {
			case "fade":
				$( ($(window).scrollTop() > o.topDistance) ? $(scrollId).fadeIn(o.animationInSpeed) : $(scrollId).fadeOut(o.animationOutSpeed) );
				break;
			case "slide":
				$( ($(window).scrollTop() > o.topDistance) ? $(scrollId).slideDown(o.animationInSpeed) : $(scrollId).slideUp(o.animationOutSpeed) );
				break;
			default:
				$( ($(window).scrollTop() > o.topDistance) ? $(scrollId).show(0) : $(scrollId).hide(0) );
			}
		});

		// To the top
		$(scrollId).click( function(event) {
			$('html, body').animate({scrollTop:0}, o.topSpeed);
			event.preventDefault();
		});

	};
})(jQuery);


$(document).ready(function(){
	
	//Remove outline from links
	$("a").click(function(){
		$(this).blur();
	});

});

// Ajax for xsrf , csrf
$(document).ajaxSend(function(event, xhr, settings) {  
    function getCookie(name) {  
        var cookieValue = null;  
        if (document.cookie && document.cookie != '') {  
            var cookies = document.cookie.split(';');  
            for (var i = 0; i < cookies.length; i++) {  
                var cookie = jQuery.trim(cookies[i]);  
                // Does this cookie string begin with the name we want?  
                if (cookie.substring(0, name.length + 1) == (name + '=')) {  
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));  
                    break;  
                }  
            }  
        }

		if (!cookieValue)
			cookieValue = $("#xsrf-cookie").text();

        return cookieValue;  
    }  
    function sameOrigin(url) {  
        // url could be relative or scheme relative or absolute  
        var host = document.location.host; // host + port  
        var protocol = document.location.protocol;  
        var sr_origin = '//' + host;  
        var origin = protocol + sr_origin;  
        // Allow absolute or scheme relative URLs to same origin  
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||  
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||  
            // or any other URL that isn't scheme relative or absolute i.e relative.  
            !(/^(\/\/|http:|https:).*/.test(url));  
    }  
    function safeMethod(method) {  
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));  
    }  
	
    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {  
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken')); 
    }  
});


function selected_reload( selector, url_template ) {
	$( selector ).change( function() {
		var select = $(this).children('option:selected').val();
		var url = url_template.replace('REPLACEOBJ', select)
		if ( url != url_template )
			location.href = url;
		else
			alert( 'failed' )
	});
}


function menu_entry_active ( link ) {
	$(".site-menu li[class=active]").removeClass("active");
	$('.site-menu a[href="' + link +'"]').parent().addClass("active");
}

function just_active_myself ( selector ) {
	$(selector).siblings().removeClass("active");
	$(selector).addClass("active");
}

function binding_site_language_select( current ) {
	$('.site-language-select').val( current );
    $('.site-language-select').change( function() {
        var select = $(this).children('option:selected').val();
        url = '/setlocale?language=' + select;
        url += '&next=' + location.pathname + location.search;
        location.href = url;
    });
}


function _check_toggle( obj ) {
	if ( obj.hasClass('icon-check') ) {
		obj.removeClass('icon-check');
		obj.addClass('icon-check-empty');
	} else {
		obj.removeClass('icon-check-empty');
		obj.addClass('icon-check');
	}
}
function _checked( obj ) {
	obj.removeClass('icon-check-empty');
	obj.addClass('icon-check');
	obj.parents('.y-check-line').addClass('success');
}
function _unchecked( obj ) {
	obj.removeClass('icon-check');
	obj.addClass('icon-check-empty');
	obj.parents('.y-check-line').removeClass('success');
}
function _after_check_changed( area ) {
	a = area.find('.y-check').length;
	b = area.find('.y-check.icon-check').length;

	if ( a == b )
		_checked( $all_check_all );
	else
		_unchecked( $all_check_all );

	var $action_one = area.find('.y-action-one');
	var $action_nonzero = area.find('.y-action-nonzero');

	if ( b == 0 ) {
		$action_one.addClass('disabled');
		$action_nonzero.addClass('disabled');
	} else if ( b == 1 ) {
		$action_one.removeClass('disabled');
		$action_nonzero.removeClass('disabled');
	} else {
		$action_one.addClass('disabled');
		$action_nonzero.removeClass('disabled');
	}
}
function y_checkarea_binding() {

	$obj = $('.y-checkarea');

	$area          = $('.y-checkarea');
	$all_checkline = $area.find('.y-check-line')
	$all_check     = $area.find('.y-check');
	$all_check_all = $area.find('.y-check-all');

	// outside click
	$('body').click( function(event) {
		_unchecked( $all_check );
		_unchecked( $all_check_all );
		$all_checkline.removeClass('success');

		_after_check_changed( $area );
	});


	$area.find('a').click( function(event) {
		event.stopPropagation();
	});


	$all_checkline.click( function(event) {
		event.stopPropagation();

		var $this = $(this);

		if ( event.ctrlKey ) {
			$this.toggleClass('success');
			_check_toggle( $this.find('.y-check') );
		} else {
			$all_checkline.removeClass('success');
			$this.addClass('success');

			_unchecked( $all_check );
			_checked( $this.find('.y-check') );
		}

		_after_check_changed( $area );
	});


	$all_check.click( function(event) {
		event.stopPropagation();

		var $this = $(this);

		$this.parents('.y-check-line').toggleClass('success');
		_check_toggle( $this );

		_after_check_changed( $area );
	});


	$all_check_all.click( function(event) {
		event.stopPropagation();

		var $this = $(this);

		if ( $this.hasClass('icon-check') ) {
			_unchecked( $all_check );
			_unchecked( $all_check_all );
		} else {
			_checked( $all_check );
			_checked( $all_check_all );
		};

		_after_check_changed( $area );
	});


	$area.find('.y-select-all').click( function(event) {
		event.preventDefault();

		_checked( $all_check );
		_checked( $all_check_all );
		$all_checkline.addClass('success');

		_after_check_changed( $area );
	});


	$area.find('.y-unselect-all').click( function(event) {
		event.preventDefault();

		_unchecked( $all_check );
		_unchecked( $all_check_all );
		$all_checkline.removeClass('success');

		_after_check_changed( $area );
	});


	$area.find('.y-select-reverse').click( function(event) {
		event.preventDefault();

		$all_check.each( function() {
			var $this = $(this);

			_check_toggle( $this );
			$this.parents('.y-check-line').toggleClass('success');
		});

		_after_check_changed( $area );
	});

}



function draw_used (data) {

    used_percentage = data.used * 100.0 / data.total;
    used_percentage = Math.round(used_percentage * Math.pow(10, 2)) / Math.pow(10, 2);

	if (data.pie_size)
		pie_size = data.pie_size;
	else
		pie_size = 200;
    
	$(data.container).highcharts({
	    chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
        },
        title: {
            text: data.title,
			floating: true,
        },
        subtitle: {
            text: data.subtitle,
			floating: true,
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
				size: pie_size,
                dataLabels: {
                    enabled: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    connectorWidth: 0,
                    distance: 6, // -50 is inside
                    formatter: function() {
                        return '<b>'+ this.point.name +'</b>';//<br/>'+ this.percentage +' %';
                    }
                }
            }
        },
        series: [{
            type: 'pie',
            name: data.series_name,
            data: [
				{
					name: data.used_text,
					color: '#FEC157',
					y: used_percentage,
                    sliced: true,
                    selected: true
				},
                [data.unused_text, 100.0 - used_percentage]
            ]
        }],
        credits: {
            text: 'LuoYun.CO',
            href: 'http://www.luoyun.co'
        }
    });
}


function y_input_search( input_selector, url_template, update_obj ) {
    $(input_selector).keyup(function(){

		txt=$(this).val();

		var url = url_template.replace('REPLACEOBJ', txt);

		clearTimeout($(this).data('timeId'));

		var timeoutId = setTimeout(function() {
			$.get(url,function(data){
				$(update_obj).html(data);
			}); }, 300);

		$(this).data('timeId', timeoutId);
    });
}


function load_kindeditor( data ) {

    KindEditor.ready(function(K) {
        window.editor = K.create( data.selector, {
            uploadJson : '/attachment/upload_kindeditor',
            fileManagerJson : '/attachment/upload_kindeditor', //TODO
            allowFileManager : true,

            extraFileUploadParams : {
				//_xsrf: getCookie("_xsrf"),
                _xsrf: $("#xsrf-cookie").text(),
                way: 'local'
            },

			items: [
				'source', '|', 'undo', 'redo', '|', 'preview', 'code',
				'|', 'justifyleft', 'justifycenter', 'justifyright',
				'justifyfull', 'insertorderedlist', 'insertunorderedlist', 'indent', 'outdent', 'subscript',
				'superscript', 'selectall', '|', 'fullscreen', '/',
				'formatblock', 'forecolor', 'hilitecolor', 'bold',
				'italic', 'underline', 'strikethrough', '|', 'image',
				'media', 'insertfile', 'table', 'emoticons', 'baidumap',
				'anchor', 'link', 'unlink', '|', 'about'
			],
        });
    });

}


