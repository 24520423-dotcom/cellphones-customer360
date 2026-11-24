#!/usr/bin/env bash
set -euo pipefail

mode=$1
site=$2
patch=$3
bench_dir=/home/frappe/frappe-bench
frappe_commit=2e9ecdc03fa5b5b8d1ba05224a1aff7dad832bd0
crm_base=638bf3db23e7142870819a213368e028866b79b1

if [[ ! $site =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]]; then
    printf '%s\n' "Invalid site name." >&2
    exit 1
fi

if [[ $mode == new ]]; then
    if [[ -e $bench_dir/sites/$site/site_config.json || -e $bench_dir/apps/frappe ]]; then
        printf '%s\n' "A Bench or site already exists. Use the update workflow." >&2
        exit 1
    fi
    bench init --frappe-branch v15.126.1 --ignore-exist --skip-assets \
        --skip-redis-config-generation --python "$(command -v python)" "$bench_dir"
    cd "$bench_dir"
    bench set-config -g redis_cache redis://redis:6379
    bench set-config -g redis_queue redis://redis:6379
    bench set-config -g redis_socketio redis://redis:6379
    sed -i '/^redis_/d' Procfile
    git clone https://github.com/frappe/crm.git apps/crm
    git -C apps/crm switch -c feature/cellphones-c360 "$crm_base"
elif [[ $mode != update && $mode != verify ]]; then
    printf '%s\n' "Invalid release mode." >&2
    exit 1
fi

cd "$bench_dir"
test "$(git -C apps/frappe rev-parse HEAD)" = "$frappe_commit"
git -C apps/crm merge-base --is-ancestor "$crm_base" HEAD
test -f apps/cellphones_c360/pyproject.toml
test -f apps/cellphones_c360/cellphones_c360/public/branding/cellphones-brand.png

if [[ $mode == verify ]]; then
    bench version
    bench --site "$site" list-apps
    exit 0
fi

test -r "$patch"
if [[ $mode == update ]]; then
    test -f "sites/$site/site_config.json"
    bench --site "$site" backup --with-files
fi

crm_repo=$bench_dir/apps/crm
if [[ -n $(git -C "$crm_repo" status --porcelain) ]]; then
    printf '%s\n' "Commit local CRM changes before applying a release." >&2
    exit 1
fi
scratch=$(mktemp -d /tmp/c360-release.XXXXXX)
cleanup() {
    if [[ -d $scratch/worktree ]]; then
        git -C "$scratch/worktree" am --abort >/dev/null 2>&1 || true
        git -C "$crm_repo" worktree remove --force "$scratch/worktree"
    fi
    rm -r -- "$scratch"
}
trap cleanup EXIT
mkdir "$scratch/mail"
git mailsplit -o"$scratch/mail" "$patch" >/dev/null
git -C "$crm_repo" log --format=medium -p "$crm_base..HEAD" |
    git patch-id --stable | cut -d' ' -f1 > "$scratch/applied"
git -C "$crm_repo" worktree add --detach "$scratch/worktree" HEAD
for mail in "$scratch"/mail/*; do
    patch_id=$(git patch-id --stable < "$mail" | cut -d' ' -f1)
    if [[ -z $patch_id ]]; then
        printf '%s\n' "Could not read CRM patch identity." >&2
        exit 1
    fi
    if ! grep -qx "$patch_id" "$scratch/applied"; then
        git -C "$scratch/worktree" -c user.name="CellphoneS C360 release" \
            -c user.email="release@example.test" am "$mail"
    fi
done
git -C "$crm_repo" merge --ff-only "$(git -C "$scratch/worktree" rev-parse HEAD)"

for app in crm cellphones_c360; do
    env/bin/pip install -e "apps/$app"
    grep -qx "$app" sites/apps.txt || printf '%s\n' "$app" >> sites/apps.txt
done
if [[ $mode == new ]]; then
    if [[ -f apps/crm/package.json ]]; then
        yarn --cwd apps/crm install --frozen-lockfile
    fi
    yarn --cwd apps/crm/frontend install --frozen-lockfile
    bench new-site "$site" --db-host mariadb --db-root-username root \
        --db-root-password "$C360_DB_ROOT_PASSWORD" --admin-password "$C360_ADMIN_PASSWORD" \
        --mariadb-user-host-login-scope '%'
fi
for app in crm cellphones_c360; do
    if ! bench --site "$site" list-apps | grep -q "^$app[[:space:]]"; then
        bench --site "$site" install-app "$app"
    fi
done
bench --site "$site" migrate --skip-search-index
bench build --app crm
if [[ $mode == new ]]; then
    bench --site "$site" execute cellphones_c360.branding.apply_default_branding
fi
bench --site "$site" clear-cache
bench --site "$site" list-apps
