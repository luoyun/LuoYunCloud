function forum_vote() {

	$('.vote-opt').click( function(event) {

		$this = $(this);
/*
		if ( $this.hasClass('disabled') ) {

			noty({
				layout: 'topRight',
				type: 'warning',
				timeout: 3000,
				text: $('#repeat-click-string').html()
			});

			return
		}
*/
		var URL = $this.data('url');

		$.ajax({
			url: URL,
			type: "POST",
			success: function( data ) {
				if (data.ret_code != 0) {
					noty({
						layout: 'topRight',
						type: 'warning',
						timeout: 6000,
						text: data.ret_string
					});
				} else {
					var $p = $this.parent().parent();
					$p.find('.like').html( data.like );
					$p.find('.unlike').html( data.unlike );

					noty({
						layout: 'topRight',
						type: 'success',
						timeout: 1500,
						text: data.ret_string
					});
				}
				$this.addClass('disabled');
			},
		});

	});
};


function forum_topic_delete() {

	$('.topic-delete-btn').click( function(event) {

		event.preventDefault();

		$this = $(this);

		var $modal = $('#topic-delete-modal');
		$modal.modal();
	});

	$('#topic-delete-modal .real-delete').click( function(event) {
		event.preventDefault();
		$this = $(this);
		var URL = $this.attr('href');

		var $body = $('#topic-delete-modal .modal-body');

		$.ajax({
			url: URL,
			type: "POST",
			success: function( data ) {
				if (data.ret_code != 0) {
					var html = '<div class="text-warning">' + data.ret_string + '</div>'
				} else {
					var html = '<div class="text-success">' + data.ret_string + '</div>'
				}
				$body.html( html );
			},
		});

	});
};
