function InstanceStatusCheck ( URL, update_url ) {
    var job_status = $('#lyjob-status-id').html();
    var instance_status = $('#lyinst-status-id').html();

    var newurl = URL + '?instance_status=' + instance_status + '&job_status=' + job_status;

    $.ajax({
	url: newurl,
	type: "GET",

	success: function (data) {

	    $('#lyjob-id').html(data.job_id);
	    $('#lyjob-status-id').html(data.jstatus);
	    $('#lyjob-status-str').html(data.jstatus_str);
	    $('#lyjob-status-img').attr('src', data.jstatus_imgurl);

	    $('#lyinst-status-id').html(data.istatus);
	    $('#lyinst-status-str').html(data.istatus_str);
	    $('#lyinst-status-img').attr('src', data.istatus_imgurl);

	    if (data.job_completed) {
		$('#iview-task-result').html('');
	    }

	    if (data.ip) {
		if (data.ip_link) {
		    newip = '<a href="' + data.ip_link + '" target="_blank">' + data.ip + '</a>';
		} else {
		    newip = data.ip;
		}
		$('#iview-ip').html( newip );
	    } else {
		$('#iview-ip').html('');
	    }

	    if (data.domain) {
		if (data.domain_link) {
		    newdomain = '<a href="' + data.domain_link + '" target="_blank">' + data.domain + '</a>';
		} else {
		    newdomain = data.domain;
		}
		$('#iview-domain').html( newdomain );
	    } else {
		$('#iview-domain').html('');
	    }

	    $.get(update_url, function(result) {
		$('#i-action').html(result);
	    });


            window.setTimeout(InstanceStatusCheck, 1200, URL, update_url);

	    //alert( 'data.jstatus_str = ' + data.jstatus_str );
	},

        error: function (data) {
            //alert(data + ', try again !');
            window.setTimeout(InstanceStatusCheck, 6000, URL, update_url);
        }
    });


}

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

    $('#iview-inst-control-btn a').click( function () {

	var $obj = $(this);

        URL = $(this).attr('href');

	// set link is unaviable
        $obj.attr('href', "javascript:void(0);");

	// change img on clicked status
	var imgp = $obj.children('img').attr('src');
	imgp = imgp.replace(/(\w+).png/, '$1-clicked.png')
	$obj.children('img').attr('src', imgp);

	// add a clicked class
        $obj.addClass('clicked');


        $.ajax({
            url: URL,
            type: 'GET',
            success: function (data) {
		$('#iview-inst-control-btn').html(data);
            }
        });

        return false;

    });

}

function InstanceControlOld() {

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



// show/hide the .hidden obj in sild
function lyItemHover ( tag ) {

    var x = 22;
    var y = 20;

    $( tag ).hover(

	function ( e ) {
	    var $hidden = $(this).children(".hidden");
	    $hidden.css({top:(e.pageY - y ) + 'px',left:(e.pageX + x ) + 'px'}).fadeIn('fast');
	},

	function () {
            $(this).children(".hidden").hide();
	}

    );

    $( tag ).mousemove( function(e) {
	var $hidden = $(this).children(".hidden");
	$hidden.css({top:(e.pageY -y ) + 'px',left:(e.pageX + x ) + 'px'});
    });

}
