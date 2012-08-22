// A delay example when mounse hover
(function($){
    $.fn.hoverDelay = function(options){
        var defaults = {
            hoverDuring: 200,
            outDuring: 200,
            hoverEvent: function(){
                $.noop();
            },
            outEvent: function(){
                $.noop();
            }
        };
        var sets = $.extend(defaults,options || {});
        var hoverTimer, outTimer;
        return $(this).each(function(){
            $(this).hover(function(){
                clearTimeout(outTimer);
                hoverTimer = setTimeout(sets.hoverEvent, sets.hoverDuring);
            },function(){
                clearTimeout(hoverTimer);
                outTimer = setTimeout(sets.outEvent, sets.outDuring);
            });
        });
    }
})(jQuery);


function InstanceDynamicStatus () {

    var jid = $('#job-id').html();
    if (! jid)
    {
        $('#job-status-desc').html('No id found');
        window.setTimeout(InstanceDynamicStatus, 1000);
        return
    } else if ( jid == -1 ) {
	return
    }


    var previous = $('#job-status-value').html();

    var URL = '/job/' + jid + '/status?previous=' + previous;

    $.ajax({

        url: URL,
        type: "GET",

        success: function (data) {
            var status = $('#job-status-value').text();

            if (data.job_status != status) {
                $('#job-id').html(jid);
                $('#job-status-value').html(data.job_status);
                $('#job-status-desc').html(data.desc);
                if (data.status == 1) {
                    window.setTimeout(
                        InstanceDynamicStatus, 500);
                } else {
                    // TODO: done
                    if (data.job_status == 301)
                        location.reload(true);
		    else if (
			(data.job_status >= 311 &&
			 data.job_status <= 399) ||
			    data.job_status == 600 ||
			    (data.job_status >=700 &&
			     data.job_status <=799)
		    ) {
			// 300-399, 600, 700-799
			ly_url_set_parameter('job_result', data.desc);
		    }
                }
            }
        },

        error: function (data) {
            //alert(data + ', try again !');
            window.setTimeout(InstanceDynamicStatus, 5000);
        }

    });

}


function InstanceControl() {

    $('#i-action .run a, #i-action .stop a, #i-action .query a').click( function () {

        var $obj = $(this);

	$('#job-result').html('');

        URL = $obj.attr('href');

        $.ajax({
            url: URL + '?ajax=1',
            type: 'GET',
            success: function (data) {
                if (! data.jid) {
                    $('#job-status-desc').html( data.desc );
                    return
                }

		// set link is unaviable
                $obj.attr('href', "javascript:void(0);");

		// change img on clicked status
		var imgp = $obj.children('img').attr('src');
		imgp = imgp.replace(/(\w+).png/, '$1-clicked.png')
		$obj.children('img').attr('src', imgp);

		// add a clicked class
                $obj.addClass('clicked');

		if ( data.jid == -1 ) {
                    $('#job-status-desc').html( data.desc );
		    return
		}

                // set status img of instance
                var imgp = $('#i-status-img').attr('src');
                imgp = imgp.replace(/\d+\.png/, 'running.gif');
                $('#i-status-img').attr('src', imgp);

                $('#job-id').html(data.jid);
                //alert(data.desc + data.jid);
                // TODO: change action between run and stop
                InstanceDynamicStatus();
            }
        });

        return false;

    });

}


function MenuClick() {
    $("#admin-menu a").click(function(event) {
        event.preventDefault();
        var a = $(this);
        var href = a.attr('href');
        href += '&ajax=1';

        $.ajax({
            url: href,
            success: function(data) {
                $('#admin-center').html(data);
                $('#admin-menu a').removeClass('current');
                a.addClass("current");
            }
        }).done(function() { 

        });

    });
}


function AdminMenuslide() {

    var $tool = $('#admin-config-tool');
    var $parent = $tool.parent();
    var $menu = $parent.children('ul');

    $tool.click(function () {
	$menu.slideToggle("normal",function(){ });
    });

}



function lyInstanceSort( sort_obj, select, default_value) {

    var exist = ly_url_get_parameter( sort_obj );
    var found = 0;
    var $choice = $( select );
    if ( exist == "" ) {
        $choice.each(function(){
            if ( this.value == default_value ) {
                this.checked = true;
            } else {
                this.checked = false;
            }
        });
    } else {
        $choice.each(function(){
            if ( this.value == exist ) {
                this.checked = true;
                found = 1;
            } else {
                this.checked = false;
            }
        });
    }

    $choice.click(function(){
        var curval = this.value;
        $choice.each(function(){
            if ( this.value != curval ) {
                this.checked = false;
            }
        });
        ly_url_set_parameter(sort_obj, curval);
    });
}


function indexInstanceLogoHover ( ) {
    $(".section").hover(
	function () {},
	function () {
	    $(".i-logo-hover").hide();
	}
    );

    $(".i-logo").hover(
	function () {

            var curElement = this;

	    var timeoutId = setTimeout(function() {
		$(".i-logo-hover").hide();
		$(curElement).parent().children('.i-logo-hover').show();
	    'slow'}, 250);
 
	    // Use data so trigger can be cleared.
	    $(curElement).data('timeId', timeoutId);
	},
	function () {
	    clearTimeout($(this).data('timeId'));
	}
    );

    $(".i-logo-hover").hover(
	function () {},
	function () {
	    $(this).hide();
	}
    );
}
