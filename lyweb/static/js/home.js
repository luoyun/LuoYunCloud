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
