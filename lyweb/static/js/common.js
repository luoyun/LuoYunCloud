function showHide( tag ) {

    var $show = $(tag).find('.show');
    var $hide = $(tag).find('.hide');

    $(tag).hover(
	function () {
	    clearTimeout( $(this).data('hideID') );

	    var ID = setTimeout( function() {
		$hide.show();
		$show.addClass('hover');
	    }, 100);

	    $(this).data('showID', ID);
	},
	function () {
	    clearTimeout( $(this).data('showID') );

	    var ID = setTimeout( function() {
		$hide.hide();
		$show.removeClass('hover');
	    }, 100);

	    $(this).data('hideID', ID);
	}
    );
}
