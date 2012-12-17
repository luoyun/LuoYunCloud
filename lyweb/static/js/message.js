function deleteMessage ( obj, container ) {

    var check = obj.checked;

    $C = $(container).notify()

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
