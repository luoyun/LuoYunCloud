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

