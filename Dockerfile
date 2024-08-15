FROM httpd:latest AS base

RUN apt-get update
RUN apt-get install -y tzdata
RUN ln -sf /usr/share/zoneinfo/America/Chicago /etc/localtime

RUN apt-get install -y python3 python3-pip python3-venv
RUN apt-get install -y libapache2-mod-wsgi-py3
RUN ln -sf /usr/lib/apache2/modules/mod_wsgi.so /usr/local/apache2/modules/mod_wsgi.so
RUN mkdir -p /var/www/static/sets/previews
RUN chown www-data /var/www/static/sets/previews

# install chrome for page preview screenshots
RUN apt-get install -y wget
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# expected to error (fixed with fix broken):
RUN dpkg -i google-chrome-stable_current_amd64.deb; exit 0
RUN apt-get --fix-broken install -y

FROM base AS packages
WORKDIR /app
RUN python3 -m venv .venv
COPY requirements.txt .

FROM packages AS venv
RUN .venv/bin/python -m pip install --upgrade pip
RUN .venv/bin/pip install -r requirements.txt

FROM venv AS requirements
COPY --chown=www-data:www-data . .
RUN sed -i 's|#!.*|#!/app/.venv/bin/python|g' /app/.venv/bin/django-admin
RUN ln -sf /app/.venv/lib/python*/site-packages/django/contrib/admin/static/admin/ /app/static/sets/admin

RUN .venv/bin/python manage.py collectstatic --no-input

FROM requirements AS django

# RUN sed -i 's|%b|%b %R \\"%{Host}i\\"|g'  /usr/local/apache2/conf/httpd.conf
RUN sed -i 's|CustomLog logs/access.log combined|CustomLog /dev/stdout combined|g'  /usr/local/apache2/conf/httpd.conf
RUN sed -i 's|ErrorLog logs/error.log|ErrorLog  /dev/stderr|g'  /usr/local/apache2/conf/httpd.conf
RUN printf "Include /app/site.conf\n" >>  /usr/local/apache2/conf/httpd.conf
RUN printf "ServerName sets.rabbitfrost.com\n" >>  /usr/local/apache2/conf/httpd.conf
RUN printf "WSGISocketPrefix /var/run/wsgi\n" >>  /usr/local/apache2/conf/httpd.conf
