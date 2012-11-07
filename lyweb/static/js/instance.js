function InstanceControl() {

    $('#iview-inst-control-btn a').click( function () {

	var $obj = $(this);

        URL = $(this).attr('href');

	// set link is unaviable
        $obj.attr('href', "javascript:void(0);");

	// add a clicked class
        $obj.addClass('clicked');

        $.ajax({
            url: URL + "&t=" + Math.random(), // values t is a hack for cache in ie
            type: 'GET',
            success: function (data) {
		if (data.return_code == 0) {
		    imgurl = $('html').data('job-running-img');
		    $('#i-js-img').attr('src', imgurl);
		    $('#i-js-str').text(data.msg);
		    $('#i-js').text('');
		} else {
		    $('#iview-task-result').html(data);
		}
            }
        });

        return false;

    });

}


function MenuClick() {
    $("#admin-menu a").click(function(event) {
        event.preventDefault();
        var a = $(this);
        var href = a.attr('href');
        href += '&ajax=1';

        $.ajax({
            url: href,
            success: function(data) {
                $('#admin-center').html(data);
                $('#admin-menu a').removeClass('current');
                a.addClass("current");
            }
        }).done(function() { 

        });

    });
}


function AdminMenuslide() {

    var $tool = $('#admin-config-tool');
    var $parent = $tool.parent();
    var $menu = $parent.children('ul');

    $tool.click(function () {
	$menu.slideToggle("normal",function(){ });
    });

}



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



// show/hide the .hidden obj in sild
function lyItemHover ( tag ) {

    var x = 22;
    var y = 20;

    $( tag ).hover(

	function ( e ) {
	    var $hidden = $(this).children(".hidden");
	    $hidden.css({top:(e.pageY - y ) + 'px',left:(e.pageX + x ) + 'px'}).fadeIn('fast');
	},

	function () {
            $(this).children(".hidden").hide();
	}

    );

    $( tag ).mousemove( function(e) {
	var $hidden = $(this).children(".hidden");
	$hidden.css({top:(e.pageY -y ) + 'px',left:(e.pageX + x ) + 'px'});
    });

}
