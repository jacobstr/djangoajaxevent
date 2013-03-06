from django.db import models
from django.http import HttpResponse
from django import template
from django.contrib import messages
from django.utils.functional import Promise
from django.utils.encoding import force_unicode
from django import forms
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.forms.formsets import BaseFormSet
try:
    from simplejson import JSONEncoder, dumps
except ImportError:
    try:
        from json import JSONEncoder, dumps
    except ImportError:
        from django.utils.simplejson import JSONEncoder, dumps

import string
# Create your models here.

def build_response(request, *args):
    """
    Convenience wrapper to build a top-level :class:`AjaxResponse`. Automatically adds message events. Other :class:`AjaxEvent`
    may be provided as positional arguments.

    :param request: A Django request object. Messages are automatically processed and corresponding messages created.
    :param args: Additional AjaxEvents provided as positional arguments.

    """
    final_args = list(args)
    kwargs = {}
    if request is not None:
        final_args.append(AjaxMessage(messages.get_messages(request)))
    # Pull the namespace from the post vars if it's present.
    # This is useful if you want to namespace the response on a per-form basis.
    if request.POST.get('namespace',None) is not None:
        kwargs['namespace'] = request.POST['namespace']
    return AjaxResponse(final_args,**kwargs)

class JSONResponse(HttpResponse):
    """
    Sets content_type as application/json.
    """
    def __init__(self,  content, *args, **kwargs):
        if not kwargs.get('content_type',False):
            kwargs['content_type'] = 'application/json'

        # Kind of fugly. json encode
        content = dumps(content, cls=PayloadEncoder)

        # Note: all args should be json encodable, things such as response code and type are not delegated back down.
        super(JSONResponse, self).__init__(content, *args, **kwargs)

class AjaxResponse(JSONResponse):
    """
    Sets content_type as application/json. Also establishes a level of indirection for future customizations.
    """
    def __init__(self,  content, *args, **kwargs):
        # Wrap all responses in AjaxEvent of Response.
        if kwargs.has_key('namespace'):
            namespace = kwargs.pop('namespace')
        else:
            namespace = None

        content = AjaxEvent('Response', content, namespace=namespace)

        # Note: all args should be json encodable, things such as response code and type are not delegated back down.
        super(AjaxResponse, self).__init__(content, *args, **kwargs)

class AjaxEvent(object):
    """
    Represents a single event. Pass this off to an AjaxResponse in order to have the payload make it's way to your client side.
    """
    def __init__(self, type, payload, namespace=None):
        self.type = type
        self.payload = payload
        self.namespace = namespace

    def __str__(self):
        return dumps(self.to_payload(), cls=PayloadEncoder)

    def to_payload(self):
        payload = {
            'djangoPayload': True,
            'type': self.type,
            'payload': self.payload
        }
        if self.namespace:
            payload.update({"namespace" : self.namespace})

        return payload

class AjaxMessage(AjaxEvent):
    """
    An AjaxEvent that's customized for use with django.contrib.messages. It will trigger a **Message** event
    with associated **MessageItems** for each message django created.
    """
    tag_lib = 'draw_message'

    def __init__(self, messages, tag_lib=None):
        """
        Draws django.contrib.messages`messages` as ajax payload items.
        `tag_lib` is a tag_library to be loaded that provides a draw_message function to draw a message.
        """
        assert tag_lib or self.tag_lib
        tag_lib = tag_lib or self.tag_lib

        # Use template substitutions so I don't have to escape `%` ( old style) or `{` (string.format())
        template_string = string.Template("""{% load $tag_lib %} {% draw_message message %}""").substitute( { "tag_lib" : tag_lib})
        template_item = template.Template(template_string)


        payload  = []
        for message in messages:
            payload.append(
                AjaxEvent(
                    'MessageItem',
                    template_item.render(template.Context({'message':message}))
                )
            )
        super(AjaxMessage, self).__init__('Messages',payload)

class LazyEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return obj

class PayloadEncoder(LazyEncoder):
    def __init__(self, *args, **kwargs):
        # Ensure our keys are sorted the way we specify
        if kwargs.get('sort_keys',None) is None:
            kwargs['sort_keys'] = False
        return super(PayloadEncoder, self).__init__(*args, **kwargs)

    def default(self,obj):
        if hasattr(obj,'to_payload'):
            return obj.to_payload()
        else:
            return super(PayloadEncoder,self).default(obj)

# From Alex Gaynor's ajax_validation project.
# http://github.com/alex/django-ajax-validation
def validate(request, *args, **kwargs):
    if kwargs.has_key('form'):
        form = kwargs.pop('form')
    else:
        form_class = kwargs.pop('form_class')
        defaults = {
            'data': request.POST
        }
        extra_args_func = kwargs.pop('callback', lambda request, *args, **kwargs: {})
        kwargs = extra_args_func(request, *args, **kwargs)
        defaults.update(kwargs)
        form = form_class(**defaults)

    if form.is_valid():
        data = {
            'valid': True,
        }
    else:
        # if we're dealing with a FormSet then walk over .forms to populate errors and formfields
        if isinstance(form, BaseFormSet):
            errors = {}
            formfields = {}
            for f in form.forms:
                for field in f.fields.keys():
                    formfields[f.add_prefix(field)] = f[field]
                for field, error in f.errors.iteritems():
                    errors[f.add_prefix(field)] = error
            if form.non_form_errors():
                errors['__all__'] = form.non_form_errors()
        else:
            errors = form.errors
            formfields = dict([(fieldname, form[fieldname]) for fieldname in form.fields.keys()])

        # if fields have been specified then restrict the error list
        if request.POST.getlist('fields'):
            fields = request.POST.getlist('fields') + ['__all__']
            errors = dict([(key, val) for key, val in errors.iteritems() if key in fields])

        final_errors = {}
        for key, val in errors.iteritems():
            if '__all__' in key:
                final_errors[key] = val
            elif not isinstance(formfields[key].field, forms.FileField):
                html_id = formfields[key].field.widget.attrs.get('id') or formfields[key].auto_id
                html_id = formfields[key].field.widget.id_for_label(html_id)
                final_errors[html_id] = val
        data = {
            'valid': False or not final_errors,
            'errors': final_errors,
        }

    return AjaxEvent('Validation',data)
