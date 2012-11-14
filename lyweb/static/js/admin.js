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
	    var aid = $top.children('.i-aid').html();

	    $top.append( HOVER_TEMP.replace('AID', aid) );

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



function lyAdminSortByHover ( HOVER_TEMP, toptag, selecttag ) {

    var obj = toptag + ' .link';
    var hovertag = '.hover-content';

    $(obj).hover(
	function () {

	    $(hovertag).each( function () {
		$(this).remove();
	    });

	    var $top = $(this).parent();
	    var select = $top.children(selecttag).html();
	    $top.append( HOVER_TEMP.replace('SELECT', select) );

	    // Mouse moveout, remove .hover-content
	    $(hovertag).hover(
		function () {},
		function () {
		    $(this).remove();
		}
	    );

	},
	function () {
	}
    );
}


function setCurrent() {
    var cur = window.location.pathname;
    $("#submenu a").removeClass('current');
    $("#submenu a").each(function () {
        var href = $(this).attr('href');
        if (href == cur) {
            $(this).addClass('current');
        };
    });
}


function showHide( tag ) {

    var $hide = $(tag).find('.hide');

    $(tag).hover(
	function () {
	    clearTimeout( $(this).data('hideID') );

	    var ID = setTimeout( function() {
		$hide.show();
	    }, 100);

	    $(this).data('showID', ID);
	},
	function () {
	    clearTimeout( $(this).data('showID') );

	    var ID = setTimeout( function() {
		$hide.hide();
	    }, 100);

	    $(this).data('hideID', ID);
	}
    );
}



function ajaxTuneValue ( obj, container, value ) {

    var $obj = $(obj);

    $C = $(container).notify()

    $.ajax({
        url: $obj.attr("href") + "&t=" + Math.random(),
        type: 'GET',
        success: function (data) {
	    if (data) {
		$C.notify("create", "error-template", { text: data }, { expires:false });
	    } else {
		var $old = $obj.parent().parent().find('.number')
		$old.text( Number($old.text()) + value );
		$C.notify("create", "basic-template");
	    }
        }
    });

};


function simpleClickConfirm( tag, data ) {

    var href = '';

    if (data === undefined)
	data = {
	    title: "Are you sure?",
	    ok: "I'm sure !",
	    cancel: "Cancel",
	    destroy: true,
	    ok_func: function() {
		$(this).dialog( "close" );
		$("<p>Waiting ...</p>").dialog();
		location.href = href;
	    },
	    cancel_func: function() {
		$(this).dialog( "close" );
	    }
	};

    if (data.title === undefined) data.title = "Are you sure?";
    if (data.ok === undefined) data.ok = "I'm sure !";
    if (data.cancel === undefined) data.cancel = "Cancel";
    if (data.destroy === undefined) data.destroy = true;
    if (data.text === undefined) data.text = "Are you sure ?"
    if (data.ok_func === undefined)
	data.ok_func = function() {
	    $(this).dialog( "close" );
	    $("<p>Waiting ...</p>").dialog();
	    location.href = href;
	};
    if (data.cancel_func === undefined)
	data.cancel_func = function() {
	    $(this).dialog( "close" );
	}

    var dialogTag = "ly-confirm-dialog";
    var dialogSelector = '#' + dialogTag;
    var dialogHTML = '<div id="' + dialogTag + 
	'" style="display:none;" class="simple-confirm-dialog">' +
	'<table class="vertical-align"><tr>' +
	'<td><img class="ywarn-img" ' +
	'src="/static/image/warning48.png?v=e10b6"/></td>' +
	'<td><span class="ywarn">' + data.text + '</span></td>' +
	'</tr></table></div>'

    $(tag).click( function(e) {
	e.preventDefault();

	if (data.href === undefined)
	    href = $(this).attr('href');
	else
	    href = data.href

	$('body').append(dialogHTML);

	$(dialogSelector).dialog({
	    title: data.title,
	    autoOpen: false,
	    modal: true,
	    resizable: false,
	    buttons: [{
		text: data.cancel,
		"id": "btnCancel",
		click: data.cancel_func,
	    }, {
		text: data.ok,
		"id": "btnOk",
		click: data.ok_func,
		
	    }],
	    open: function () {
	
	    },
	    close: function () {
		//if (data.destroy)
		//    $( this ).dialog("destroy");
		$(dialogSelector).remove();
	    }
	});

	$(dialogSelector).dialog("open");

	return false;

    });
}
