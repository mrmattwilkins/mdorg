# Markdown Viewer Editor with Tags

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

        ./manage.py migrate

6. Start up the development server

        ./manage.py runserver 0:8000

7. Make a superuser admin account

        ./manage.py createsuperuser --username=admin
            --email=matt.wilkins@niwa.co.nz

8. There are multiple versions of the settings that are controlled via
   `conf/settings/__init__.py` which imports `default.py` and then the
   required version based on the git branch you are tracking.  A `prod`
   branch means the `conf/settings/prod.py` are used.

9. Edit `ALLOWED_HOSTS` in `conf/settings/default.py` to control access
   to the server.

## Running Django in production

More-or-less following a cut down version of
[this](https://djangodeployment.readthedocs.io/en/latest/index.html).
In summary, nginx is serving static files and proxying other requests
through to gunicorn which via a socket is passing along to Django which
is running in /home/hydrodesk/hydrodesk.prod which is tracking the prod
branch.

Development is in /home/hydrodesk/hydrodesk which tracks whatever branch
you wish.  The development server will listen on 8000.

In the following the environment DOMAIN should be set, ideally to
something like hdesk.nzwam.nz


### Settings

1. Production settings.  Ensure that `conf/settings/prod.py` settings
   file has DEBUG=False and imports secret keys from the local
   filesystem.  To make a new secret key in python do this:

        import sys
        from django.utils.crypto import get_random_string
        with open('/etc/django_secret_key.txt', 'w') as f:
            f.write(get_random_string(50))

    and make sure it is readable by user running Django:

        chmod 644 /etc/django_secret_key.txt

2. Logging is set in `conf/settings/prod.py` but you need to set up the
   directory (as root):

        mkdir /var/log/hydrodesk/
        chown hydrodesk.hydrodesk /var/log/hydrodesk/

3. Static files

    1. Ensure we have this in `conf/settings/default.py`

            STATIC_ROOT = '/var/cache/hydrodesk/static/'
            STATIC_URL = '/static/'

    2. Set up location for static files (as root)

            umask 0022
            mkdir -m755 -p /var/cache/hydrodesk/static
            chown -R hydrodesk.hydrodesk /var/cache/hydrodesk/static/

    3. And copy them over (as hydrodesk user)

            umask 0022
            ./ws/manage.py collectstatic


###  Nginx

0. Get ssl certs
        
        certbot certonly --nginx -d hdesk.nzwam.nz

   This also sets up the automatic renewal

1. Make sure no one can access the site except with proper name (people
   scanning/trolling the web repeatedly hit our website using the IP
   address)

        cat << 'EOF' > /etc/nginx/sites-available/default
        server {
            listen      80 default_server;
            server_name _;
            return      444;
        }
        EOF

2. Set up our site

        cat << 'EOF' > /etc/nginx/sites-available/hdesk.nzwam.nz
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 10m;

        server {
            listen 80;
            server_name hdesk.nzwam.nz hydrodesk.nzwam.nz;
            return 301 https://hdesk.nzwam.nz$request_uri;
        }

        server {
            listen              443 ssl;
            server_name         hdesk.nzwam.nz;
            keepalive_timeout   70;
            ssl_certificate     /etc/letsencrypt/live/hdesk.nzwam.nz/fullchain.pem;
            ssl_certificate_key /etc/letsencrypt/live/hdesk.nzwam.nz/privkey.pem;
            root                /var/www/hdesk.nzwam.nz;

            # this is for when we want to mark site as down.  comment out all
            # the gunicorn stuff below and uncomment this one
            #location / {
            #    try_files $uri /index.html;
            #}

            # stop access via ip address or any other hostname
            if ($host != "hdesk.nzwam.nz") {
                return 444;
            }

            location / {
                proxy_pass http://unix:/run/gunicorn.sock;
                proxy_set_header Host $http_host;
                proxy_redirect off;
                proxy_set_header X-Forwarded-For $remote_addr;
                proxy_set_header X-Forwarded-Proto $scheme;
                client_max_body_size 5g;	
                proxy_request_buffering off;	# so we don't store file uploads in a tmp file, then copy to gunicorn
            }

            location /static/ {
                alias /var/cache/hydrodesk/static/;
            }
        }	
        EOF
        cd /etc/nginx/sites-enabled
        ln -s ../sites-available/$DOMAIN .

3. And a default location when site is down

        mkdir -m755 /var/www/$DOMAIN
        cat << EOF > /var/www/$DOMAIN/index.html
            <p>Sorry, we are down for database maintenance</p>
            <p>Check back in a few minutes.</p>
            <!--<p>We aim to be back online by </p>-->
        EOF
        chmod 644 /var/www/$DOMAIN/index.html

### Gunicorn

1. Gunicorn takes requests from nginx and runs Django

        cat << 'EOF' > /etc/systemd/system/gunicorn.socket
        [Unit]
        Description=gunicorn socket

        [Socket]
        ListenStream=/run/gunicorn.sock

        [Install]
        WantedBy=sockets.target
        EOF

        cat << 'EOF' > /etc/systemd/system/gunicorn.service
        [Unit]
        Description=gunicorn daemon
        Requires=gunicorn.socket
        After=network.target

        [Service]
        User=hydrodesk
        Group=www-data
        WorkingDirectory=/home/hydrodesk/hydrodesk.prod/ws
        ExecStart=/usr/bin/gunicorn3 \
                --timeout=4000 \
                  --access-logfile - \
                  --workers 4 \
                  --bind unix:/run/gunicorn.sock \
                  conf.wsgi:application

        [Install]
        WantedBy=multi-user.target

        EOF
        systemctl start gunicorn.socket
        systemctl enable gunicorn.socket

    The reason for the large timeout is to allow the user to do large
    uploads.

## Development

### Lint

You can run lint on a source file like this:

    pylint3 --load-plugins pylint_django admin.py

### Testing

The tests live in `ws/tests`, to run them all do

    ./manage.py test

if you want to run just one, do

    ./manage.py test core.tests.test_admin

### Coverage

I'm using coverage.py to check the test coverage.  Don't use the NOSE
coverage library in Django, it means coverage is under-reported because
Django testing starts then calls coverage.  Need to run the testing
under coverage, in other words, start the Django test from coverage like
this:

    python3-coverage run manage.py test

or

    python3-coverage run manage.py test core.tests.test_admin

Then view the results like so:

    python3-coverage report

or

    python3-coverage html

then 

    google-chrome htmlcov/index.html




