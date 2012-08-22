function SetMenuCurrent( url ) {
    //alert( url );
    $("#admin-menu a").removeClass('current');
    $("#admin-menu a").each(function (index) {
        var href = $(this).attr('href');
        if (href == url) {
            $(this).addClass('current');
        };
    });
};

function MenuClick() {
    $("#admin-menu a").click(function(event) {
        event.preventDefault();
        var a = $(this);
        var href = a.attr('href');

        $.ajax({
            url: href + '?ajax=1',
            success: function(data) {
                $('#sidemain').html(data);
            }
        }).done(function () {
            SetMenuCurrent( href );
        });
    });

//    $('#admin-menu li.dropdown').click(function() {
//	$(this).find('ul').slideToggle('normal');
//    });

}



function AdminSideMenuClick() {

    var $all = $('#admin-menu .one');
    $("#admin-menu li > ul").slideToggle(900);

    $all.click(function () {
	var $obj = $(this).parent().children('ul');
	$obj.slideToggle("fast", function(){});
    });

}


function lyAdminMenuInit() {
    var current = '';
    var pattern = /^(\/[-_\/a-zA-Z]*)/;
    var matchs = window.location.pathname.match(pattern);
    if (matchs) {
        current = matchs[1];
    }
    var show_obj = false;
    var drop_raw_obj = false;
    $("#ly-admin-menu .dropdown ul li a").each(function (index) {
	var href = $(this).attr('href');
	var $drop = $(this).parent().parent();
	drop_raw_obj = $drop[0];
	//alert( 'current = ' + current + ', href = ' + href);
	if (href == current) {
	    $(this).addClass('current');
	    $drop.parent().find(".show-flag").html("+");
	    $drop.show();
	    show_obj = drop_raw_obj;
	} else {
	    $(this).removeClass('current');
	    if (show_obj != drop_raw_obj) {
		$drop.hide();
		$drop.parent().find(".show-flag").html("-");
	    }
	};
    });

}

function lyAdminMenuHover() {
    $("#ly-admin-menu .dropdown span").hover(
	function () {
	    var $curobj = $(this);
	    var curobj = this;
	    $("#ly-admin-menu .dropdown span").each( function (i, o) {
		var $drop = $(this).parent().children('ul');
		if ( o == curobj ) {
		    $drop.show('slow');
		    $drop.parent().find(".show-flag").html("+");
		    $drop.addClass('hover');
		} else {
		    $drop.hide('slow');
		    $drop.removeClass('hover');
		    $drop.parent().find(".show-flag").html("-");
		}
	    });
	},
	function () {
	}
    );

    $("#ly-admin-menu").hover(
	function () {
	},
	function () {
	    lyAdminMenuInit();
	}
    );
}


function pieHover(event, pos, obj) 
{
    if (!obj)
        return;
    percent = parseFloat(obj.series.percent).toFixed(2);
    var $dynamic_obj = $(this).parent().find('.admin-pie-item-hover')
    //alert ( $dynamic_obj );
    $dynamic_obj.html('<span style="color: '+obj.series.color+'">'+obj.series.label+' ('+percent+'%)</span>');
}

function lyAdminShowPie( tag, data ) {

    $.plot( $(tag), data,
	    {
		series: {
		    pie: {
			show: true,
			radius: 1,
			label: {
			    show: true,
			    radius: 3/5,
			    formatter: function(label, series) {
				return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'+label+'<br/>'+Math.round(series.percent)+'%</div>';
			    },
			    background: { opacity: 0.5 }
			}
		    }
		},
		legend: {
		    show: false
		},
		grid: {
		    hoverable: true,
		    clickable: true
		}
	    });

    $(tag).bind("plothover", pieHover);
}



function lyAdminApplianceOwnerHover ( HOVER_TEMP ) {

    var toptag = '.a-owner';
    var ownertag = '.a-link a';
    var hovertag = '.hover-content';

    $(ownertag).hover(
	function () {

	    $(hovertag).each( function () {
		$(this).remove();
	    });

	    var $top = $(this).parents(toptag);
	    var uid = $top.children('.a-uid').html();

	    $top.append( HOVER_TEMP.replace('UID', uid) );

	    // Mouse moveout, remove .hover-content
	    $('.hover-content').hover(
		function () {
		},
		function () {
		    $(this).remove();
		}
	    );

	},
	function () {
	}
    );
}


function lyAdminInstanceOwnerHover ( HOVER_TEMP ) {

    var toptag = '.i-owner';
    var ownertag = '.i-link a';
    var hovertag = '.hover-content';

    $(ownertag).hover(
	function () {

	    $(hovertag).each( function () {
		$(this).remove();
	    });

	    var $top = $(this).parents(toptag);
	    var uid = $top.children('.i-uid').html();

	    $top.append( HOVER_TEMP.replace('UID', uid) );

	    // Mouse moveout, remove .hover-content
	    $('.hover-content').hover(
		function () {
		},
		function () {
		    $(this).remove();
		}
	    );

	},
	function () {
	}
    );
}
