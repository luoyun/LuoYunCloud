function InstanceControl() {

    $('#i-control-btn a').click( function () {

	var $obj = $(this);

        URL = $(this).attr('href');

	// set link is unaviable
        $obj.attr('href', "javascript:void(0);");

	// add a clicked class
        $obj.addClass('clicked');

        $.ajax({
            url: URL + "&t=" + Math.random(), // values t is a hack for cache in ie
            type: 'GET',
            success: function (data) {
		if (data.return_code == 0) {
		    imgurl = $('html').data('job-running-img');
		    $('#i-js-img').attr('src', imgurl);
		    $('#i-js-str').text(data.msg);
		    $('#i-js').text('1'); // TODO:
		    $('#i-reboot-warning').html('');
		} else {
		    $('#i-task-result').html(data);
		}
            }
        });

        return false;

    });

}


function _setInstanceChange (data) {

    var I = data;

    $('#i-is').text(I.is);
    $('#i-is-str').text(I.is_str);
    $('#i-is-img').attr('src', I.is_img);

    $('#i-js').text(I.js);
    $('#i-js-str').text(I.js_str);
    $('#i-js-img').attr('src', I.js_img);

	$('#i-vdi_ip').text(I.vdi_ip);
	$('#i-vdi_port').text(I.vdi_port);

    if (I.lastjob) {
	$('#i-lastjob-id').text(I.lastjob);
    }

    if (I.ip) {
	if (I.ip_link) {
	    newip = '<a href="' + I.ip_link + '" target="_blank">' + I.ip + '</a>';
	} else {
	    newip = I.ip;
	}
	$('#i-ip').html( newip );
    } else {
	$('#i-ip').html('');
    }

    if (I.domain) {
	if (I.domain_link) {
	    newdomain = '<a href="' + I.domain_link + '" target="_blank">' + I.domain + '</a>';
	} else {
	    newdomain = I.domain;
	}
	$('#i-domain').html( newdomain );
    } else {
	$('#i-domain').html('');
    }

    if (I.iaction) {

	/* update control area */
	control_url = $('html').data('inst_control_url');
	img_url = $('html').data('inst_control_imgsrc');

	href = control_url + '?action=' + I.iaction;
	imgsrc = img_url.replace('REPLACE', I.iaction);

	href += '&ajax=True';
	control_html = '<a href="' + href + '"><img src="' + imgsrc + '"/></a>';

	if (I.iaction == 'stop')
	    control_html += $("html").data("i-ctn-reboot-link");
	$('#i-control-btn').html( control_html );
	InstanceControl();
    }

}


function InstanceStatusUpdate () {

    var ID = $('html').data('instance-id');

    var curstatus = { 'id': ID,
		      'is': $('#i-is').text(),
		      'js': $('#i-js').text() }

    $.ajax({

	url: '/instance/single_status' + "?t=" + Math.random() + '&_xsrf=' + $("#xsrf-cookie").text(),
	type: 'POST',
	contentType: "application/json",
	data: JSON.stringify(curstatus),
	dataType: 'json',

	success: function(data) {
	    if (data.return_code == 0)
		_setInstanceChange (data);
            setTimeout(InstanceStatusUpdate, 1500);
	},

	error: function(data) {
            setTimeout(InstanceStatusUpdate, 6000);
	}

    });

}


function checkboxToggle() {
    $('.isprivate-checkbox > input').click( function() {

	var check = this.checked;
	var $obj = $(this);
	var show = 'none';

	if ( $obj.attr('checked') == 'checked')	{
	    check_value = 'true';
	}
	else {
	    check_value = 'false';
	    show = 'inline-block';
	}

	var URL = $obj.parent().children('.access-url').text();

	$.ajax({
	    url: URL + '?flag=' + check_value,
	    type: 'GET',
	    success: function (data) {
		$obj.parent().children('.public-view').css('display',show);
	    }
	});
    });
}


function showTab() {
    $('.tabs li a').click( function() {
	var $obj = $(this);

	var tab = $(this).attr('id').replace('tab-', '');
	var $show = $('#tab-content-' + tab);

	$('.tab-content').hide();
	$('.tabs a').removeClass('selected');

	if ($show.length > 0) {
	    $show.show();
	} else {
	    window.location = $('#tab-' + tab).attr('href');
	}

	$('#tab-' + tab).addClass('selected');
	return false;
    });
}


function toggleStatus() {
    $('.toggle').click( function(e) {

	e.preventDefault();

	var $obj = $(this);

	$.ajax({
	    url: $obj.attr('href'),
	    type: 'GET',
	    success: function (data) {
		$obj.parent().append('<span class="yerror">' + data + '</span>');
	    }
	});

    });
};


