# http://stackoverflow.com/questions/2724383/dry-urls-in-django-javascript
from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse, HttpResponseNotFound
from urlparse import urlparse
import json

def get_args(request):
    """
    Pulls out positional arguments from a request for use with Django's url reversal mechanism.
    """
    return json.loads(request.REQUEST.get('djangoajax_args','[]'))
    
def get_kwargs(request):
    """
    Pulls out kwargs from a request for use with Django's url reversal mechanism.
    """
    return json.loads(request.REQUEST.get('djangoajax_kwargs','{}')) 

def prep_args(request):
    """
    Prepares incoming request data into a format suitable for our url_resolve and url_reverse functions.
    """
    args = get_args(request)
    kwargs = get_kwargs(request)
    
    reverse_args = {}
    if args and len(args):    
        reverse_args['args'] = args
    if kwargs and len(kwargs.items()):
        reverse_args['kwargs'] = kwargs
    
    return reverse_args

def url_reverse(request, url_name):
    """
    Asks Django to reverse a url for us and returns that url as a string.
    """
    reverse_args = prep_args(request)
    try:
        return HttpResponse(reverse(url_name,**reverse_args))
    except:
        return HttpResponseNotFound()

def url_resolve(request, url_name):
    """
    Asks Django to resolve a url for us and returns the response.
    """
    reverse_args = prep_args(request)

    try:
        url = reverse(url_name, **reverse_args)
    except:
        return HttpResponseNotFound()

    view, args, kwargs = resolve(url)

    return view(request, *args, **kwargs)