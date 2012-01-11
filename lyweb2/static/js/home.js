$(document).ready(function() {
    updater.poll();
});


var updater = {

    errorSleepTime: 5000,

    poll: function() {
        var args = {"total": $("#online-total").html()};
        $.ajax({url: "/account/online_total", type: "POST", dataType: "text",
                data: $.param(args), success: updater.onSuccess,
                error: updater.onError});
    },

    onSuccess: function(response) {
        $("#online-total").html(response);
        window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
        window.setTimeout(updater.poll, updater.errorSleepTime);
    },

};
