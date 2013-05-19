/* format a string */
String.prototype.format = function()
{
    var args = arguments;
    return this.replace(/\{(\d+)\}/g,
        function(m,i){
            return args[i];
        });
}

/* Set the current class */
function lySetCurrentNavigator () {
    var current = 'home';
    var pattern = /^(\/[a-zA-Z]*)/;
    var matchs = window.location.pathname.match(pattern);
    if (matchs) {
        current = matchs[1];
    }

//    if (current == '/instance')
//        $("#navigator li:first").addClass("current");


    if (current != '/') {
	if (current == '/message') {
	    $('#my-message-enter').addClass("current");
	} else if (current == '/account') {
	    $('#my-profile-enter').addClass("current");
	} else {
            var link = "#navigator a[href^='{0}']".format(current);
            $(link).parent().addClass("current");
	}
    } else {
        $("#navigator li:first").addClass("current");
    }
}


function lyJudgementMainHeight () {
    var winH = $(window).height();
    var docH = $(document).height();
    var mainH = $("#main").height();
    alert("your window height: " + winH + "\nyour document height: " + docH + "\nyour main height: " + mainH);
    if ( ( docH + 50 ) < winH ) {
        $("#main").css("height", docH - 100);
    }
}



// Hover event on element
function lyHover(id) {
    //alert(id);
    $(id).hover(
        function () {
            $(this).addClass("hover");
        },
        function () {
            $(this).removeClass("hover");
        }
    );
}


function lyMenuSetCurrentEntry ( tag ) {
    var current = '';
    var pattern = /^(\/[-_\/a-zA-Z]*)/;
    var matchs = window.location.pathname.match(pattern);
    if (matchs) {
        current = matchs[1];
    }

    //alert ( 'tag = ' + tag );
    $(tag).each(function (index) {
	var href = $(this).attr('href');
	//alert( 'current = ' + current + ', href = ' + href);
	if (href == current) {
	    $(this).addClass('current');
	} else {
	    $(this).removeClass('current');
	};
    });
}



function lyMenuSetCurrentEntry2 ( tag ) {
    var current = '';
    var pattern = /^(\/[-_\/a-zA-Z]*)/;
    var matchs = window.location.pathname.match(pattern);
    if (matchs) {
        current = matchs[1];
    }

    //alert ( 'tag = ' + tag );
    $(tag).each(function (index) {
	var href = $(this).attr('href');
	//alert( 'current = ' + current + ', href = ' + href);
	if (current.indexOf(href) == 0) {
	    $(this).addClass('current');
	} else {
	    $(this).removeClass('current');
	};
    });
}


function true_false_toggle ( obj, URL ) {

    var check = this.checked;

    if ( $(obj).attr("checked") == "checked" )
	check_value = 'true';
    else
	check_value = 'false';

    if ( URL.indexOf('?') == 0 )
	URL += "&flag=";
    else
	URL += "?flag=";

    $.ajax({
        url: URL + check_value,
        type: 'GET',
        success: function (data) {
	    this.checked = !check;
        }
    });

};


function lyurl_update_arg(url, key, value)
{
    var x = url.split("?");
    var href = x[0];
    var allargs = x[1];

    if ( !value )
	return href;

    if ( !allargs )
        return href + "?" + key + "=" + value;

    var found = 0
    var newsearch = "?"

    var args = allargs.split("&");
    for(var i=0; i<args.length; i++)
    {
        if ( newsearch != "?" )
            newsearch += "&"

        var arg = args[i].split("=");
        if ( arg[0] == key ) {
            newsearch = newsearch + arg[0] + "=" + value
            found = 1
        } else {
            newsearch = newsearch + args[i]
        }
    }

    if ( found == 0 ) {
        newsearch = newsearch + "&" + key + "=" + value
    }

    return href + newsearch;
} 


BackTop=function(btnId){
	var btn=document.getElementById(btnId);
	var d=document.documentElement;
	window.onscroll=set;
	btn.onclick=function (){
		btn.style.display="none";
		window.onscroll=null;
		this.timer=setInterval(function(){
			d.scrollTop-=Math.ceil(d.scrollTop*0.1);
			if(d.scrollTop==0) clearInterval(btn.timer,window.onscroll=set);
		},10);
	};
	function set(){btn.style.display=d.scrollTop?'block':"none"}
};



