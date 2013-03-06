from ajax_event.utils import JSONResponse, AjaxEvent, AjaxResponse, AjaxMessage, \
    build_response
from ajax_event.views import url_reverse
from django.contrib import messages
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.http import HttpResponseNotFound
from test_utils.crawler.signals import post_request
from test_utils.mocks import RequestFactory
import json


# Note: Please see the django/tests/regressiontests/urlpatterns_reverse. It's where I'm getting some of the url tests from.
test_data = (
    ('special', NoReverseMatch, [''], {}),
    ('price', '/price/$10/', ['10'], {}),
    ('price2', '/price/$10/', ['10'], {}),
    ('price3', '/price/$10/', ['10'], {}),
    ('product', '/product/chocolate+($2.00)/', [], {'price': '2.00', 'product': 'chocolate'}),
    ('headlines', '/headlines/2007.5.21/', [], dict(year=2007, month=5, day=21)),
    ('windows', r'/windows_path/C:%5CDocuments%20and%20Settings%5Cspam/', [], dict(drive_name='C', path=r'Documents and Settings\spam')),
    )
    
class TestAjaxEvent(TestCase):
    fixtures = ['authtestdata.json']

    def test_ajax_content(self):
        """
        Tests that our basic encoding is sane.
        """
        test_response = AjaxEvent('TestItem','I am a Test')
        self.failUnlessEqual(str(test_response), """{"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}""")

    def test_array_payload(self):
        test_response = AjaxEvent('TestItem',['I am a Test','1'])
        self.failUnlessEqual(str(test_response), """{"type": "TestItem", "djangoPayload": true, "payload": ["I am a Test", "1"]}""")

    def test_nested_payload(self):
        test_response = AjaxEvent('TestItem','I am a Test')
        test_nested = AjaxEvent('TestItem',test_response)
        self.failUnlessEqual(str(test_nested), """{"type": "TestItem", "djangoPayload": true, "payload": {"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}}""")

    def test_nested_multi_payload(self):
        test_response = [AjaxEvent('TestItem','I am a Test'),AjaxEvent('TestItem','I am a Test')]
        test_nested = AjaxEvent('TestItem',test_response)
        self.failUnlessEqual(str(test_nested), """{"type": "TestItem", "djangoPayload": true, "payload": [{"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}, {"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}]}""")

    def test_json_response(self):
        """
        Tests that the JSONResponse looks ok.
        Tests that multiple items are encoded as an array.
        """
        payload = AjaxEvent('TestItem','I am a Test')
        test_response = JSONResponse(payload)
        self.failUnlessEqual(str(test_response), """Content-Type: application/json\n\n{"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}""")

    def test_json_response_array(self):
        """
        Tests that the JSONResponse works when using an array of data.
        """
        payload = []
        payload.append(AjaxEvent('TestItem','I am a Test'))
        payload.append(AjaxEvent('TestItem','I am a Test'))
        test_response = JSONResponse(payload)
        self.failUnlessEqual(str(test_response), """Content-Type: application/json\n\n[{"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}, {"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}]""")

    def test_ajax_event(self):
        """
        Tests that the AjaxResponse correctly has one over-arching "Response" item, with everything
        else stuff into the payload as individual items.
        """
        payload = []
        payload.append(AjaxEvent('TestItem','I am a Test'))
        payload.append(AjaxEvent('TestItem','I am a Test'))
        test_response = AjaxResponse(payload)
        self.failUnlessEqual(str(test_response), """Content-Type: application/json\n\n{"type": "Response", "djangoPayload": true, "payload": [{"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}, {"type": "TestItem", "djangoPayload": true, "payload": "I am a Test"}]}""")

    def test_ajax_message(self):
        """
        Test that messages encode nicely when we package them into an AjaxMessage()
        """
        request_factory = RequestFactory()
        auth_result = request_factory.login(username='testclient', password='password')
        self.failUnlessEqual(auth_result, True, "Assert that our test client can log in.")

        request = request_factory.request()
        messages.add_message(request,messages.INFO,'Testing')

        test_response = AjaxMessage(messages.get_messages(request))
        self.failUnlessEqual(str(test_response), """{"type": "Messages", "djangoPayload": true, "payload": [{"type": "MessageItem", "djangoPayload": true, "payload": " <li class=\\"info message-item ui-corner-all\\">\\n\\t<div class=\\"icon\\"></div>Testing\\n</li>"}]}""")

    def test_build_response(self):
        """
        Test the buid_response shortcut function, which automatically appends messages and accepts an arguments list of `AjaxContent` as additional parameters.
        """
        request_factory = RequestFactory()

        auth_result = request_factory.login(username='testclient', password='password')
        self.failUnlessEqual(auth_result, True, "Assert that our test client can log in.")

        request = request_factory.request()
        messages.add_message(request,messages.INFO,'Testing')

        test_response = build_response(request)

        self.failUnlessEqual(str(test_response), """Content-Type: application/json\n\n{"type": "Response", "djangoPayload": true, "payload": [{"type": "Messages", "djangoPayload": true, "payload": [{"type": "MessageItem", "djangoPayload": true, "payload": " <li class=\\"info message-item ui-corner-all\\">\\n\\t<div class=\\"icon\\"></div>Testing\\n</li>"}]}]}""")


    def test_complex_payload(self):
        events = []
        events.append(AjaxEvent('CartRemove',
            # See also core/context_processors.py : favorites()
            { 
                'cart_item': { 
                    'pk' : 5 
                }, 
                'cart': { 
                    'total_price' : 9.99, 
                    'total_qty': 3
                } 
            } 
        ))
        
        request_factory = RequestFactory()
        request = request_factory.request()
        build_response(request,*events)
    
    def test_build_response_namespace(self):
        """
        Tests that our optional namespace gets captured if it's part of the post variables.
        """
        request_factory = RequestFactory()

        auth_result = request_factory.login(username='testclient', password='password')
        self.failUnlessEqual(auth_result, True, "Assert that our test client can log in.")

        request = request_factory.post('',{"namespace" : "test-namespace"})
        messages.add_message(request,messages.INFO,'Testing')

        test_response = build_response(request)

        self.failUnlessEqual(str(test_response), """Content-Type: application/json\n\n{"type": "Response", "namespace": "test-namespace", "djangoPayload": true, "payload": [{"type": "Messages", "djangoPayload": true, "payload": [{"type": "MessageItem", "djangoPayload": true, "payload": " <li class=\\"info message-item ui-corner-all\\">\\n\\t<div class=\\"icon\\"></div>Testing\\n</li>"}]}]}""")

