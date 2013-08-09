function appliance_list_attr_set( selector ) {
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
			data: { id: ID,
					_xsrf: $('.xsrf-cookie').text() },
			dataType: 'json',
			success: function( ret ) {
				if (ret.code != 0) {

					var detail_html = '';

					$.each(ret.data, function(k, v) {
						detail_html += '<tr><td>' + v.id + '</td><td>' + v.string + '</td></tr>';
					});

					$('#appliance-setattr-modal-body').find(
						'.detail').html( detail_html );

					$('#appliance-setattr-modal-body').find(
						'.title').html( ret.string );

					var $modal = $('#action-return-modal');

					$modal.find('.modal-body').html(
						$('#appliance-setattr-modal-body').html() )

					$modal.modal();
				} else {
					location.href = '/myun/appliance';
				}

			},
			error: function(ret) {
				alert( 'ret = ', ret );
			},
		});

	});
}

