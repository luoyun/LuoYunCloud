function _setInstanceChange (data) {
    var return_code = data.return_code;
    var INS = data.instance;
    for (var i = 0; i < INS.length; i++) {
	instance = INS[i];
	instance_id = instance.id;
	tag = 'i'+instance_id;

	$('#' + tag + '-js').text(instance.js);
	$('#' + tag + '-is').text(instance.is);

	$('#' + tag + '-js-str').text(instance.js_str);
	$('#' + tag + '-is-str').text(instance.is_str);

	$('#' + tag + '-is-img').attr('src', instance.is_img);
	$('#' + tag + '-js-img').attr('src', instance.js_img);

	if (instance.ip) {
	    if (instance.ip_link) {
		newip = '<a href="' + instance.ip_link + '" target="_blank">' + instance.ip + '</a>';
	    } else {
		newip = instance.ip;
	    }
	    $('#iview-ip').html( newip );
	} else {
	    $('#iview-ip').html('');
	}

	if (instance.domain) {
	    if (instance.domain_link) {
		newdomain = '<a href="' + instance.domain_link + '" target="_blank">' + instance.domain + '</a>';
	    } else {
		newdomain = instance.domain;
	    }
	    $('#iview-domain').html( newdomain );
	} else {
	    $('#iview-domain').html('');
	}

	if (instance.iaction) {

	    /* update control area */
	    control_url = $('html').data('inst_control_url');
	    img_url = $('html').data('inst_control_imgsrc');

	    href = control_url + '?action=' + instance.iaction;
	    imgsrc = img_url.replace('REPLACE', instance.iaction);

	    href += '&ajax=True';
	    control_html = '<a href="' + href + '"><img src="' + imgsrc + '"/></a>';
	    $('#iview-inst-control-btn').html( control_html );
	    InstanceControl();
	}

    }
    
}


function CheckInstanceStatus () {

    var IDS = $('html').data('watch-instance-list');
    IDS = JSON.parse(IDS);
    
    var instance = new Array();

    for (var i = 0; i < IDS.length; i++) {

	id = IDS[i];

	instance.push({
	    'id': id,
	    'js': $('#i' + id + '-js').text(),
	    'is': $('#i' + id + '-is').text() });

    }

    var curstatus = { 'instance': instance, 'show_action': 1,
		      'show_domain': 1, 'show_ip': 1,
		      'show_job': 1 };

    $.ajax({

	url: '/instance/status',
	type: 'POST',
	contentType: "application/json",
	data: JSON.stringify(curstatus),
	dataType: 'json',

	success: function(data) {
	    if (data.return_code == 0)
		_setInstanceChange (data);
            setTimeout(CheckInstanceStatus, 1500);
	},

	error: function(data) {
            setTimeout(CheckInstanceStatus, 6000);
	}

    });

}


function _setSingleInstanceChange (data) {

    var I = data;

    $('#i-is').text(I.is);
    $('#i-is-str').text(I.is_str);
    $('#i-is-img').attr('src', I.is_img);

    $('#i-js').text(I.js);
    $('#i-js-str').text(I.js_str);
    $('#i-js-img').attr('src', I.js_img);

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
	$('#iview-inst-control-btn').html( control_html );
	InstanceControl();
    }

}


function SingleInstanceStatusUpdate () {

    var ID = $('html').data('instance-id');

    var curstatus = { 'id': ID,
		      'is': $('#i-is').text(),
		      'js': $('#i-js').text() }

    $.ajax({

	url: '/instance/single_status' + "?t=" + Math.random(),
	type: 'POST',
	contentType: "application/json",
	data: JSON.stringify(curstatus),
	dataType: 'json',

	success: function(data) {
	    if (data.return_code == 0)
		_setSingleInstanceChange (data);
            setTimeout(SingleInstanceStatusUpdate, 1500);
	},

	error: function(data) {
            setTimeout(SingleInstanceStatusUpdate, 6000);
	}

    });

}
