function forum_vote() {

	$('.vote-opt').click( function(event) {

		event.preventDefault();

		$this = $(this);

		if ( $this.hasClass('disabled') )
			return

		var URL = $this.attr('href');

		$.ajax({
			url: URL,
			type: "POST",
			success: function( data ) {
				if (data.ret_code != 0) {
//					alert( data.ret_string );
				} else {
					var $p = $this.parent()
					$p.find('.like').html( data.like );
					$p.find('.unlike').html( data.unlike );
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
