#!/bin/sh
# Prepare bind-mounted host directories, then drop privileges before starting the API.
#
# The models directory is mounted read-only and may be owned by any host user, so a
# failure to adjust it is never fatal. The uploads directory must be writable by the
# unprivileged runtime user, so it is normalized when the container owns the volume.
set -e

APP_USER="${APP_USER:-appuser}"
APP_HOME="${APP_HOME:-/app}"

if [ "$(id -u)" = "0" ]; then
    if [ -d "${APP_HOME}/uploads" ]; then
        chown "${APP_USER}:${APP_USER}" "${APP_HOME}/uploads" 2>/dev/null || \
            echo "warning: could not set ownership on ${APP_HOME}/uploads; uploads may fail to save" >&2
    fi
    mkdir -p "${APP_HOME}/uploads"
    exec gosu "${APP_USER}" "$@"
fi

exec "$@"
