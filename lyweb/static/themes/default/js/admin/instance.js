function admin_instance_search( url_template ) {
    $(".instance-search input").keyup(function(){

		txt=$(this).val();

		var url = url_template.replace('REPLACEOBJ', txt);

		clearTimeout($(this).data('timeId'));

		var timeoutId = setTimeout(function() {
			$.get(url,function(data){
				$("#instance-list").html(data);
			}); }, 300);

		$(this).data('timeId', timeoutId);
    });
}
