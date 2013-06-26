function _update_single_action_img(action) {

	$btnimg = $('#instance-life-control-btn i');
	if ( action == 'run' ) {
		$btnimg.css('color', 'gray');
		$btnimg.attr('class', 'icon-refresh');
	} else if ( action == 'query' ) {
		$btnimg.css('color', 'blue');
		$btnimg.attr('class', 'icon-question-sign');
	} else if ( action == 'stop' ) {
		$btnimg.css('color', 'red');
		$btnimg.attr('class', 'icon-off');
	} else {
		$btnimg.css('color', 'orange');
		$btnimg.attr('class', 'icon-spinner icon-spin');
	}

}
function _update_single_status(data) {
    var I = data;

    $('#i-is').text(I.is);
    $('#i-is-str').text(I.is_str);
    $('#i-is-img').html(I.is_img);

    $('#i-js').text(I.js);
    $('#i-js-str').text(I.js_str);
    $('#i-js-img').html(I.js_img);

	$('#i-vdi-ip').text(I.vdi_ip);
	$('#i-vdi-port').text(I.vdi_port);


	// update action
	if ( $('#i-action') != I.action ) {
		var $btn = $('#instance-life-control-btn a');
		$btn.removeClass('disable');

		$('#i-action').text(I.action);
		$('#instance-life-control-btn span').text(I.action_trans);
		_update_single_action_img( I.action );
	}
}

function single_life_control( data ) {

	_update_single_action_img( $('#i-action').text() );

	var $btn = $('#instance-life-control-btn a');

	$btn.hover( function(event) {
		$(this).find('i').toggleClass('hover');
	});

	$btn.click( function(event) {
		event.preventDefault();

		if ( $(this).hasClass('disable') )
			return

		var data = { 'id': $('#i-id').text(),
					 'action': $('#i-action').text() };

		var URL = $(this).attr('href');

		$.ajax({
			url: URL,
			type: 'POST',
			data: data,
			dataType: 'json',

			success: function(data) {

				var title = $('#instance-lifecontrol-title').html();
				var body = $('#instance-lifecontrol-body').html();

				var $modal = $('#action-return-modal');
				$modal.find('.modal-title').html(title);
				$modal.find('.modal-body').html(body);
				$modal.modal();

				var detail_html = '';
				$.each(data.data, function(k, v) {
					detail_html += '<tr><td>' + v.id + '</td><td>' + v.data + '</td></tr>';
				});
				$modal.find('.detail').html( detail_html );

				if (data.code == 0) {
					$modal.find('.action-success').show();

					// update img
					var $btnimg = $('#instance-life-control-btn i');
					$btnimg.attr('class', 'icon-spinner icon-spin');
					$btnimg.css('color', 'green');

					// add disable
					$(this).addClass('disable');

				} else {
					$modal.find('.action-failed').show();
				};

			},

			error: function(data) {
				setTimeout(single_status_monitor, 6000);
			}
		});
	});

}


function single_status_monitor () {

    var curstatus = { 'id': $('#i-id').text(),
					  'is': $('#i-is').text(),
					  'js': $('#i-js').text() };

	var random = Math.random().toString().substr(2,6);
	var URL = '/instance/single_status' + "?t=" + random;

    $.ajax({
		url: URL,
		type: 'POST',
		data: curstatus,
		dataType: 'json',

		success: function(data) {
			if (data.return_code == 0)
				_update_single_status(data);
            setTimeout(single_status_monitor, 3000);
		},

		error: function(data) {
            setTimeout(single_status_monitor, 9000);
		}

    });

}


function single_instance_delete() {

	var $btn = $('.instance-delete-btn');
	$btn.click( function(event) {
		event.preventDefault();

		if ( $(this).hasClass('disable') )
			return

		var title = $('#instance-delete-title').html();
		var body = $('#instance-delete-body').html();

		var $modal = $('#action-return-modal');
		$modal.find('.modal-title').html(title);
		$modal.find('.modal-body').html(body);

		$('.instance-delete-btn-true').click( function(event) {
			event.preventDefault();

			$modal.find('.action-success').hide();
			$modal.find('.action-failed').hide();

			var URL = $(this).attr('href');
			var post_data = { 'id': $('#i-id').text(),
							  'action': 'delete' }

			$body = $(this).parents('.modal-body');

			$.ajax({
				url: URL,
				type: 'POST',
				dataType: 'json',
				data: post_data,

				success: function(data) {
					if (data.code == 0) {
						$modal.find('.action-success').show();
					} else {
						$modal.find('.action-failed').show();
						var detail_html = '';
						$.each(data.data, function(k, v) {
							detail_html += '<tr><td>' + v.id + '</td><td>' + v.data + '</td></tr>';
						});
						$modal.find('.detail').html( detail_html );
					};
				},
			});
		});

		$modal.modal();
	});

}


function multi_life_control( selector ) {

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
			type: 'POST',
			data: { 'id': ID },
			dataType: 'json',

			success: function(data) {

				var title = $('#instance-lifecontrol-title').html();
				var body = $('#instance-lifecontrol-body').html();

				var $modal = $('#action-return-modal');
				$modal.find('.modal-title').html(title);
				$modal.find('.modal-body').html(body);
				$modal.modal();

				var detail_html = '';
				$.each(data.data, function(k, v) {
					detail_html += '<tr><td>' + v.id + '</td><td>' + v.data + '</td></tr>';
				});
				$modal.find('.detail').html( detail_html );

				if (data.code == 0) {
					$modal.find('.action-success').show();

					// add disable
					$(this).addClass('disable');

				} else {
					$modal.find('.action-failed').show();
				};

			}
		});
	});
}

