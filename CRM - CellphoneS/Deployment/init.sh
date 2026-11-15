#!/bin/bash
set -e

export PYENV_VERSION=3.12.15
export UV_HTTP_TIMEOUT=300
export UV_HTTP_RETRIES=10

cat > /home/frappe/.my.cnf <<'EOF'
[client]
skip-ssl
EOF

chmod 600 /home/frappe/.my.cnf

if [ -d "/home/frappe/frappe-bench/apps/frappe" ] && \
   [ -d "/home/frappe/frappe-bench/apps/crm" ] && \
   [ -f "/home/frappe/frappe-bench/sites/crm.localhost/site_config.json" ]; then
    echo "Existing Bench and CRM site detected"
    cd /home/frappe/frappe-bench
    bench start
    exit 0
fi

echo "Creating new bench..."

bench init --skip-redis-config-generation frappe-bench --frappe-branch version-15 --python /home/frappe/.pyenv/versions/3.12.15/bin/python3
cd frappe-bench

bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

bench get-app crm --branch main

bench new-site crm.localhost \
    --force \
    --mariadb-root-password 123 \
    --admin-password admin \
    --no-mariadb-socket

bench --site crm.localhost install-app crm
bench --site crm.localhost set-config developer_mode 1
bench --site crm.localhost set-config mute_emails 1
bench --site crm.localhost set-config server_script_enabled 1
bench --site crm.localhost clear-cache

bench use crm.localhost
bench start