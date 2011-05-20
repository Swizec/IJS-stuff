$(function(){

    // Accordion

    $('.edit').live('click', function () {
	var $edit = $(this);
	$(this).siblings(".display").animate({opacity: 0}, 500, function () {
	    $(this).siblings(".form").fadeIn(function () {
     		$(this).css('z-index', 1)
     		    .siblings('.display').css('z-index', 0);
		$edit.fadeOut();
	    });
	});
    });

    $('input.cancel').live('click', function (event) {
	event.preventDefault();
	$(this).parent(".form").fadeOut(function () {
	    $(this).siblings(".display").animate({opacity: 1.0}, 500, function () {
		$(this).css('z-index', 1)
		    .siblings('.form').css('z-index', 0)
		    .siblings('.edit').fadeIn();
	    });
	});
    });

    $('.update').live('click', function (event) {
	var $this = $(this);
	var $meta = $this.parent().parent().parent();

	$('#'+$meta.attr('id')+'-inner').accordion('destroy').html('');

	var path = $meta.attr('dir');
	blockUI("Updating "+path);
	$.ajax({
	    url: '/update_feed/?path='+path,
	    dataType: 'text',
	    success: function (data) {
		$.unblockUI();

		add_list(path, $meta.attr('tabs'), '#'+$meta.attr('id'));
	    },
	});
    });

    $('.delete').live('click', function () {
	var $this = $(this);
	var path = $this.attr('path');
	var item = $this.attr('item');
	if (confirm("Item will be permanently removed, there is no restore!")) {
	    blockUI("Removing item");
	    $.get('/delete_item/?path='+path+'&item='+item, function (data) {
		var $accordion = $this.parents('h3').parent().parent();
		$this.parents('h3').parent().remove();
		$accordion.accordion('destroy');
		make_accordion('#'+$accordion.attr('id'));
		$.unblockUI();
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
			    autoHeight: false,
			    change: function (event, ui) {
				var $accordion = ui.newHeader.parent();
				if ($accordion.attr('listed') == 'false') {
				    $accordion.attr('listed', 'true');
				    add_list($accordion.attr('dir'),
					     '#'+$accordion.attr('id')+'-inner',
					     $accordion.attr('tabs'));
				}
			    }});

    $(selector+" h3:first a").click();
};

function blockUI(s) {
    $.blockUI({
	message: s,
	css: {
	    border: 'none',
	    padding: '15px',
	    backgroundColor: '#000',
	    '-webkit-border-radius': '10px',
	    '-moz-border-radius': '10px',
	    opacity: .5,
	    color: '#fff'
	} });
}

function add_list (dir, accordion, tabs) {
    $(tabs).tabs();

    $.get('/list_dir/', {'dir': dir}, function (data) {
	$(accordion).accordion('destroy').append(data);
	make_accordion(accordion);

	$("[class*='tabbed']").tabs({
	    select: function (event, ui) {
		var tab = ui.tab.hash.split('-');
		var $panel = $("#"+ui.panel.id);
		var path = $panel.attr('path');
		if (tab[tab.length-1] == 'view') {
		    blockUI('Fetching atom feed');

		    $.ajax({
			url: '/fetch_feed/?path='+$panel.attr('path'),
			dataType: 'text',
			success: function (data) {
			    $.unblockUI();
			    var $pre = $panel.find('.pre');
			    if ($pre.size() > 0) {
				$pre.html('<pre>'+htmlentities(data)+'</pre>');
			    }else{
				$panel.append(
				    $('<div></div>').addClass('pre')
					.html('<pre>'+htmlentities(data)+'</pre>')
					.css('overflow', 'auto'));
			    }
			},
			error: function (data) {
			    $.unblockUI();
			    alert("Sorry, something went wrong.");
			}
		    });
		}else if (tab[tab.length-1] == 'torrent') {
		    blockUI('Fetching torrent file');

		    $.ajax({
			url: '/fetch_torrent/?path='+$panel.attr('path'),
			dataType: 'text',
			success: function (data) {
			    $.unblockUI();
			    var $pre = $panel.find('.pre');
			    if ($pre.size() > 0) {
				$pre.html('<pre>'+htmlentities(data)+'</pre>');
			    }else{
				$panel.append(
				    $('<div></div>').addClass('pre')
					.html('<pre>'+htmlentities(data)+'</pre>')
					.css('overflow', 'auto'));
			    }
			},
			error: function (data) {
			    $.unblockUI();
			    alert("Sorry, something went wrong.");
			}
		    });
		}else if (tab[tab.length-1] == 'preview') {
		    if ($panel.find('iframe').size() < 1) {
			$panel.append($('<iframe></iframe>')
				      .attr('src', '/preview/?path='+$panel.attr('path'))
				      .attr('width', 620)
				      .attr('height', 520));
		    }
		}
	    }
	});
    });
}

function metafy_accordion(dir, accordion, tabs) {
    $(tabs).tabs();

    $(accordion)
	.attr('dir', dir)
  	.attr('tabs', tabs)
	.attr('listed', 'false');
}

function htmlentities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}