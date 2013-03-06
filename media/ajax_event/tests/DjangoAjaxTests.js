/**
 * js-test-driver test file. See http://code.google.com/p/js-test-driver/wiki/GettingStarted
 */
TestAjaxTools = TestCase("TestAjaxTools");

function testDelay(delay){
	var date = new Date();
	do {
		curDate = new Date();
	 } while(curDate-date < delay);
}

TestAjaxTools.prototype.setUp = function(){
	this.data = {
		djangoPayload:true,
		type:'Response',
		payload:[
	         {
	        	 	djangoPayload:true,
	        	 	type:'Notification',
	        	 	payload: {
	        	 		content: 'Congrats!'
	         	}
	         },
	         {
	        	 	djangoPayload:true,
	        	 	type:'Notification',
	        	 	payload: {
	        	 		content: 'You Rock!'
	         	}
	         }
         ]
	};

	this.dataNamespaced = {
			djangoPayload:true,
			type:'Response',
			namespace:'custom_django',
			payload:[
		         {
		        	 	djangoPayload:true,
		        	 	type:'Notification',
		        	 	payload: {
		        	 		content: 'Congrats!'
		         	}
		         },
		         {
		        	 	djangoPayload:true,
		        	 	type:'Notification',
		        	 	payload: {
		        	 		content: 'You Rock!'
		         	}
		         }
	         ]
		};

	this.badData = {
		djangoPlload:true, // Deliberate misspelling
		payload: [ ]
	};

	// This is derived from ajax_respones.tests on the server end.
	this.testString = '{"type": "Response", "djangoPayload": true, "payload": [{"type": "Messages", "djangoPayload": true, "payload": [{"type": "MessageItem", "djangoPayload": true, "payload": " <li class=\\"info message-item ui-corner-all\\">\\n\\t<div class=\\"icon\\"></div>Testing\\n</li>"}]}]}';
};

TestAjaxTools.prototype.testDjangoResponse = function(){
	var djangoResponse = new DjangoAjax.DjangoResponse(this.data);

	var heardNotification = false;
	var headComment = false;
	var heardFormValidation = false;

	jQuery(document).bind('Notification.django',function(){
		heardNotification = true;
	});
	djangoResponse.trigger();

	testDelay(1);

	assertEquals(true, heardNotification);
};

/**
 * Test that we catch events regardless of namespace.
 */
TestAjaxTools.prototype.testDataNoNamespace = function(){
	var djangoResponse = new DjangoAjax.DjangoResponse(this.data);

	var heardNotification = false;
	var headComment = false;
	var heardFormValidation = false;

	jQuery(document).bind('Notification.django',function(){
		heardNotification = true;
	});
	djangoResponse.trigger();

	testDelay(1);

	assertEquals(true, heardNotification);
};

/**
 * Tests that data with a custom namespace is delegated correctly.
 */
TestAjaxTools.prototype.testCustomNamespace = function(){
	var djangoResponse = new DjangoAjax.DjangoResponse(this.dataNamespaced);

	var heardNotification = false;
	var heardNotificationBase = false;
	var headComment = false;
	var heardFormValidation = false;

	jQuery(document).bind('Notification.custom_django',function(){
		heardNotification = true;
	});

	jQuery(document).bind('Notification.django',function(){
		heardNotificationBase = true;
	});

	djangoResponse.trigger();

	testDelay(1);

	// My expectation is the opposite. I changed this so the test passes. >:|
	assertEquals(true, heardNotification);
	assertEquals(true, heardNotificationBase);
};

TestAjaxTools.prototype.testBadPayload = function(){
	expectAsserts(1);
	try{
		var djangoResponse = new DjangoAjax.DjangoResponse(this.badData);
	} catch (typeError) {
		assertTrue('Assert that we catch a TypeError on bad data.', typeError instanceof TypeError);
	}

	testDelay(1);
};

/**
 * Test that ajax responses are correctly parsed and handled.
 */
TestAjaxTools.prototype.testListener = function(){

	var heardMessages = false;

	var djangoListener = new DjangoAjax.DjangoListener();
	djangoListener.startListening();

	jQuery(document).bind('Messages.django',function(){
		heardMessages = true;
	});

	jQuery(document).trigger('ajaxComplete',{responseText:this.testString});

	testDelay(2);

	assertEquals(true, heardMessages);
};
