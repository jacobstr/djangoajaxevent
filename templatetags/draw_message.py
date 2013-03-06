from django.template import Library, Node, resolve_variable, TemplateSyntaxError
from django.utils.safestring import mark_safe

register = Library()

@register.inclusion_tag('message.html')
def draw_message(message):
    clear = mark_safe("""
        <span class="message-clear"><a href="#" onclick="jQuery(this).closest('.message-item').remove()">Clear</a></span>
        """)
    return { "clear" : clear, "message": message}
