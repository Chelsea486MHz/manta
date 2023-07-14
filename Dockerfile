#
# Dockerfile borrowing hardening from "Iron Alpine"
# => https://github.com/ironpeakservices/iron-alpine
#

FROM python:3.11 AS image-build

RUN apt update
RUN apt install -y --no-install-recommends \
    build-essential \
    gcc
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt



FROM python:3.11.0-alpine

# Container settings
ENV APP_USER=app
ENV APP_DIR="/$APP_USER"

# Add user and group
RUN addgroup -S $APP_USER && \
    adduser -s /bin/true -u 1000 -D -h $APP_DIR -G $APP_USER $APP_USER

# Hardening
RUN rm -fr /var/spool/cron && \
	rm -fr /etc/crontabs && \
	rm -fr /etc/periodic && \
    find /sbin /usr/sbin ! -type d -a ! -name apk -a ! -name ln -delete && \
    find / -xdev -type d -perm +0002 -exec chmod o-w {} + && \
	find / -xdev -type f -perm +0002 -exec chmod o-w {} + && \
	chmod 777 /tmp/ && \
    chown $APP_USER:root /tmp/ && \
    find /sbin /usr/sbin ! -type d -a ! -name apk -a ! -name ln -delete && \
    sed -i -r "/^($APP_USER|root|nobody)/!d" /etc/group && \
    sed -i -r "/^($APP_USER|root|nobody)/!d" /etc/passwd && \
    sed -i -r 's#^(.*):[^:]*$#\1:/sbin/nologin#' /etc/passwd && \
    while IFS=: read -r username _; do passwd -l "$username"; done < /etc/passwd || true && \
    find /bin /etc /lib /sbin /usr -xdev -type f -regex '.*-$' -exec rm -f {} + && \
    find /bin /etc /lib /sbin /usr -xdev -type d -exec chown root:root {} \; -exec chmod 0755 {} \; && \
    find /bin /etc /lib /sbin /usr -xdev -type f -a \( -perm +4000 -o -perm +2000 \) -delete && \
    find /bin /etc /lib /sbin /usr -xdev \( \
    -iname hexdump -o \
    -iname chgrp -o \
    -iname ln -o \
    -iname od -o \
    -iname strings -o \
    -iname su -o \
    -iname sudo \
    \) -delete && \
    rm -fr /etc/init.d /lib/rc /etc/conf.d /etc/inittab /etc/runlevels /etc/rc.conf /etc/logrotate.d && \
    rm -fr /etc/sysctl* /etc/modprobe.d /etc/modules /etc/mdev.conf /etc/acpi && \
    rm -fr /root && \
    rm -f /etc/fstab && \
    find /bin /etc /lib /sbin /usr -xdev -type l -exec test ! -e {} \; -delete && \
    mount -t tmpfs none /tmp

# Python security
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# App settings
ENV DEBUG False
WORKDIR $APP_DIR
EXPOSE 8000

# Install GnuPG
RUN apk update && \
    apk add --no-cache gnupg

# Install dependencies from the build image venv
COPY --from=image-build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the app
COPY app.py .
COPY config.py .

# Run the app
USER $APP_USER
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]