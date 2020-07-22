from django.shortcuts import render

# Create your views here.

def items(request, tag='None'):
    return render(request, 'core/item.html', {'stuff': 'hello'})
