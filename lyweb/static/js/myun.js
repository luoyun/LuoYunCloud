function myunPieHover() {
    $(".myun-pie-item").hover(
	function() {
	    $(this).children(".desc").addClass("myun-pie-item-current");
	    //$(this).find(".myun-pie-item-hover").show();
	},
	function() {
	    $(this).children(".desc").removeClass("myun-pie-item-current");
	    $(this).find(".myun-pie-item-hover").html('');
	});
}


function pieHover(event, pos, obj) 
{
    if (!obj)
        return;
    percent = parseFloat(obj.series.percent).toFixed(2);
    var $dynamic_obj = $(this).parent().find('.myun-pie-item-hover')
    //alert ( $dynamic_obj );
    $dynamic_obj.html('<span style="color: '+obj.series.color+'">'+obj.series.label+' ('+percent+'%)</span>');
}

function pieClick(event, pos, obj) 
{
    if (!obj)
        return;
    percent = parseFloat(obj.series.percent).toFixed(2);
    alert(''+obj.series.label+': '+percent+'%');
}

function lyShowPie( tag, data ) {

    $.plot( $(tag), data,
	    {
		series: {
		    pie: {
			show: true,
			radius: 1,
			label: {
			    show: true,
			    radius: 3/5,
			    formatter: function(label, series) {
				return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'+label+'<br/>'+Math.round(series.percent)+'%</div>';
			    },
			    background: { opacity: 0.5 }
			}
		    }
		},
		legend: {
		    show: false
		},
		grid: {
		    hoverable: true,
		    clickable: true
		}
	    });

    $(tag).bind("plothover", pieHover);
//    $(tag).bind("plotclick", pieClick);
}



function instance_isprivate_toggle ( obj, ID ) {


    var check = this.checked;

    if ( $(obj).attr("checked") == "checked" )
	check_value = 'true';
    else
	check_value = 'false';

    var URL = "/instance/" + ID + "/set_private?isprivate=" + check_value;

    $.ajax({
        url: URL,
        type: 'GET',
        success: function (data) {
	    this.checked = !check;
        }
    });

};