function shake (ele, cls, times) {

    var i = 0,t= false ,o =ele.attr("class")+" ",c ="",times=times||2;

    if(t) return;

    t= setInterval(function(){
	i++;
	c = i%2 ? o+cls : o;
	ele.attr("class",c);
	if(i==2*times){
	    clearInterval(t);
	    ele.removeClass(cls);
	}
    }, 200);
};


function lygoback()
{
    var domain=window.location.host;
    var protocol=window.location.protocol;
    var url = "$!{url}"||"-1";
    history.go(url);
}



function showTab() {
    $('.tabs li a').click( function() {
	var $obj = $(this);

	var tab = $(this).attr('id').replace('tab-', '');
	var $show = $('#tab-content-' + tab);

	$('.tab-content').hide();
	$('.tabs a').removeClass('selected');

	if ($show.length > 0) {
	    $show.show();
	} else {
	    window.location = $('#tab-' + tab).attr('href');
	}

	$('#tab-' + tab).addClass('selected');
	return false;
    });
}



function simpleToggleCheckbox ( obj, URL, container ) {

    var check = obj.checked;

    $C = $(container).notify()

    if (URL.split('?').length > 1)
	URL = URL + "&t=" + Math.random()
    else
	URL = URL + "?t=" + Math.random()

    $.ajax({
        url: URL,
        type: 'GET',
        success: function (data) {
	    if (data) {
		$(obj).attr('checked', Boolean(check));
		$C.notify("create", "error-template", { text: data }, { expires:false });
	    } else {
		$C.notify("create", "basic-template");
	    }
        }
    });

};


function lyurl_update_params(url, key, value) {
    var L = url.split('?')
    if ( L.length == 1 )
	return url + '?' + key + '=' + value;

    var path = L[0]
    var search = L[1]

    /*
     * http://www.samaxes.com/2011/09/change-url-parameters-with-jquery/
     *
     * queryParameters -> handles the query string parameters
     * queryString -> the query string without the fist '?' character
     * re -> the regular expression
     * m -> holds the string matching the regular expression
     */
    var queryParameters = {}, queryString = search, //location.search.substring(1),
    re = /([^&=]+)=([^&]*)/g, m;

    // Creates a map with the query string parameters
    while (m = re.exec(queryString)) {
	queryParameters[decodeURIComponent(m[1])] = decodeURIComponent(m[2]);
    }

    // Add new parameters or update existing ones
    //queryParameters['newParameter'] = 'new parameter';
    queryParameters[key] = value;

    /*
     * Replace the query portion of the URL.
     * jQuery.param() -> create a serialized representation of an array or
     *     object, suitable for use in a URL query string or Ajax request.
     */
    //location.search = $.param(queryParameters); // Causes page to reload

    return path + '?' + $.param(queryParameters);
}


function draw_used (data) {

    used_percentage = data.used * 100.0 / data.total;
    used_percentage = Math.round(used_percentage * Math.pow(10, 2)) / Math.pow(10, 2);

	if (data.pie_size)
		pie_size = data.pie_size;
	else
		pie_size = 200;
    
	$(data.container).highcharts({
	    chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
        },
        title: {
            text: data.title,
			floating: true,
        },
        subtitle: {
            text: data.subtitle,
			floating: true,
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
				size: pie_size,
                dataLabels: {
                    enabled: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    connectorWidth: 0,
                    distance: 6, // -50 is inside
                    formatter: function() {
                        return '<b>'+ this.point.name +'</b><br/>'+ this.percentage +' %';
                    }
                }
            }
        },
        series: [{
            type: 'pie',
            name: data.series_name,
            data: [
				{
					name: data.used_text,
					color: '#FEC157',
					y: used_percentage,
                    sliced: true,
                    selected: true
				},
                [data.unused_text, 100.0 - used_percentage]
            ]
        }],
        credits: {
            text: 'LuoYun.CO',
            href: 'http://www.luoyun.co'
        }
    });
}
