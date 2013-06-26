function instance_list_attr_set( selector, return_href ) {
	$(selector).click( function(event) {
		event.preventDefault();

		if ( $(this).hasClass('disabled') )
			return

		var ID = '';
		$('.y-checkarea .icon-check').each( function() {
			myid = $(this).parents('.y-check-line').find('.y-id').html();
			if (myid) {
				if (ID) {
					ID = ID + ',' + myid;
				} else {
					ID = myid;
				}
			}
		});

		var URL = $(this).attr('href');

		$.ajax({
			url: URL,
			type: "POST",
			data: { id: ID },
			dataType: 'json',
			success: function( data ) {
				if (data.return_code != 0) {
					alert( data.retstr_list );
				} else {
					location.href = location.href;
				}

			},
			error: function(data) {
				alert( 'data = ', data );
			},
		});

	});
}

