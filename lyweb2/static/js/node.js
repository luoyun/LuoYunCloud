var nodeListUpdater = {

    errorSleepTime: 5000,

    poll: function() {
        $.ajax({url: "/node/dynamic_list", type: "GET",
                success: nodeListUpdater.onSuccess,
                error: nodeListUpdater.onError});
    },

    onSuccess: function(response) {
        $("#node-main").html(response);
        window.setTimeout(nodeListUpdater.poll, 0);
    },

    onError: function(response) {
        window.setTimeout(nodeListUpdater.poll,
                          nodeListUpdater.errorSleepTime);
    },

};