#
#        request = HttpRequest()
#        messages.add_message(request,messages.INFO,'Testing')
#
#        payload = []
#        test_response = AjaxMessage(messages.get_messages())
#        self.failUnlessEqual(str(test_response), """ WOOT """)
    
class DjangoAjaxUrlTests(TestCase):
    urls = 'ajax_event.tests.urls'

    def test_urlpattern_reverse(self):
        for name, expected, args, kwargs in test_data:
            # Prepare our data by jsonifying it - this is how javascript clients should be transmitting information.
            args_json = json.dumps(args)
            kwargs_json = json.dumps(kwargs)
            # Simulate a request with our json-encoded parameters - note: we don't actually post to the url specified.
            # Instead, we pass the request directly to the view.
            rf = RequestFactory()
            post_request = rf.post('', {'djangoajax_args': args_json, 'djangoajax_kwargs': kwargs_json })
            
            response = url_reverse(post_request, name)
            # If there is no reverse match, we return an HttpResponseNotFound
            if expected is NoReverseMatch: 
                self.assertEquals(HttpResponseNotFound, type(response))
            else:
                self.assertEqual(expected, response.content)
            
#            try:
#                got = reverse(name, args=args, kwargs=kwargs)
#            except NoReverseMatch, e:
#                self.assertEqual(expected, NoReverseMatch)
#            else:
#                self.assertEquals(got, expected)
#    
