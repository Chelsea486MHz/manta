#
# Build image
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

#
# Production image
#
FROM python:3.11-slim

# Container settings
ENV APP_USER app
ENV APP_DIR "/$APP_USER"

# Python security
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1

# App settings
ENV DEBUG False
WORKDIR $APP_DIR
EXPOSE 8000

# Install dependencies from the build image venv
COPY --from=image-build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the app
COPY app.py .
COPY config.py .

# Add user and group
RUN groupadd -r -g 1000 $APP_USER && \
    useradd -r -u 1000 -g $APP_USER $APP_USER

# TMPFS creation
RUN echo "tmpfs /tmp tmpfs defaults 0 0" >> /etc/fstab

# Install dependencies
RUN apt update && apt install -y gnupg

# Run the app
USER $APP_USER
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]