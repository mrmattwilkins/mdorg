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
In summary, nginx is serving static files and proxying other requests
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

###  Nginx

Set up our site in /etc/nginx/site-enabled

            location /blah/ {
                proxy_pass http://unix:/run/mdorg_gunicorn.sock;
                proxy_set_header Host $http_host;
                proxy_redirect off;
                proxy_set_header X-Forwarded-For $remote_addr;
                proxy_set_header X-Forwarded-Proto $scheme;
            }


### Gunicorn

Gunicorn takes requests from nginx and runs Django

        cat << 'EOF' > /etc/systemd/system/mdorg_gunicorn.socket
        [Unit]
        Description=mdorg gunicorn socket

        [Socket]
        ListenStream=/run/mdorg_gunicorn.sock

        [Install]
        WantedBy=sockets.target
        EOF

        cat << 'EOF' > /etc/systemd/system/mdorg_gunicorn.service
        [Unit]
        Description=mdorg gunicorn daemon
        Requires=mdorg_gunicorn.socket
        After=network.target

        [Service]
        User=blah
        Group=blah
        WorkingDirectory=/var/tmp/mdorg/ws
        ExecStart=/usr/bin/gunicorn3 \
                  --access-logfile - \
                  --bind unix:/run/mdorg_gunicorn.sock \
                  conf.wsgi:application

        [Install]
        WantedBy=multi-user.target

        EOF
        systemctl start mdorg_gunicorn.socket
        systemctl enable mdorg_gunicorn.socket

