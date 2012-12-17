function showHide( tag ) {

    var $show = $(tag).find('.show');
    var $hide = $(tag).find('.hide');

    $(tag).hover(
	function () {
	    clearTimeout( $(this).data('hideID') );

	    var ID = setTimeout( function() {
		$hide.show();
		$show.addClass('hover');
	    }, 100);

	    $(this).data('showID', ID);
	},
	function () {
	    clearTimeout( $(this).data('showID') );

	    var ID = setTimeout( function() {
		$hide.hide();
		$show.removeClass('hover');
	    }, 100);

	    $(this).data('hideID', ID);
	}
    );
}


function hoverShowHide( tag ) {
    $(tag).hover(
	function () {
	    clearTimeout( $(this).data('showID') );

	    $hide = $(this).find('.hide');
	    var ID = setTimeout( function() {
		$hide.show();
	    }, 200);

	    $(this).data('showID', ID);
	},
	function () {
	    $hide = $(this).find('.hide');
	    $hide.hide();
	}
    );
}


function aClickConfirm( tag, data ) {

    var href = '';

    if (data === undefined)
	data = {
	    title: "Are you sure?",
	    ok: "I'm sure !",
	    cancel: "Cancel",
	    destroy: true,
	    ok_func: function() {
		$(this).dialog( "close" );
		$("<p>Waiting ...</p>").dialog();
		location.href = href;
	    },
	    cancel_func: function() {
		$(this).dialog( "close" );
	    }
	};

    if (data.title === undefined) data.title = "Are you sure?";
    if (data.ok === undefined) data.ok = "I'm sure !";
    if (data.cancel === undefined) data.cancel = "Cancel";
    if (data.destroy === undefined) data.destroy = true;
    if (data.text === undefined) data.text = "Are you sure ?"
    if (data.ok_func === undefined)
	data.ok_func = function() {
	    $(this).dialog( "close" );
	    $("<p>Waiting ...</p>").dialog();
	    location.href = href;
	};
    if (data.cancel_func === undefined)
	data.cancel_func = function() {
	    $(this).dialog( "close" );
	}

    var dialogTag = "ly-confirm-dialog";
    var dialogSelector = '#' + dialogTag;
    var dialogHTML = '<div id="' + dialogTag + 
	'" style="display:none;" class="simple-confirm-dialog">' +
	'<table class="vertical-align"><tr>' +
	'<td><img class="ywarn-img" ' +
	'src="/static/image/warning48.png?v=e10b6"/></td>' +
	'<td><span class="ywarn">' + data.text + '</span></td>' +
	'</tr></table></div>'

    $(tag).click( function(e) {
	e.preventDefault();

	if (data.href === undefined)
	    href = $(this).attr('href');
	else
	    href = data.href

	$('body').append(dialogHTML);

	$(dialogSelector).dialog({
	    title: data.title,
	    autoOpen: false,
	    modal: true,
	    resizable: false,
	    buttons: [{
		text: data.cancel,
		"id": "btnCancel",
		click: data.cancel_func
	    }, {
		text: data.ok,
		"id": "btnOk",
		click: data.ok_func
	    }],
	    open: function () {
	
	    },
	    close: function () {
		//if (data.destroy)
		//    $( this ).dialog("destroy");
		$(dialogSelector).remove();
	    }
	});

	$(dialogSelector).dialog("open");

	return false;

    });
}



function checkboxClickNotify ( obj, URL, success_text ) {

    var check = obj.checked;
    var $obj = $(obj);

    var notifyTag = $obj.data('notifyTag');
    if ( notifyTag === undefined ) {
	notifyTag = 'lynotify' + Math.round(1000000*Math.random())
	$obj.data('notifyTag', notifyTag);
    }

    var HTML = '' +
'<div id="' + notifyTag + '" style="display:none">' +
'  <div id="basic-template">' +
'    <a class="ui-notify-cross ui-notify-close" href="#">x</a>' +
'    <p>' + success_text + '</p>' +
'  </div>' +
'  <div id="error-template">' +
'    <a class="ui-notify-cross ui-notify-close" href="#">x</a>' +
'    <p>#{text}</p>' +
'  </div>' +
'</div>';

    if ( $('#' + notifyTag).length < 1 ) {
	$('body').append( HTML );
    }

    $C = $('#' + notifyTag).notify();

    if (URL.split('?').length > 1)
	URL = URL + "&t=" + Math.random()
    else
	URL = URL + "?t=" + Math.random()

    $.ajax({
        url: URL,
        type: 'GET',
        success: function (data) {
	    if (data) {
		$(obj).attr('checked', Boolean(check));
		$C.notify("create", "error-template", { text: data }, { expires:false });
	    } else {
		$C.notify("create", "basic-template");
	    }
        }
    });

};


