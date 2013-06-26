function binding_action_edit() {

	// edit
	$(".action-edit").click( function(event) {
		event.preventDefault();

		if ($(this).hasClass("disabled"))
			return

		var $obj = $("[name='checkbox']:checked").parents('tr');
		var ID = $obj.find('.item-id').html();
		url = '/admin/site/entry/' + ID + '/edit';
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
			url: '/admin/site/entry/delete',
			data: { 'ids': JSON.stringify(ids) },
			success: function(data) {
				if (data.return_code == 0) {
					$('#delete-warning').modal("hide");
					$.each(data.success_ids, function(k, v) {
						$("#item" + v).remove();
					});
				} else {
					alert('failed: ' + data.failed_ids + ', ' + data.failed_string);
				}
			},
		});

	});
}

