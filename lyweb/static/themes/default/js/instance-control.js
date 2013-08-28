function _update_single_action_img(action) {

	$btnimg = $('#instance-life-control-btn i');
	if ( action == 'run' ) {
		$btnimg.css('color', 'blue');
		$btnimg.attr('class', 'icon-play');
	} else if ( action == 'query' ) {
		$btnimg.css('color', 'blue');
		$btnimg.attr('class', 'icon-question-sign');
	} else if ( action == 'stop' ) {
		$btnimg.css('color', 'red');
		$btnimg.attr('class', 'icon-stop');
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

    $('#i-vdi-ip').text(I.vdi_ip);
    $('#i-vdi-port').text(I.vdi_port);

    $('#i-domain').html(I.domain_link);
    $('#i-ip').html(I.ip_link);

	// update action
	if ( $('#i-action').text() != I.action ) {
		$('#i-action').text(I.action);
		$('#instance-life-control-btn span').text(I.action_trans);

		_update_single_action_img( I.action );
	}

	// update button status
	var $btn = $('#instance-life-control-btn a');
	if ( I.j_completed ) {
		$btn.removeClass('disabled');

		$('#i-js-str').text('');
		$('#i-js-img').html('');

	} else {
		$btn.addClass('disabled');
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

		var $this = $(this);

		if ( $this.hasClass('disabled') )
			return;

		single_status_monitor();
		$this.addClass('disabled');

		var data = { 'id': $('#i-id').text(),
					 'action': $('#i-action').text() };

		var URL = $this.attr('href');

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

				var j_str_html = '';

				$.each(data.data, function(k, v) {
					if (j_str_html)
						j_str_html += '<br>'
					j_str_html += '<span class="text-error">' + v.data + '</span>';
				});

				$('#i-js-str').html( j_str_html );
				$modal.find('.detail').html( j_str_html );

				if (data.code == 0) {
					$('#i-js-img').html('<img src="/static/image/running.gif?v=0.6.1" />');
					$modal.find('.action-success').show();
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

			if ( ! data.j_completed )
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

		if ( $(this).hasClass('disabled') )
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

			$body = $(this).parents('.modal-body');

			$.ajax({
				url: URL,
				type: 'POST',

				success: function(data) {
					if (data.code == 0) {
						$modal.find('.action-success').show();
					} else {
						$modal.find('.action-failed').show();
						$modal.find('.detail').html( data.data );
					};
				},
			});
		});

		$modal.modal();
	});

}



function multi_instance_lifecontrol( ) {

    $('.multi-lifecontrol-opt').click( function(event) {
        event.preventDefault();

        $this = $(this);

        if ( $this.hasClass('disabled') )
            return

        var URL   = $this.attr('href');
        var warn  = $this.data('warning');
        var title = $this.attr('title');

        var $body = $('#multi-lifecontrol-window-body');

        var $modalobj = $('#multi-lifecontrol-window');
        var $okbtn = $modalobj.find('.ok-btn');

        $modalobj.find('.title').text( title );

        $okbtn.removeClass('disabled');
        $okbtn.show();

        $body.find('.warning').text( warn );

        $return_area = $modalobj.find('.modal-body');
        $return_area.html( $body.html() );

        // OK button
        $okbtn.click( function(event) {

            if ( $(this).hasClass('disabled') )
                return

            $(this).addClass('disabled');
            $(this).hide();

            $return_area.html('');

            $('.y-checkarea .icon-check').each( function() {
                ID = $(this).parents('.y-check-line').find('.y-id').html();
                if ( ID ) {
                    
		            $.ajax({
			            url: URL,
			            type: 'POST',
			            data: { 'id': ID },
			            dataType: 'json',

			            success: function(data) {

                            // TODO: hack now
                            if (typeof(data.data) == 'string')
                                detail_html = data.data;
                            else {
				                var detail_html = '';
				                $.each(data.data, function(k, v) {
					                detail_html += '<strong>' + v.id + '</strong>, ' + v.data + '<br>';
				                });
                            }

                            $return_area.append('<div>' + detail_html + '</div>');

                        },

                        error: function() {
                            $return_area.append('<div class="text-error">Internal Server Error</div>');
                        }
                    });

                }
            });

        });

        $modalobj.modal();

        return
    });
}

