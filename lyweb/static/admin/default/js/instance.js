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
}
