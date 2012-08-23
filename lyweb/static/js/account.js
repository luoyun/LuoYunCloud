function HomeSideMenuClick() {

    var $all = $('#u-home-side-menu .one');

    $all.click(function () {
	var $obj = $(this).parent().children('ul');
	$obj.slideToggle("normal", function(){});
    });

}


