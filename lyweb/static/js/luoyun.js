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

    if (current == '/instance')
        $("#navigator li:first").addClass("current");


    if (current != '/') {
        var link = "#navigator a[href^='{0}']".format(current);
        $(link).parent().addClass("current");
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


