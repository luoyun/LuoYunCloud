function _get_parameters()
{
    if ( location.search == "" ) 
        return

    var params = new Object();
    var keys = new Array();

    var allargs = location.search.split("?")[1];
    var args = allargs.split("&");

    for (var i=0; i<args.length; i++) {
        keys[ keys.length ] = args[0];
        params[ args[0] ] = args[1];
    }
}

function _generate_url_search()
{
    var ts = '';
    for (var i=0; i<keys.length; i++) {
        ts = ts + "##" + params[ keys[i] ];
    }
    alert( "ts = " + ts );
}


function ly_url_set_parameter(key, value)
{
    if ( location.search == "") {
        location.search = "?"+key+"="+value
        return 
    }

    var found = 0
    var newsearch = "?"
    var allargs = location.search.split("?")[1];
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

    location.search = newsearch
} 


function ly_url_get_parameter(key)
{
    if ( location.search == "") {
        return ""
    }

    var allargs = location.search.split("?")[1];
    var args = allargs.split("&");
    for(var i=0; i<args.length; i++)
    {
        var arg = args[i].split("=");
        if ( arg[0] == key ) {
            return arg[1]
        }
    }

    return ""
} 


function ly_url_orderby( by )
{
    if ( location.search == "") {
        location.search = "?by=" + by + "&order=DESC"
        return
    }

    var found = 0
    var newsearch = "?"
    var allargs = location.search.split("?")[1];
    var args = allargs.split("&");
    for(var i=0; i<args.length; i++)
    {
        if ( newsearch != "?" )
            newsearch += "&"

        var arg = args[i].split("=");
        if ( arg[0] == 'by' ) {
            newsearch = newsearch + "by=" + by
            found = 1
        } else {
            if ( arg[0] == 'order' && arg[1] == 'DESC' ) {
                newsearch = newsearch + arg[0] + "=ASC"
            } else if ( arg[0] == 'order' && arg[1] == 'ASC' ) {
                newsearch = newsearch + arg[0] + "=DESC"
            } else {
                newsearch = newsearch + args[i]
            }
        }
    }

    if ( found == 0 ) {
        newsearch = newsearch + "&by=" + by
    }

    location.search = newsearch
} 
