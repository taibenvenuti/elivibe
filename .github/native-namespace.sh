#!/usr/bin/env bash
# Ubuntu 24.04 GitHub-hosted native job only. Never run on a developer machine.
set -euo pipefail
[[ $RUNNER_ENVIRONMENT == github-hosted && $(id -u) != 0 ]]
[[ $(command -v bwrap) == /usr/bin/bwrap ]]
uname -r
bwrap --version
probe=(/usr/bin/bwrap --unshare-all --unshare-net --clearenv --cap-drop ALL --die-with-parent --new-session --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib64 /lib64 --proc /proc --)
profiles=/sys/kernel/security/apparmor/profiles
check_namespace() {
  "${probe[@]}" /usr/bin/true || return
  echo 'Namespace setup succeeded; checking the enforcing child stack and isolation.'
  "${probe[@]}" /usr/bin/python3 -IB - --verify-hosted-namespace "$(readlink /proc/self/ns/net)" < dev/omp_smoke.py
}
started=$(date --iso-8601=seconds)
if failure=$(check_namespace 2>&1); then
  printf '%s\n' "$failure"
else
  printf '%s\n' "$failure"
  [[ $failure == 'bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted' ]]
  [[ $(sysctl -n kernel.apparmor_restrict_unprivileged_userns) == 1 ]]
  # Require the specific enforcing denial, not just an enabled AppArmor module.
  sudo journalctl -k --since "$started" --no-pager -o cat --grep='apparmor="DENIED"' |
    awk '/operation="capable"/ && /profile="unprivileged_userns"/ && /comm="bwrap"/ && /capname="net_admin"/ { found=1 } END { exit !found }'
  loaded=$(sudo cat "$profiles")
  if grep -Eq '^(bwrap|unpriv_bwrap) ' <<< "$loaded"; then exit 1; fi
  for path in /etc/apparmor.d/{,local/}{bwrap-userns-restrict,unpriv_bwrap}; do
    [[ ! -e $path && ! -L $path ]]
  done
  echo 'Before: no bwrap or unpriv_bwrap profile loaded; net_admin denied. Sandbox payload cannot start.'
  # Download, do not install: the collection has unrelated policy-loading maintainer scripts.
  work=$(mktemp -d)
  package=apparmor-profiles_4.0.1really4.0.1-0ubuntu0.24.04.9_all.deb
  curl -fsSL --proto '=https' --proto-redir '=https' --max-time 60 "https://archive.ubuntu.com/ubuntu/pool/main/a/apparmor/$package" -o "$work/$package"
  (cd "$work" && echo "90b02aa006eea7702cd4e851343e469e41365dda42145a3cb035de1d6c773b8c  $package" | sha256sum --check)
  dpkg-deb --fsys-tarfile "$work/$package" | tar -xOf - ./usr/share/apparmor/extra-profiles/bwrap-userns-restrict > "$work/profile"
  echo "11d39094f044f0cda0febb3ad517b830301da6b2ce929664af09ee9e4dd264f9  $work/profile" | sha256sum --check
  sudo apparmor_parser --add --skip-cache "$work/profile"
  sudo grep -Fx -e 'bwrap (enforce)' -e 'unpriv_bwrap (enforce)' "$profiles"
  check_namespace
fi
