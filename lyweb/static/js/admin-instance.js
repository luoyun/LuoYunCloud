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
		    $('#i-js').text('1');
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


function lyinst_checkbox_binding() {
    $("#lyinst-list").find('input[name="all"]').click( function() {
	if ( $(this).attr("checked") == 'checked' )
	    $("input[name='instance']").each(function(){
		$(this).attr("checked", true);
	    });
	else
	    $("input[name='instance']").each(function(){
		$(this).attr("checked", false);
	    });
    });
}


function lyinst_control(xsrf) {
    $("#lyinst-list").find('a.lyinst-control-btn').click(function(event){
	event.preventDefault();
	var url = $(this).attr('href');
	var action = $(this).text();

	var idlist = new Array();
	$("input[name='instance']").each(function(){
	    if ( $(this).attr("checked") == 'checked' )
		idlist[idlist.length] = $(this).attr("value");
	});

	$('#ictl-cfm-dialog .ids').html(idlist.join(','));
	$('#ictl-cfm-dialog .action').html( action );

	$('#ictl-cfm-dialog').dialog({

	    title: "Are you sure ?",
	    resizable: false,
	    height: "auto",
	    minWidth: 520,
	    modal: true,
	    buttons: {
		"Cancel": function() {
		    $(this).dialog("close");
		},
		"I'm sure": function() {

		    $('#ictl-cfm-dialog-wait').dialog({
			modal: true,
			minWidth: 300,
		    });

		    $.ajax({
			type: 'POST', 'url': url,
			data: { 'ids': idlist.join(','), '_xsrf': xsrf },
			success: function (data, textStatus) {
			    $('#ictl-cfm-dialog-wait').dialog("close");
			    if (data.code != 0) 
				alert(data.data);
			    else {
				var tbody = '';
				$.each(data.data, function(index,v) {
				    var tr = '<tr><td>' + v.id + '</td><td>' + v.data + '</td></tr>';
				    tbody += tr;
				});
				$('#ictl-cfm-dialog-success .return').html(tbody);
				$('#ictl-cfm-dialog-success').dialog({
				    show: "slow",
				    modal: true,
				    minWidth: 500,
				    maxHeight: 380,
				    create: function() {
					$(this).css("maxHeight", 380);
				    },
				    buttons: {
					"OK": function() {
					    $(this).dialog("close");
					}
				    },
				    close: function( event, ui ) {
					var url = $('#lyinst-list').find('.current-uri').text();
					$.get(url, function(data){ $("#lyinst-list").html(data); });
					$("input[name='instance']").each(function(){
					    $(this).attr("checked", false);
					});
				    }
				});
			    }
			},
			error: function (XMLHttpRequest, textStatus, errorThrown) {
			    alert('error: server response ' + XMLHttpRequest.status);
			}
		    });
		    $( this ).dialog( "close" );
		}
	    },
	    close: function() {
		$(this).dialog("destroy");
	    }
	});
	return false;
    });
}


function lyinst_name_hover() {
    $("#lyinst-list .i-name").hover(
	function(){
	    $(this).parents('tr').after('<div class="hover-content"><h1>hELLO</h1></div>');
	},
	function(){
	    $('#lyinst-list tbody > .hover-content').remove();
	}
    );
}

function lyinst_list_binding() {
    $("#lyinst-list .i-list tr.even").hide();
    
    $("#lyinst-list .i-list td.ex").click(function(){
	var id = $(this).parents("tr").attr("id")
	var url = $(this).attr('href');
	var $next_tr = $(this).parents("tr").next("tr");
	$next_tr.toggle();
	$(this).toggleClass("up");
	if ($(this).text() == '+')
	    $(this).text("-");
	else
	    $(this).text("+");

	var content_id = '#' + id + '-hide';
	if ( $(content_id).children().length <= 0 )
	{
	    $(content_id).html('<img src="/static/admin/default/css/img/running.gif" /> loading ...')
	    $.ajax({
		type: 'GET', 'url': url,
		success: function (data, textStatus) {
		    $(content_id).html(data);
		}
	    });
	}
    });

    $("#lyinst-list .i-list tr.odd").hover(
	function(){
	    $("#lyinst-list .i-list tr.odd").removeClass('hover');
	    $(this).addClass('hover');
	},
	function(){}
    );
}

function lyinst_page_view_binding() {
    $('#lyinst-list .pagination a').click(function(event) {
	event.preventDefault();
	var url = $(this).attr('href');
	url = lyurl_update_params(url, 'ajax', 't');
	$.get(url, function(data){ $("#lyinst-list").html(data); });
    })
    return false;
}

function lyinst_search() {
    $("#search input").keyup(function(){
	txt=$("#search input").val();

	var url = $('#lyinst-list').find('.current-uri').text();
	url = lyurl_update_params(url, 'search', txt);
	url = lyurl_update_params(url, 'p', '1');
	url = lyurl_update_params(url, 'ajax', 't');

	clearTimeout($(this).data('timeId'));

	var timeoutId = setTimeout(function() {
	    $.get(url,function(data){
		$("#lyinst-list").html(data);
	    }); }, 300);

	$(this).data('timeId', timeoutId);
    });
}

function lytip_ajax_binding() {
    // Make sure to only match links to wikipedia with a rel tag
    $('a.tip-ajax').each(function(){
	// We make use of the .each() loop to gain access to each element via the "this" keyword...
	$(this).qtip(
	    {
		content: {
		    // Set the text to an image HTML string with the correct src URL to the loading image you want to use
		    text: '<img class="throbber" src="/projects/qtip/images/throbber.gif" alt="Loading..." />',
		    ajax: {
			url: lyurl_update_params($(this).attr('href'), 'ajax', 't')
		    },
		    title: {
			text: 'LuoYunCloud - ' + $(this).text(), // Give the tooltip a title using each elements text
			button: true
		    }
		},
		position: {
		    at: 'bottom center', // Position the tooltip above the link
		    my: 'top center',
//		    viewport: $(window), // Keep the tooltip on-screen at all times
		    effect: false // Disable positioning animation
		},

		show: {
		    event: 'click',
		    solo: true // Only show one tooltip at a time
		},

		hide: 'unfocus',

		style: {
		    widget: false,
		    //def: false,
		    classes: 'qtip-light qtip-user-info'
		}
	    })
    })
	// Make sure it doesn't follow the link when we click it
	.click(function(event) { event.preventDefault(); });
}

