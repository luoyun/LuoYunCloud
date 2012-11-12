function lyInstanceSort( sort_obj, select, default_value) {

    var exist = ly_url_get_parameter( sort_obj );
    var found = 0;
    var $choice = $( select );
    if ( exist == "" ) {
        $choice.each(function(){
            if ( this.value == default_value ) {
                this.checked = true;
            } else {
                this.checked = false;
            }
        });
    } else {
        $choice.each(function(){
            if ( this.value == exist ) {
                this.checked = true;
                found = 1;
            } else {
                this.checked = false;
            }
        });
    }

    $choice.click(function(){
        var curval = this.value;
        $choice.each(function(){
            if ( this.value != curval ) {
                this.checked = false;
            }
        });
        ly_url_set_parameter(sort_obj, curval);
    });
}


function indexInstanceLogoHover ( ) {
    $(".section").hover(
	function () {},
	function () {
	    $(".i-logo-hover").hide();
	}
    );

    $(".i-logo").hover(
	function () {

            var curElement = this;

	    var timeoutId = setTimeout(function() {
		$(".i-logo-hover").hide();
		$(curElement).parent().children('.i-logo-hover').show();
	    'slow'}, 250);
 
	    // Use data so trigger can be cleared.
	    $(curElement).data('timeId', timeoutId);
	},
	function () {
	    clearTimeout($(this).data('timeId'));
	}
    );

    $(".i-logo-hover").hover(
	function () {},
	function () {
	    $(this).hide();
	}
    );
}

