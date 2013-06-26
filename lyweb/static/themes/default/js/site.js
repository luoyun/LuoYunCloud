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

function binding_site_language_select() {
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
