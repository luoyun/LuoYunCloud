function HanNumber(n) {

    switch (n) {
    case 0 : return "〇";
    case 1 : return "一";
    case 2 : return "二";
    case 3 : return "三";
    case 4 : return "四";
    case 5 : return "五";
    case 6 : return "六";
    case 7 : return "七";
    case 8 : return "八";
    case 9 : return "九";
    case 10 : return "十";
    }
}



// 更新标题 , YM1 = YLinux Markup 1
function YM1UpdateH () {

    function humanH1 (index) {
        if (index < 11) {
            return HanNumber(index);
        } else if (index < 100) {
            return HanNumber( parseInt( index / 10 ) ) + HanNumber( index % 10 );
        } else {
            return index;
        }
    }

    var h1index = 0;
    var h2index = 0;
    var h3index = 0;

    $(".markup1 h1, .markup1 h2, .markup1 h3").each( function (index) {

        tagName = $(this)[0].tagName;
        text = $(this).text();

        if ( tagName == "H1" ) {

            h1index += 1;
            h2index = 0;  // 新的 H1 区域,将 H2 计数清零
            h3index = 0;
            //newtext = humanH1(h1index) + "、 " + text;
            newtext = h1index + ". " + text;
            $(this).text( newtext );

        } else if ( tagName == "H2" ) {

            h2index += 1;
            h3index = 0;
            newtext = h1index + "." + h2index + " " + text;
            $(this).text( newtext );

        } else if ( tagName == "H3" ) {

            h3index += 1;
            newtext = h1index + "." + h2index + "." + h3index + " " + text;
            $(this).text( newtext );
        }

    });
}


$(document).ready( function () {
    YM1UpdateH();
})
