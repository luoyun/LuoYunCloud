function Uploading() {
    $(function() {

        $("form").uploadProgress({
            /* scripts locations for safari */
            jqueryPath: "${STATIC_URL}js/jquery-1.7.min.js",
            uploadProgressPath: "${STATIC_URL}js/jquery.uploadProgress.js",

            start: function() {
                var t = new Date();
                var seconds = t.getHours() * 3600;
                seconds += t.getMinutes() * 60;
                seconds += t.getSeconds();

                $('body').data('start_time', seconds);

                $("#uploading").show();
            },

            /* function called each time bar is updated */
            uploading: function(upload) {

                var t = new Date();
                var now = t.getHours() * 3600;
                now += t.getMinutes() * 60;
                now += t.getSeconds();

                var start = $('body').data('start_time');

                var rate = Math.floor( (upload.received) / (now - start) )

                var remain = Math.floor( (upload.size - upload.received) / rate ) 

                if ( rate > 1048576 )
                    rate = ( rate / 1048576 ).toFixed(2) + 'M/s'
                else if ( rate > 1024 )
                    rate = ( rate / 1024 ).toFixed(2) + 'Kb/s'
                else
                    rate = rate + 'B/s'

                if ( remain > 3600 )
                    remain = Math.floor( remain / 3600 ) + 'h'
                else if ( remain > 60 )
                    remain = Math.floor( remain / 60 ) + 'm'
                else
                    remain = remain + 's'
                
                

                $('#percents').html(upload.percents+'%' + ' (' + rate + ', remain ' + remain + ')');
            },

            success: function(upload) { $("#uploading").hide(); },

            /* selector or element that will be updated */
            progressBar: "#progressbar",

            /* progress reports url */
            progressUrl: "/progress",

            /* how often will bar be updated */
            interval: 1000,
        });
    });

}

function ApplianceHover() {

    return false;

    $(".appliance").each( function () {
        var $obj = $(this);
        var $info = $obj.find(".appliance-base-info")
        //$info.show();
        URL = $obj.find(".logo a").attr("href");

        $obj.qtip({
            //content: $info
            //content:  "show appliance-base-info"
            content: {
                text: "Loading ...",
                ajax: {
                    url: URL + '?ajax=1'
                }
            },
            show: {
                event: 'click',
                solo: true,
                modal: true
            },
            hide: false
        });
    })
}

function ApplianceHoverOld() {
    $(".sidemain .appliance").hover(
        function () {

            obj = $(this);

            if (obj.find(".appliance-base-info").length > 0) {
                $(".appliance-base-info").hide();
                obj.find(".appliance-base-info").show();
                return;
            }

            URL = obj.find(".logo a").attr("href");
            $.ajax({
                url: URL + '?ajax=1',
                type: 'GET',
                success: function (data) {
                    obj.append(data);
                    $(".appliance-base-info").hide();
                    obj.find(".appliance-base-info").show();
                    ApplianceDeleteInIndex(); // TODO
                }
            });
        },
        function () {
            $(this).find(".appliance-base-info").hide();
        }
    );
}


function DeleteInstance() {

    $(".instance-list .delete").qtip({

        content: {
            text: "Loading ...",
            ajax: {
                url:  $(this).attr('href')
            }
        },
        show: {
            event: 'click', // Show it on click...
            solo: true, // ...and hide all other tooltips...
            modal: true // ...and make it modal
        },
        hide: false

    });

}

