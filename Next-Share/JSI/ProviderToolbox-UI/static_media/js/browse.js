$(function(){

    // Accordion


    $('.edit').click(function () {
	$(this).siblings(".display").fadeOut(function () {
	    $(this).siblings(".form").fadeIn();
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
	$(selector).append(data).accordion('destroy');
	make_accordion(selector);
    });
}