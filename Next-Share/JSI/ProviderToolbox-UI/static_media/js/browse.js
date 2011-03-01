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

    $('input.cancel').live('click', function (event) {
	event.preventDefault();
	$(this).parent(".form").fadeOut(function () {
	    $(this).siblings(".display").animate({opacity: 1.0}, 500, function () {
		$(this).css('z-index', 1);
     		$(this).siblings('.form').css('z-index', 0);
	    });
	});
    });
    
    $('.update').live('click', function () {
	var path = $(this).attr('path');
	$.get('/update_feed/?path='+path, function (data) {
            alert("done updating "+path);
	});
    });
    
    $('.delete').live('click', function () {
	var path = $(this).attr('path');
	alert(path);
	if (confirm("Item will be permanently removed, there is no restore!")) {
	    $.get('/delete_feed/?path='+path, function (data) {
		window.location.reload();
	    });
	}
    });

    $('form').live('submit', function (event) {
	if ($(this).find("input[name='should_cascade']").val() == 'True') {
            if (!confirm("Changes will be applied in cascade to all children.")) {
		event.preventDefault();
            }
	}
    });

    $('#tabs').tabs();

    add_list('', '#accordion')
});

function make_accordion(selector) {
    $(selector).accordion({ header: "h3", 
			    collapsible: true,
			    autoHeight: false});
    //if (window.location.href.indexOf('#posted') < 0) {
    $(selector+" h3:first a").click();
    //}
};

function add_list (dir, accordion, tabs) {
    $(tabs).tabs();

    $.get('/list_dir/', {'dir': dir}, function (data) {
	$(accordion).accordion('destroy').append(data);
	make_accordion(accordion);
	
	$("[class*='tabbed']").tabs();
    });
}