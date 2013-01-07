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
