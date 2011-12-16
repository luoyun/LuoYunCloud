// Switch between Menu Element
function lyDomainMenuElementSwitch () {

    $("#lyentry .menu .normal").click( function() {
        var curelement = $(this);
        var cid = $(this).attr("id").replace(/^c(\d+).*$/, '$1');
        var curl = "/domain/catalog_ajax/" + cid + "/";
        //alert(curl);
        $.ajax({
            url: curl,
            success: function(data) {
                curelement.addClass("current");
                curelement.siblings().removeClass("current");
                $("#lyentry .close-main").html(data);
            }
        });
    });
}