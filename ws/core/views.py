import os
import re
import markdown
import frontmatter
import json
from pathlib import Path

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from .models import Item, Tag

def home(request, msg=None):
    """Home view

    Parameters
    ----------
    request: django.http.request

    msg: str
        A mark_safed string to display in the main
    """

    return render(request, 'core/items.html', {
        'tags': Tag.objects.all().order_by('name').values_list('name', flat=True),
        'msg': msg
    })

def rescan(request):
    """Scan the document repo."""

    # start afresh
    Item.objects.all().delete()
    Tag.objects.all().delete()

    # warning messages
    msg = []

    for path in Path(settings.DOC_REPO).rglob('*.md'):
        try:
            it, tags = Item.create(path)
            it.save()
            it.tags.add(*tags)
        except Exception as exp:
            msg.append(str(exp))
   
    return home(request, msg=mark_safe('<br />'.join(msg)))

@require_http_methods(["GET"])
def search(request):
    """Search for items containing text.

    Parameters
    ----------
    request : django.http.request
        request['tag'] is a tag name, restrict search to this tag
        request['lookfor'] string to look for

    Returns
    -------
    JsonResponse
        {
            'success': bool
            'items': list [(id, title, context), (id, title, context) ...]
            'msg': str
        }
        The msg is only there if there was a problem

        If tag is 'Recipes' then search in all items.

    """

    txt, tag = request.GET['lookfor'], request.GET.get('tag', None)

    if tag and tag not in ('Recipes', 'recent'):
        its = Item.objects.filter(tags__name=tag).order_by('title')
    else:
        its = Item.objects.all().order_by('title')

    items = []
    for it in its:
        found = None

        # found refers to Item, and if we found txt in the body context gives
        # us the string where it was found

        if re.search(txt, it.title, re.IGNORECASE):
            found, context = it, None
        else:
            with open(it.path, 'r') as handle:
                body = frontmatter.load(handle).content
                m = re.search(txt, body, re.IGNORECASE)
                if m:
                    found = it
                    context = f"...{body[max(m.start()-20, 0):min(m.end()+20, len(body))]}..."""
       
        if found:
            items.append([it.id, it.title, context])

    return JsonResponse({
        'success': True,
        'items': json.dumps(items)
    })


@require_http_methods(["GET"])
def items(request):
    """Returns items in given tag

    Parameters
    ----------
    request : django.http.request
        request['tag'] is a tag name, or 'recent'

    Returns
    -------
    JsonResponse
        {
            'success': bool
            'items': list [(id, title), (id, title) ...]
            'msg': str
        }
        The msg is only there if there was a problem

        If tag is 'Recipes' then all items returned.  If tag is 'recent'
        return all items sorted by 'accessed'.

    """

    tag = request.GET['tag']

    if tag == 'Recipes':
        its = Item.objects.all().order_by('title')
    elif tag == 'recent':
        # not None means never accessed has key = (False, None), and False goes
        # first.  Then we reverse if
        its = sorted(
            Item.objects.all(),
            key=lambda ob: (ob.accessed is not None, ob.accessed),
            reverse=True
        )
    else:
        its = Item.objects.filter(tags__name=tag).order_by('title')

    return JsonResponse({
        'success': True,
        'items': json.dumps([(it.id, it.title) for it in its])
    })


@require_http_methods(["GET"])
def tags(request):
    """The tags

    Parameters
    ----------
    request : django.http.request

    Returns
    -------
    JsonResponse
        {
            'success': bool
            'tags': dict (id to name)
            'msg': str
        }
        The msg is only there if there was a problem

    """

    tags = {
        t.id: t.name
        for t in Tag.objects.all().order_by('name')
    }

    return JsonResponse({
        'success': True,
        'tags': json.dumps(tags)
    })



@require_http_methods(["GET"])
def item(request):
    """An item

    Parameters
    ----------
    request : django.http.request
        request['id'] is an item ID

    Returns
    -------
    JsonResponse
        {
            'success': bool
            'title': str
            'created': str (YYYY-MM-DD HH:MM:SS) or None
            'last': str either YYYY-MM-DD HH:MM:SS or 'never'
            'tags': list of tag names
            'filename': str
            'content': html str
            'msg': str
        }
        The msg is only there if there was a problem

    """

    try:
        it = Item.objects.get(pk=json.loads(request.GET['id']))
    except Exception as exp: # pylint: disable=broad-except
        return JsonResponse({'success': False, 'msg': str(exp)})
    
    tags = [t.name for t in it.tags.all()]
    created = timezone.localtime(it.created).strftime("%Y-%m-%d %H:%M") if it.created else None
    last = timezone.localtime(it.accessed).strftime("%Y-%m-%d %H:%M") if it.accessed else 'never'

    # get the content
    with open(it.path, "r", encoding="utf-8") as fh:
        text = frontmatter.load(fh)
        content = markdown.markdown(text.content, extensions=['tables'])

    # save back with correct accessed
    with open(it.path, "w", encoding="utf-8") as fh:
        text['accessed'] = it.accessed = timezone.now()
        fh.write(frontmatter.dumps(text))
        it.save()

    return JsonResponse({
        'success': True,
        'title': it.title,
        'created': timezone.localtime(it.created).strftime("%Y-%m-%d %H:%M")
                   if it.created else None,
        'last': last,
        'tags': json.dumps(tags),
        'filename': os.path.basename(it.path),
        'content': content
    })



@require_http_methods(["GET"])
def delete(request):
    """Delete an item

    Parameters
    ----------
    request : django.http.request
        request['id'] is an item ID

    Returns
    -------
    JsonResponse
        {
            'success': bool
            'msg': str
        }
        The msg is only there if there was a problem

    """

    try:
        it = Item.objects.get(pk=json.loads(request.GET['id']))
        os.unlink(it.path)
        it.delete()
    except Exception as exp: # pylint: disable=broad-except
        return JsonResponse({'success': False, 'msg': str(exp)})
   
    return JsonResponse({
        'success': True,
    })



