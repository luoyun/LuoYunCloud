function _update_action() {

	var check_sum = $("[name='checkbox']").length;
	var check_num = $("[name='checkbox']:checked").length;

	if ( check_num != check_sum )
		$("[name='checkbox_all']").prop('checked', false);
	else
		$("[name='checkbox_all']").prop('checked', true);

	if ( check_num == 0 ) {
		$(".action-edit").addClass("disabled");
		$(".action-delete").addClass("disabled");
	} else {
		if ( check_num == 1 ) {
			$(".action-edit").removeClass("disabled");
		} else {
			$(".action-edit").addClass("disabled");
		}
		$(".action-delete").removeClass("disabled");
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
	$("tr.item").click( function() {
		var $cb = $(this).find("[name='checkbox']");
		$cb.prop('checked', !$cb.prop('checked'));
		_update_action();
	});
}


function binding_action_edit() {

	// edit
	$(".action-edit").click( function(event) {
		event.preventDefault();

		if ($(this).hasClass("disabled"))
			return

		var $obj = $("[name='checkbox']:checked").parents('tr');
		var eid = $obj.find('.item-id').html();
		url = '/admin/cms/category/' + eid + '/edit';
		//alert('edit action: ' + url);
		location.href = url;
	})

}

function binding_action_delete() {

	// delete
	$(".action-delete").click( function(event) {
		event.preventDefault();

		if ($(this).hasClass("disabled"))
			return

		ids = new Array();

		$("[name='checkbox']:checked").each( function() {
			ids[ ids.length ] = $(this).parents('tr').find('.item-id').html();
		});
		$('#delete-warning').modal();
	})

	$(".delete-confirm").click( function(event) {

		$.ajax({
			type: 'POST',
			url: '/admin/cms/category/delete',
			data: { 'ids': JSON.stringify(ids) },
			success: function(data) {
				if (data.return_code == 0) {
					$('#delete-warning').modal("hide");
					$.each(data.success_ids, function(k, v) {
						$("#item" + v).remove();
					});
				} else {
					alert('failed: ' + data.failed_ids);
				}
			},
		});

	});
}
