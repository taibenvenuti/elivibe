#!/usr/bin/env bash
# Ubuntu 24.04 GitHub-hosted native job only. Never run on a developer machine.
set -euo pipefail
[[ $RUNNER_ENVIRONMENT == github-hosted && $(id -u) != 0 ]]
[[ $(command -v bwrap) == /usr/bin/bwrap ]]
uname -r
bwrap --version
probe=(/usr/bin/bwrap --unshare-all --unshare-net --clearenv --cap-drop ALL --die-with-parent --new-session --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib64 /lib64 --proc /proc --)
profiles=/sys/kernel/security/apparmor/profiles
required_stack=0
started=$(date --iso-8601=seconds)
if failure=$("${probe[@]}" /usr/bin/true 2>&1); then
  echo 'Namespace preflight passed without a policy change.'
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
  "${probe[@]}" /usr/bin/true
  required_stack=1
fi
"${probe[@]}" /usr/bin/python3 -I - "$(readlink /proc/self/ns/net)" "$required_stack" <<'PY'
import errno, os, socket, sys
from pathlib import Path

label = Path('/proc/self/attr/current').read_text().strip()
print('Sandbox AppArmor label:', label)
if sys.argv[2] == '1':
    assert label == 'bwrap//&unpriv_bwrap (enforce)', label
assert os.getuid() != 0 and os.readlink('/proc/self/ns/net') != sys.argv[1]
status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines())
assert all(int(status[key], 16) == 0 for key in ('CapEff', 'CapPrm', 'CapBnd'))
assert [name for _, name in socket.if_nameindex()] == ['lo']
with socket.socket() as server, socket.socket() as client:
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    client.connect(server.getsockname())
    peer, _ = server.accept()
    peer.close()
with socket.socket(type=socket.SOCK_DGRAM) as sock:
    # Route lookup only: UDP connect sends no packet, even on a broken runner.
    assert sock.connect_ex(('192.0.2.1', 9)) == errno.ENETUNREACH
print('Non-root; no capabilities; separate network namespace; only lo; TCP loopback works; external route unreachable.')
PY
