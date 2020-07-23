# Markdown Viewer with Tags

## Overview

A Django web app that allows you to display a bunch of markdown files
that live in a directory (and sub directories) using a tag hierarchy
view.  Should be able to create/view/edit/delete.


## Install

1. Install packages (note we use pip for Django, since the Django
   version with ubuntu 18.04 is 1.11 which is too old):

        cat requirements_system.txt | xargs sudo apt -y install
        sudo pip3 install -Ur requirements_pip.txt

2. Initialize empty models in the database

        ./ws/manage.py migrate

3. Configure where doc repo is by editing `ws/conf/settings.py`:

        DOC_REPO = '/blah/blah'

4. Start up the development server

        ./ws/manage.py runserver 0:8000


## Running Django in production

More-or-less following a cut down version of
[this](https://djangodeployment.readthedocs.io/en/latest/index.html).
In summary, apache is serving static files and proxying other requests
through to gunicorn which via a socket is passing along to Django which
is running in /var/tmp/mdorg

### Settings

1. Production settings.  Ensure settings file has DEBUG=False and
   imports secret keys from the local filesystem.  To make a new secret
   key in python do this:

        import sys
        from django.utils.crypto import get_random_string
        with open('/etc/django_secret_key.txt', 'w') as f:
            f.write(get_random_string(50))

    and make sure it is readable by user running Django:

        chmod 644 /etc/django_secret_key.txt

2. Logging is set in `conf/settings/prod.py` but you need to set up the
   directory (as root):

        mkdir /var/log/mdorg/
        chown user.user /var/log/mdorg/

###  Apache

1. a2enmod proxy proxy_http headers

2. Put this in apache.conf

        <VirtualHost *:80>

            ...

            WSGIDaemonProcess yourapplication user=me group=users threads=5 python-path=/var/tmp/mdorg/ws

            WSGIScriptAlias /wharever /var/tmp/mdorg/ws/conf/wsgi.py
            <Directory /var/tmp/mdorg/ws>
                 WSGIProcessGroup yourapplication
                 WSGIApplicationGroup %{GLOBAL}
                 WSGIScriptReloading On
                 Require all granted
                 AllowOverride All
            </Directory>

            ...

        </VirtualHost>

