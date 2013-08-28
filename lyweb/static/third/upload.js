function Uploading() {
    $(function() {

        $("form").uploadProgress({
            /* scripts locations for safari */
            jqueryPath: "/static/third/jquery-1.9.1.min.js",
            uploadProgressPath: "/static/third/jquery.uploadProgress.js",

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
