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


function setHeight() {
    var header = $('#header').height();
    var main = $('#main').height();
    var footer = $('#footer').height();

    $('#main').height($(window).height() - header - footer);
}

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
