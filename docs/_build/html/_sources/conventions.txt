================
Conventions & Tips
================

Javascript
--------------

Sometimes when you add content that you've fetch via ajax, it comes completely vanilla. It's the necessary to either `progressively-enhance <http://en.wikipedia.org/wiki/Progressive_enhancement>`_ it
or simply bind events such as 'click' to the various interface components that came along for the ride.

My convention is to trigger a **'domAdded'** event after you've insert your content into to the dom in such cases.

Another convention I typically use is a controller class in javascript that handles various event bindings and interface needs for things such as comments, paginators, etc. This controller class almost always has
a bindEvents function into which I can optionally pass invidual objects. This allows for me to stick to DRY and allows me to re-use the same event binding code when:

	1. The page is statically loaded.
	2. New content arrives via ajax and it needs to *just work*.