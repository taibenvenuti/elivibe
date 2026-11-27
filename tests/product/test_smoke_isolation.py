import errno
import socket
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from tools import omp_smoke

HOST_NETNS = "net:[100]"
HOSTED_LABEL = "bwrap//&unpriv_bwrap (enforce)"


class NativeLaunch(Exception):
    pass


@pytest.fixture
def sandbox(monkeypatch, tmp_path):
    status = {
        "Uid": "1000\t1000\t1000\t1000",
        "CapEff": "0000000000000000",
        "CapPrm": "0000000000000000",
        "CapBnd": "0000000000000000",
        "NoNewPrivs": "1",
    }
    observations = SimpleNamespace(
        netns="net:[101]", label=HOSTED_LABEL, interfaces=[(1, "lo")]
    )

    def read_proc(path, **_):
        if path == Path("/proc/self/status"):
            return "".join(f"{key}:\t{value}\n" for key, value in status.items())
        assert path == Path("/proc/self/attr/current")
        if observations.label is None:
            raise FileNotFoundError(path)
        return observations.label + "\n"

    def readlink(path):
        assert Path(path) == Path("/proc/self/ns/net")
        return observations.netns

    tcp = MagicMock()
    tcp.__enter__.return_value = tcp
    tcp.getsockname.return_value = ("127.0.0.1", 12345)
    tcp.accept.return_value = (tcp, ("127.0.0.1", 12346))
    udp = MagicMock()
    udp.__enter__.return_value = udp
    udp.connect_ex.return_value = errno.ENETUNREACH

    def open_socket(family, kind):
        return sockets_by_kind[family, kind]

    sockets_by_kind = {
        (socket.AF_INET, socket.SOCK_STREAM): tcp,
        (socket.AF_INET, socket.SOCK_DGRAM): udp,
    }
    monkeypatch.setattr(Path, "read_text", read_proc)
    monkeypatch.setattr(
        omp_smoke,
        "os",
        SimpleNamespace(environ=omp_smoke.os.environ, readlink=readlink),
    )
    monkeypatch.setattr(
        omp_smoke,
        "socket",
        SimpleNamespace(
            AF_INET=socket.AF_INET,
            SOCK_STREAM=socket.SOCK_STREAM,
            SOCK_DGRAM=socket.SOCK_DGRAM,
            if_nameindex=lambda: observations.interfaces,
            socket=open_socket,
        ),
    )
    monkeypatch.setenv("SMOKE_HOST_NETNS", HOST_NETNS)
    for key in (
        "HOME",
        "PI_CODING_AGENT_DIR",
        "TMPDIR",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_CACHE_HOME",
        "XDG_STATE_HOME",
    ):
        profile = tmp_path / key
        profile.mkdir()
        monkeypatch.setenv(key, str(profile))
    monkeypatch.setattr(omp_smoke, "TRIAL", tmp_path)
    monkeypatch.setattr(omp_smoke, "WORK", tmp_path / "work")
    monkeypatch.delenv("LD_LIBRARY_PATH", raising=False)
    launch = Mock(side_effect=NativeLaunch)
    monkeypatch.setattr(omp_smoke, "verify_omp_cli", launch)
    monkeypatch.setattr(omp_smoke, "native", launch)
    monkeypatch.setattr(
        omp_smoke,
        "ThreadingHTTPServer",
        Mock(side_effect=AssertionError("unexpected HTTP server launch")),
    )
    return SimpleNamespace(
        status=status, observations=observations, launch=launch, tcp=tcp, udp=udp
    )


def assert_launch_blocked(sandbox, *, hosted=True):
    with pytest.raises(SystemExit):
        omp_smoke.isolated(hosted)
    sandbox.launch.assert_not_called()


@pytest.mark.parametrize(
    ("hosted", "label"),
    [(True, HOSTED_LABEL), (False, "unconfined"), (False, None)],
)
def test_isolated_reaches_native_with_required_properties(sandbox, hosted, label):
    sandbox.observations.label = label
    with pytest.raises(NativeLaunch):
        omp_smoke.isolated(hosted)
    sandbox.launch.assert_called_once()


@pytest.mark.parametrize(
    "label", [None, "unconfined", "bwrap//&unpriv_bwrap (complain)"]
)
def test_hosted_isolated_requires_enforcing_label(sandbox, label):
    sandbox.observations.label = label
    assert_launch_blocked(sandbox)


@pytest.mark.parametrize("field", ["CapEff", "CapPrm", "CapBnd"])
@pytest.mark.parametrize("value", [None, "0000000000000001"], ids=["missing", "set"])
def test_isolated_requires_empty_capability_sets(sandbox, field, value):
    if value is None:
        del sandbox.status[field]
    else:
        sandbox.status[field] = value
    assert_launch_blocked(sandbox)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("Uid", None, id="missing-uid"),
        pytest.param("Uid", "1000\t0\t1000\t1000", id="effective-root"),
        pytest.param("Uid", "1000\t1000\t0\t1000", id="saved-root"),
        pytest.param("NoNewPrivs", "0", id="new-privileges-allowed"),
    ],
)
def test_isolated_requires_unprivileged_identity(sandbox, field, value):
    if value is None:
        del sandbox.status[field]
    else:
        sandbox.status[field] = value
    assert_launch_blocked(sandbox)


@pytest.mark.parametrize(
    ("host_netns", "sandbox_netns"),
    [
        pytest.param(None, "net:[101]", id="missing-host"),
        pytest.param(HOST_NETNS, HOST_NETNS, id="shared"),
        pytest.param("invalid", "net:[101]", id="malformed-host"),
        pytest.param(HOST_NETNS, "invalid", id="malformed-sandbox"),
    ],
)
def test_isolated_requires_distinct_namespace(
    sandbox, monkeypatch, host_netns, sandbox_netns
):
    if host_netns is None:
        monkeypatch.delenv("SMOKE_HOST_NETNS")
    else:
        monkeypatch.setenv("SMOKE_HOST_NETNS", host_netns)
    sandbox.observations.netns = sandbox_netns
    assert_launch_blocked(sandbox, hosted=False)


def test_isolated_requires_loopback_only(sandbox):
    sandbox.observations.interfaces.append((2, "eth0"))
    assert_launch_blocked(sandbox, hosted=False)


def test_isolated_requires_working_loopback(sandbox):
    sandbox.tcp.connect.side_effect = OSError(errno.ECONNREFUSED, "loopback down")
    assert_launch_blocked(sandbox, hosted=False)


def test_isolated_rejects_external_route(sandbox):
    sandbox.udp.connect_ex.return_value = 0
    assert_launch_blocked(sandbox, hosted=False)
