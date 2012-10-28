function InstanceStatusCheck () {

    var job_status = $('#lyjob-status-id').html();

    if (! $('#lyjob-id').html()) {
	job_status = 12345;
    }

    var instance_status = $('#lyinst-status-id').html();

    var newurl = $('html').data('iview_status_url') + '?instance_status=' + instance_status + '&job_status=' + job_status;

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

	    /* update control area */
	    control_url = $('html').data('inst_control_url');
	    img_url = $('html').data('inst_control_imgsrc');

	    if (data.iaction == 'run') {
		href = control_url + '?action=run';
		imgsrc = img_url.replace('REPLACE', 'run');
	    } else if (data.iaction == 'query') {
		href = control_url + '?action=query';
		imgsrc = img_url.replace('REPLACE', 'query');
	    } else if (data.iaction == 'stop') {
		href = control_url + '?action=stop';
		imgsrc = img_url.replace('REPLACE', 'stop');
	    }
	    control_html = '<a href="' + href + '"><img src="' + imgsrc + '"/></a>'
	    $('#iview-inst-control-btn').html( control_html );
	    InstanceControl();


	    clearTimeout($('html').data('statusCheck'));
            var tid = setTimeout(InstanceStatusCheck, 6000);
	    $('html').data('statusCheck', tid);
	},

        error: function (data) {
	    clearTimeout($('html').data('statusCheck'));
            var tid = setTimeout(InstanceStatusCheck, 12000);
	    $('html').data('statusCheck', tid);
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
		$('#iview-task-result').html(data);
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
