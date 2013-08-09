function _update_action() {

	var check_sum = $("[name='checkbox']").length;
	var check_num = $("[name='checkbox']:checked").length;

	if ( check_num != check_sum )
		$("[name='checkbox_all']").prop('checked', false);
	else
		$("[name='checkbox_all']").prop('checked', true);

	if ( check_num == 0 ) {
		$(".support-one").addClass("disabled");
		$(".support-nonzero").addClass("disabled");
	} else if ( check_num == 1 ) {
		$(".support-one").removeClass("disabled");
		$(".support-nonzero").removeClass("disabled");
	} else {
		$(".support-one").addClass("disabled");
		$(".support-nonzero").removeClass("disabled");
	}

	$('input[type=checkbox]').each( function() {
		if ( this.checked ) {
			$(this).parents("tr").addClass("success");
		} else {
			$(this).parents("tr").removeClass("success");
		}
	});

}

function binding_checkbox() {

	// toggle checkbox_all
	$("[name='checkbox_all']").click( function() {
		if ($(this).prop('checked') == true) {
			$("[name='checkbox']").prop('checked', true);
		} else {
			$("[name='checkbox']").prop('checked', false);
		}
		_update_action();
	});

	// select all
	$(".select-all").click( function(event) {

		event.preventDefault();
		$("[name='checkbox']").prop('checked', true);
		$("[name='checkbox_all']").prop('checked', true);
		_update_action();
	});

	// unselect all
	$(".unselect-all").click( function(event) {

		event.preventDefault();
		$("[name='checkbox']").prop('checked', false);
		$("[name='checkbox_all']").prop('checked', false);
		_update_action();
	});


	// single select
	$(".item").click( function() {
		var $cb = $(this).find("[name='checkbox']");
		$cb.prop('checked', !$cb.prop('checked'));
		_update_action();
	});
}


function binding_language_select( url ) {
	$('.language-select').change( function() {
		var select = $(this).children('option:selected').val();
		url = url + select;
		location.href = url;
	});
}
