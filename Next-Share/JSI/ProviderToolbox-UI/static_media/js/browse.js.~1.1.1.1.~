$(function(){

    // Accordion
    $("#accordion").accordion({ header: "h3", collapsible: true});

    if (window.location.href.indexOf('#posted') < 0) {
	$("#accordion h3:first a").click();
    }

    $('.edit').click(function () {
	$(this).siblings(".display").fadeOut(function () {
	    $(this).siblings(".form").fadeIn();
	});
	
    });

    $('#tabs').tabs();
});