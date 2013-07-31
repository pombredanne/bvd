/**

* BVD v1.0

* Copyright (c) 2012 Voltage Security
* All rights reserved.

* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions
* are met:
* 1. Redistributions of source code must retain the above copyright
*    notice, this list of conditions and the following disclaimer.
* 2. Redistributions in binary form must reproduce the above copyright
*    notice, this list of conditions and the following disclaimer in the
*    documentation and/or other materials provided with the distribution.
* 3. The name of the author may not be used to endorse or promote products
*    derived from this software without specific prior written permission.
* 
* THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
* IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
* OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
* IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
* INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
* NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
* DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
* THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
* THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

**/

var BVD = BVD || {};
BVD.widget_map = {};

/**
	Class to create and return a widget object, inherited from JQuery's $("<div></div>").  
	
	A widget object is an icon on the screen representing
	a Jenkins build, that has either a success, failed, or down status
	
	The object returned can be later manipulated via helper methods
	to change state, set its position on the page, set its size, etc.
	
	@param job_name String 
*/
var Widget = function(hostname, jobname, displayname, status, id, counter, readonly, background_img){

	this.make_success = function() {
		this.addClass('success');
		this.removeClass('error');
		this.removeClass('down');
		this.removeClass('unstable');
	}
	
	this.make_failure = function() {
		this.addClass('error');
		this.removeClass('success');
		this.removeClass('down');
		this.removeClass('unstable');
	}
	
	this.make_down = function() {
	    this.addClass('down');
	    this.removeClass('success');
	    this.removeClass('error');
	    this.removeClass('unstable');
	    
	}
	
	this.make_unstable = function () {
	    this.addClass('unstable');
	    this.removeClass('success');
	    this.removeClass('error');
	    this.removeClass('down');
	}
	
	this.set_size = function(count, prev_left, prev_top, counter) {
		var size = String(0.5/Math.log(count));
		size = size.substring(2,5);
		size = (size.indexOf("0") == 0) ? size.substring(1,3) : size;	
		size = parseInt(size);
		
		var mod = 6;
		
		if (count <= 15) {mod = 5;}
		else if (count >= 50) {mod = 7;}

		var left = prev_left + size + 50;;
		
		left = (counter % mod == 0 && left > ($(window).width() - 300)) ? 0 : (counter == 0) ? 0 : left;


		var top = (counter % mod == 0) ? (counter == 0) ? 0 : prev_top + size + 50  : prev_top
		
		this.css('height',size+'px');
		this.css('width',size+'px');
		this.css('left',left+'px');
		this.css('top',top+'px');
	}
	
	this.set_status = function(status) {
	    this.status = status;
	    switch (status) {
    		case 'SUCCESS':
    			this.make_success();
    			this.css('background-image', this.background_img);
    			break;
    		case 'FAILURE':
    			this.make_failure();
    			break;
    		case 'DOWN':
    		    this.make_down();
    		    break;
    		case 'UNSTABLE':
        	    this.make_unstable();
        	    break;
    		default:
    			this.make_success();
    	}
	}

    this.make_icon = function (self) {
    	$icon = $('<div>&nbsp;</div>');
		$icon.attr('class','icon');
		this.append($icon);
		
		$menu = $('<div></div>');
		$ul = $('<ul></ul>');
		
		$li = $('<li></li>');
		$li.html('Remove Job');
		$li.attr('class','menu-item');
		
		$li.hover(function(){
			$(this).addClass('menu-on');
		},function(){
			$(this).removeClass('menu-on');
		});
		
		$li1 = $('<li></li>');
		$li1.html('View Job');
		$li1.attr('class','menu-item');
		
		$li.click(function(){
			self.off('click');
			data = {};
			data['pk'] = self.pk;
			BVD.utils.do_ajax('post',BVD.data.get_url('remove'),data,function(data){
				//remove the element from the widget map
				var $widgets = BVD.widget_map[self.hostname];
				var index = 0;
				var $widget;
				for (i =0; i < $widgets.length; i++) {
					if ($widgets[i].pk == self.pk) {
						index = i;
						$widget = $widgets[i];
						break;
					}
				}
				$widgets.splice(index,1);
				$widget.remove();
				Widget.render.refresh_grid();
				BVD.widget_map[self.hostname] = $widgets;
				BVD.utils.set_size_of_widgets($(".widget").length + 3);
				BVD.utils.save_widgets();
				setTimeout(500,function(){
					var poll = new Poll('/pull/pull_jobs/');
					poll.ajax();
				});
			});
		});
		
		$li1.hover(function(){
			$(this).addClass('menu-on');
		},function(){
			$(this).removeClass('menu-on');
		});
		
		$li1.click(function(){
			window.location.href = self.hostname + '/job/' + self.jobname;
		});

        $li2 = $('<li></li>');
        $li2.html('Edit Widget');
        $li2.attr('class', 'menu-item');

        $li2.hover(function() {
            $(this).addClass('menu-on');
        }, function() {
            $(this).removeClass('menu-on');
        });

        $li2.click(function() {
            var id = 'edit_widget';
            var $modal;
            var opts = {
                width: 400,
                height: 410,
                autoOpen: true,
                title: "Edit Widget: '" + self.displayname + "'",
                resizable: false,
                modal: true,
                beforeClose: function() {
                    $("#edit_widget_dialog").remove();
                },
            }
            $modal = BVD.modal_factory(BVD.data.get_url('modal', '?template=edit_widget&widget_id='+self.pk), id, opts);
            return false;
        });

		$li3 = $('<li></li>');
		$li3.html('Edit Image');


		$li3.hover(function(){
			$(this).addClass('menu-on');
		},function(){
			$(this).removeClass('menu-on');
		});

		$li3.click(function(){
			id = 'edit_image';
			var $modal;
	
			var opts =      {
        		width : 400,
    			height : 225,
        		autoOpen: true,
        		title: 'Edit Image',
        		resizable : false,
        		modal : true
    		}
    
    		$modal = BVD.modal_factory(BVD.data.get_url('modal','?template=edit_image&widget_id='+self.pk), id, opts);
    		return false;
		});
		
		$ul.append($li);
		$ul.append($li1);
        $ul.append($li2);
		$ul.append($li3);
		
		$menu.append($ul);
		
		$icon.append($menu);
		
		$icon.hover(function(){
			$(this).children(0).toggle();
			self.on('click',function(){
				return;
			});
		},function(){
			$(this).children(0).toggle();
			self.on('click',function(){

        		window.location.href = self.hostname + '/job/' + self.jobname;
        	});
		});
		
		$marquee = $('<div></div>');
		$marquee.html(this.displayname);
    }
	
	this.init = function() {
	    
	    $.extend(this,$("<div></div>"));
	    
	    var self = this;
	    
	    this.pk = id;
	    this.hostname = hostname;
        this.jobname = jobname;
        this.status = status;
        this.displayname = displayname;
        this.icon = background_img;
        this.background_img = 'url(/static/images/'+background_img+')';
        
        this.attr('id','wdg'+id);
        this.id = this.attr('id');

        if (!eval(readonly)) {
        	this.make_icon(self);
        } else {
        	$marquee = $('<div></div>');
			$marquee.html(this.displayname);	
        }
        
		this.attr('class','widget');

        $marquee.attr('class','marquee');
        $marquee.on('click', function() {
            window.location.href = self.hostname + '/job/' + self.jobname;     
        });
		this.append($marquee);
		this.set_status(this.status);
		
		Widget.render.add_widget(this);

    }	
    
    this.init();
};
