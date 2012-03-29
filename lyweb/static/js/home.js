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

function InstanceLogoHover2() {
    $(".instance .logo").each( function (index) {

        $obj = $(this);

        //var c = $obj.parent().find('.ip').html();
        var c = $obj.parent().find('.hide').html();

        var qtip_my = 'bottom left';
        var qtip_at = 'top right';

        var r = index % 5;

        if ( r == 4 || r == 3 ) {
            qtip_my = 'bottom right';
            qtip_at = 'top left';
        } else if ( r == 2 ) {
            qtip_my = 'bottom center';
            qtip_at = 'top center';
        }

        $obj.qtip({
            content: c,
            show: 'mouseover',
            hide: 'mouseout',
            style: {
            },
            position: {
                 my: qtip_my, at: qtip_at
            },
            show: {
                //effect: true,
                //delay: 200,
            },
            suppress: true, // hide default title
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
