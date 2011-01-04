$(function(){

    // Accordion

    $('.edit').live('click', function () {
	$(this).siblings(".display").animate({opacity: 0}, 500, function () {
	    $(this).siblings(".form").fadeIn(function () {
     	  $(this).css('z-index', 1);
     	  $(this).siblings('.display').css('z-index', 0);
	    });
	});
	
    });

    $('#tabs').tabs();

    add_list('', '#accordion')
});

function make_accordion(selector) {
    $(selector).accordion({ header: "h3", 
			    collapsible: true,
			    autoHeight: false});
    if (window.location.href.indexOf('#posted') < 0) {
	$(selector+" h3:first a").click();
    }
};

function add_list (dir, selector) {
    $.get('/list_dir/', {'dir': dir}, function (data) {
      $(selector).accordion('destroy').append(data);
      make_accordion(selector);
    });
}