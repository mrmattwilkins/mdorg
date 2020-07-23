import os
import re
import markdown
import frontmatter
from pathlib import Path

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone


from .models import Item, Tag

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
   
    return items(request, msg=mark_safe('<br />'.join(msg)))

def search(request):
    """Search for items containing text."""

    txt, tag = request.GET['lookfor'], request.GET.get('tag', None)

    if tag:
        its = Item.objects.filter(tags__id=tag).order_by('title')
    else:
        its = Item.objects.all().order_by('title')

    msg = ['<ul>']
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
            args = [found.id, tag] if tag else [found.id]
            msg.append(f"""<li><a href="{reverse('core:item', args=args)}">{found.title}</a>""")
            msg.append(f"{'<br />' + context if context else ''}</li>")

    msg.append('</ul>')

    return items(request, tag=tag, msg=mark_safe(''.join(msg)))

def items(request, tag=None, msg=None):
    """Return items in sidebar with possible message in main

    Parameters
    ----------
    request: django.http.request

    tag: int
        Tag id.  If given only these items will be in sidebar (otherwise all)
    msg: str
        A mark_safed string to display in the main

    """

    # get all tags to display at the top
    tags = [
        (t.id, t.name)
        for t in Tag.objects.all().order_by('name')
    ]

    if tag:
        its = Item.objects.filter(tags__id=tag).order_by('title')
    else:
        its = Item.objects.all().order_by('title')

    return render(request, 'core/items.html', {
        'tags': tags,
        'tag': tag,
        'items': its,
        'msg': msg
    })

def item(request, pkey, tag=None):
    """View of item

    Parameters
    ----------
    request: django.http.request

    pkey: int
        The Item id to display in main
    tag: int
        Tag id.  If given only these items will be in sidebar (otherwise all)
    
    """

    it = Item.objects.get(pk=pkey)

    msg = []
    msg.append(f'<h2 style="display:inline;">{it.title}</h2>')

    # tags in () after title
    if it.tags.all():
        msg.append(' (')
        msg.append(', '.join(
            f"""<a href="{reverse('core:items', args=(t.id,))}">{t.name}</a>"""
            for t in it.tags.all()
        ))
        msg.append(')')
    msg.append('<br />')
    
    if it.created:
        msg.append(f'<small><i>Created: </i>{timezone.localtime(it.created).strftime("%Y-%m-%d %H:%M")}</small><br />')

    last = timezone.localtime(it.accessed).strftime("%Y-%m-%d %H:%M") if it.accessed else 'never'
    msg.append(f'<small><i>Last access: </i>{last}</small><br />')

    msg.append(f'<small><i>Filename: </i>{os.path.basename(it.path)}</small><br />')
    msg.append('<br />')

    # get the content
    with open(it.path, "r", encoding="utf-8") as fh:
        text = frontmatter.load(fh)
        msg.append(markdown.markdown(text.content))

    # save back with correct accessed
    with open(it.path, "w", encoding="utf-8") as fh:
        text['accessed'] = it.accessed = timezone.now()
        fh.write(frontmatter.dumps(text))
        it.save()

    return items(request, tag, msg=mark_safe(''.join(msg)))


