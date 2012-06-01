function InstanceLogoHover() {
    $(".instance .logo").each( function () {
         var $obj = $(this);
         var c = $obj.parent().find('.hide').html();
         $obj.qtip({
            content: c,
            position: {
                 my: 'top center', at: 'bottom center'
            },
            show: {
                effect: true,
                delay: 90,
            }
        });
    });
}


function InstanceStatusHover() {

    $('.instance .status img').each( function (index) {

        $obj = $(this);

        var c = $obj.parent().find('.status-string').html();

        if ( index % 5 != 0 ) {
            var qtip_my = 'center right';
            var qtip_at = 'center left';
        } else {
            var qtip_my = 'center left';
            var qtip_at = 'center right';
        }

        $obj.qtip({
            content: c,
            show: 'mouseover',
            hide: 'mouseout',
            style: { 
                classes: 'ui-tooltip-shadow ui-tooltip-youtube'
            },
            position: {
                 my: qtip_my, at: qtip_at
            },
        });

    });
}


function instance_view_method() {

    var curview = ly_url_get_parameter("view");
    var found = 0;
    if ( curview == "" ) {
        $(".single-choice input:checkbox").each(function(){
            if ( this.value == "self" ) {
                this.checked = true;
            } else {
                this.checked = false;
            }
        });
    } else {
        $(".single-choice input:checkbox").each(function(){
            if ( this.value == curview ) {
                this.checked = true;
                found = 1;
            } else {
                this.checked = false;
            }
        });
    }

    $(".single-choice input:checkbox").click(function(){
        var curval = this.value;
        $(".single-choice input:checkbox").each(function(){
            if ( this.value != curval ) {
                this.checked = false;
            }
        });
        ly_url_set_parameter('view', curval);
    });
}


function Example () {

    $('table td.example:not(:empty)').each( function() {

        var self = this;

        var header = $(self).parents('tr + .optionhead:first td.name').text().replace(': {', '');
        var title = 'Example: ' + ((header) ? header+'.' : '') + $(self).siblings('td:first').text();

        $(self).qtip({
            content: {
                text: $(self).html(),
                title: {
                    text: title
                }
            },
            position: {
                corner: {
                    target: 'leftMiddle',
                    tooltip: 'rightMiddle'
                }
            },
            show: 'click',
            hide: 'unfocus',
            style: {
                border: {
                    width: 5
                },
                tip: {
                    corner: 'rightMiddle'
                },
                name: 'green',
                width: {
                    max: 650,
                    min: 500
                },
                padding: 14
            },
            api: {
                onRender: function()
                {
                    hljs.initHighlightingOnLoad('javascript');
                }
            }
        })
            .html('Example')
            .show();
    }); 
}
