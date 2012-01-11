// lyImageDefaultSelectUploadFile({{ addmethod }})
function lyImageDefaultSelectUploadFile (addmethod) {
    // Error
    //alert(addmethod);
    $("#id_addmethod").get(0).selectedIndex = addmethod - 1;
    for (i=1; i<= 2; i++) {
        if (i.toString() == addmethod) {
            $("#addmethod" + addmethod).css("display", "block");
        } else {
            $("#addmethod" + i).css("display", "none");
        }
    }
}



// lyImageSelectUploadMethod
function lyImageSelectUploadFile () {

    $("#id_addmethod").change( function () {
        v = $(this).val();
        for (i=1; i<= 2; i++) {
            if (i.toString() == v) {
                $("#addmethod" + v).css("display", "block");
            } else {
                $("#addmethod" + i).css("display", "none");
            }
        }
    });


    //$("#id_filename").change( function () {
    //    v = $(this).find("option:selected").text();
    //    $("#id_name").val(v);
    //});
}


// Bind some event on catalog element
function lyImageCatalogEvent(catalogs) {
    //alert(catalogs.toString());
    $("#catalogs li").hover(
        function () {
            var cur = $(this).attr("id");

            $("#" + cur).addClass("hover");

            for ( i = 0; i < catalogs.length; i++)
            { 
                if ( cur != catalogs[i] ) {
                    $("#" + catalogs[i]).removeClass("hover");
                }
            }
        },
        function () {
            //action for move out
        }
    );

    $("#catalogs li").click( function() {
        var cid = $(this).attr("id").replace(/^c(\d+).*$/, '$1');
        var curl = "/image/catalog_ajax/" + cid + "/";
        //alert(curl);
        $.ajax({
            url: curl,
            success: function(data) {
                //$(this).addClass("done");
                $("#image-main-right").html(data);
            }
        });
    });
}


// Switch between Menu Element
function lyImageMenuElementSwitch () {

    $("#lyentry .menu .normal").click( function() {
        var curelement = $(this);
        var cid = $(this).attr("id").replace(/^c(\d+).*$/, '$1');
        var curl = "/image/catalog_ajax/" + cid + "/";
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


function lyImageHover (id) {
    $(id).hover(
        function () {
            $(this).addClass("hover");
            $(this).find(".image-action").css("display", "block");
        },
        function () {
            $(this).removeClass("hover");
            $(this).find(".image-action").css("display", "none");
        }
    );
}