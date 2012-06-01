function InstanceDynamicStatus () {

    var jid = $('#job-id').html();
    if (! jid)
    {
        $('#job-status-desc').html('No id found');
        window.setTimeout(InstanceDynamicStatus, 1000);
        return
    }


    var previous = $('#job-status-value').html();

    var URL = '/job/' + jid + '/status?previous=' + previous;

    $.ajax({

        url: URL,
        type: "GET",

        success: function (data) {
            var status = $('#job-status-value').text();

            if (data.job_status != status) {
                $('#job-id').html(jid);
                $('#job-status-value').html(data.job_status);
                $('#job-status-desc').html(data.desc);
                if (data.status == 1) {
                    window.setTimeout(
                        InstanceDynamicStatus, 500);
                } else {
                    // TODO: done
                    if (data.job_status == 301)
                        location.reload(true);
                }
            }
        },

        error: function (data) {
            alert(data + ', try again !');
            window.setTimeout(InstanceDynamicStatus, 5000);
        }

    });

}


function InstanceControl() {

    $('.action .run a, .action .stop a, .action .query a').click( function () {

        var $obj = $(this);

        URL = $obj.attr('href');

        $.ajax({
            url: URL + '?ajax=1',
            type: 'GET',
            success: function (data) {
                if (! data.jid) {
                    $('#job-status-desc').html( data.desc );
                    return
                }

                var imgp = $('.status img').attr('src');
                imgp = imgp.replace(/\d+\.png/, 'running.gif');

                // set status img of instance
                $('.status img').attr('src', imgp);
                $obj.attr('href', "javascript:void(0);");
                $obj.addClass('clicked');

                $('#job-id').html(data.jid);
                //alert(data.desc + data.jid);
                // TODO: change action between run and stop
                InstanceDynamicStatus();
            }
        });

        return false;

    });

}