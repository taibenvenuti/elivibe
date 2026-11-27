"""Exercise verified archives in sandboxed Linux OMP with synthetic inference."""

import argparse
import base64
import errno
import hashlib
import io
import json
import os
import queue
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import monotonic
from zipfile import ZipFile

OMP_VERSION = "19.2.1"
# GitHub can1357/oh-my-pi v19.2.1, omp-linux-x64 release asset.
OMP_SHA256 = "e8b937f9bf023baa147bdd300ad5421af0a6ef8b1f350c47a9a93d5fca94feca"
HOSTED_LABEL = "bwrap//&unpriv_bwrap (enforce)"
TRIAL = Path("/trial")
WORK = TRIAL / "work"
OMP = "/runtime/omp"
PRIMARY = "smoke-primary"
SKILL = Path("skills/elivibe/SKILL.md")
CODEX_SKILL = SKILL.parent / "agents/openai.yaml"
CODEX_POLICY = b"policy:\n  allow_implicit_invocation: false\n"
ADAPTER = Path("adapters/omp/index.ts")
CORE = Path("core/index.ts")
EXPLICIT = "eliVibe explicit explanation."
LIGHT = "eliVibe Light teaching policy."
FULL = "eliVibe Full teaching policy."
SECTION = "\n\n## eliVibe explanation\n\n"
ORIGINAL = (
    "SMOKE_SOURCE_REPORT: Wrote the queue fixture. The commit records that the event "
    "can be replayed; no test verified that a subscriber applied it."
)
ANSWER = (
    "SMOKE_FIRST_EXPLANATION: The commit is a receipt, not proof of delivery. "
    "The subscriber still needs to read and apply the event."
)
FOLLOWUP = (
    "SMOKE_FOLLOWUP: If replay happens after the subscriber applied the event "
    "but before it recorded progress, it can see the event twice."
)
MORE = "SMOKE_MORE: Applying the same event again must be safe."
TOOL_REFUSAL = "eliVibe explanation turns do not run tools."


def process_evidence(proc, hosted):
    try:
        status = dict(
            line.split(":", 1)
            for line in (proc / "status").read_text().splitlines()
            if ":" in line
        )
        netns = os.readlink(str(proc / "ns/net"))
        label = (
            (proc / "attr/current").read_text().removesuffix("\n") if hosted else None
        )
    except OSError as error:
        raise SystemExit(
            f"Cannot observe isolation state for {proc}: {error}"
        ) from error

    uids = status.get("Uid", "").split()
    if len(uids) != 4 or any(not re.fullmatch(r"[1-9][0-9]*", uid) for uid in uids):
        raise SystemExit(
            f"{proc}: expected non-root real/effective/saved/fs UIDs; got {uids}"
        )
    caps = {key: status.get(key, "").strip() for key in ("CapEff", "CapPrm", "CapBnd")}
    if not all(re.fullmatch(r"0+", value) for value in caps.values()):
        raise SystemExit(
            f"{proc}: expected zero effective/permitted/bounding capabilities; got {caps}"
        )
    if status.get("NoNewPrivs", "").strip() != "1":
        raise SystemExit(
            f"{proc}: expected NoNewPrivs=1; got {status.get('NoNewPrivs')!r}"
        )
    if not re.fullmatch(r"net:\[[0-9]+\]", netns):
        raise SystemExit(f"{proc}: invalid network namespace token {netns!r}")
    if hosted and label != HOSTED_LABEL:
        raise SystemExit(f"{proc}: expected AppArmor {HOSTED_LABEL!r}; got {label!r}")

    evidence = (
        f"Uid real/effective/saved/fs={'/'.join(uids)}, "
        f"{', '.join(f'{key}={value}' for key, value in caps.items())}, "
        f"NoNewPrivs=1, netns={netns}, "
        f"AppArmor={label if hosted else 'not checked (local)'}"
    )
    return netns, evidence


def verify_namespace(hosted: bool, host_netns: str) -> str:
    if not re.fullmatch(r"net:\[[0-9]+\]", host_netns):
        raise SystemExit(f"Invalid host network namespace token {host_netns!r}")
    netns, evidence = process_evidence(Path("/proc/self"), hosted)
    if netns == host_netns:
        raise SystemExit(
            f"Network namespace is not isolated: {netns} is the host namespace"
        )
    try:
        interfaces = [name for _, name in socket.if_nameindex()]
        if interfaces != ["lo"]:
            raise SystemExit(f"Expected only the loopback interface; got {interfaces}")
        with (
            socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener,
            socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client,
        ):
            listener.settimeout(2)
            client.settimeout(2)
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            client.connect(listener.getsockname())
            connection, _ = listener.accept()
            connection.close()
        # UDP connect does a route lookup without sending a datagram.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            error = probe.connect_ex(("192.0.2.1", 9))
        if error != errno.ENETUNREACH:
            raise SystemExit(
                f"Expected ENETUNREACH for TEST-NET UDP route; got {error}"
            )
    except OSError as error:
        raise SystemExit(f"Network namespace probe failed: {error}") from error
    print(
        f"Verified sandbox isolation: {evidence}, host netns={host_netns}, "
        "interfaces=lo only, TCP loopback connected and accepted, "
        "TEST-NET UDP connect=ENETUNREACH (no datagram sent)",
        flush=True,
    )
    return netns


def verify_omp_process(pid, hosted, expected_netns, command):
    proc = Path("/proc") / str(pid)
    try:
        if not (proc / "exe").samefile(OMP):
            raise SystemExit(f"{command} PID {pid} did not exec the pinned OMP binary")
    except OSError as error:
        raise SystemExit(
            f"Cannot confirm OMP exec for {command} PID {pid}: {error}"
        ) from error
    netns, evidence = process_evidence(proc, hosted)
    if netns != expected_netns:
        raise SystemExit(
            f"{command} PID {pid} network namespace changed: {netns} != {expected_netns}"
        )
    print(f"Verified post-exec {command} PID {pid}: {evidence}", flush=True)


def verify_omp_cli(hosted, netns):
    # The pinned --license output exceeds the pipe, so OMP stays live until we drain it.
    pipe_size = 4096
    with subprocess.Popen(
        [OMP, "--license"],
        cwd=WORK,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        pipesize=pipe_size,
    ) as proc:
        try:
            verify_omp_process(proc.pid, hosted, netns, "OMP CLI (--license)")
            stdout, stderr = proc.communicate(timeout=10)
        except BaseException:
            proc.kill()
            raise
    if proc.returncode or len(stdout) <= pipe_size:
        raise SystemExit(
            f"OMP CLI isolation probe failed: exit={proc.returncode}, "
            f"stdout={len(stdout)} bytes, stderr={stderr[-2000:]!r}"
        )


def isolate(args):
    if "GITHUB_ACTIONS" in os.environ and not args.hosted:
        raise SystemExit("GitHub Actions requires --hosted for the OMP smoke.")
    bwrap = shutil.which("bwrap")
    omp = Path(args.omp).resolve()
    python_root = Path(sys.base_prefix).resolve()
    python = (python_root / "bin" / "python3.14").resolve()
    if sys.version_info[:2] != (3, 14) or not python.is_file():
        raise SystemExit("The OMP smoke requires CPython 3.14.")
    if not bwrap or not omp.is_file():
        raise SystemExit(
            "The OMP smoke requires Linux bubblewrap and the pinned OMP binary."
        )
    for path in (args.archive, args.npm_archive, args.skill_archive):
        if not path.is_file():
            raise SystemExit(f"Missing prebuilt archive: {path}")
    addons = []
    for option, entry, subdir in (
        ("--ponytail", args.ponytail, "pi-extension"),
        ("--context-mode", args.context_mode, "omp"),
    ):
        if entry is not None:
            entry = entry.absolute()
            if (
                entry.name != "index.js"
                or entry.parent.name != subdir
                or not entry.is_file()
            ):
                raise SystemExit(
                    f"{option} must point to the installed {subdir}/index.js."
                )
            addons += [
                "--ro-bind",
                str(entry.parent.parent.resolve()),
                f"/inputs/{option[2:]}",
            ]
    with tempfile.TemporaryDirectory(prefix="elivibe-smoke-") as tmp:
        # Verify the exact bytes that will be mounted, not a path that can change after hashing.
        pinned = Path(tmp) / "omp"
        shutil.copyfile(omp, pinned)
        with pinned.open("rb") as file:
            actual = hashlib.file_digest(file, "sha256").hexdigest()
        if actual != OMP_SHA256:
            raise SystemExit(
                f"Expected OMP {OMP_VERSION} Linux x64 SHA-256 {OMP_SHA256}; got {actual}"
            )
        pinned.chmod(0o500)
        paths = {
            "HOME": TRIAL / "home",
            "PI_CODING_AGENT_DIR": TRIAL / "agent",
            "XDG_CONFIG_HOME": TRIAL / "config",
            "XDG_DATA_HOME": TRIAL / "data",
            "XDG_CACHE_HOME": TRIAL / "cache",
            "XDG_STATE_HOME": TRIAL / "state",
            "TMPDIR": TRIAL / "tmp",
        }
        command = [
            bwrap,
            "--unshare-all",
            "--unshare-net",
            "--clearenv",
            "--die-with-parent",
            "--new-session",
            "--cap-drop",
            "ALL",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            str(TRIAL),
            "--symlink",
            str(paths["TMPDIR"]),
            "/tmp",
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            str(pinned),
            OMP,
            "--ro-bind",
            str(args.archive.resolve()),
            "/inputs/candidate.tar.gz",
            "--ro-bind",
            str(args.npm_archive.resolve()),
            "/inputs/candidate.tgz",
            "--ro-bind",
            str(args.skill_archive.resolve()),
            "/inputs/standalone.zip",
            "--ro-bind",
            str(Path(__file__).resolve()),
            "/inputs/smoke.py",
            "--setenv",
            "PATH",
            "/usr/bin",
            "--setenv",
            "LANG",
            "C.UTF-8",
            *addons,
        ]
        if not python_root.is_relative_to("/usr"):
            command += [
                "--ro-bind",
                str(python_root),
                str(python_root),
                "--setenv",
                "LD_LIBRARY_PATH",
                str(python_root / "lib"),
            ]
        for alias in ("/bin", "/lib", "/lib64"):
            command += (
                ["--symlink", os.readlink(alias), alias]
                if Path(alias).is_symlink()
                else ["--ro-bind", alias, alias]
            )
        for name, path in paths.items():
            command += ["--setenv", name, str(path), "--dir", str(path)]
        command += [
            "--setenv",
            "SMOKE_HOST_NETNS",
            os.readlink("/proc/self/ns/net"),
            "--chdir",
            str(TRIAL),
            "--",
            str(python),
            "-IB",
            "/inputs/smoke.py",
            "--isolated",
            "hosted" if args.hosted else "local",
        ]
        subprocess.run(command, stdin=subprocess.DEVNULL, check=True, timeout=90)


class Sink(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Authorization") is None:
            if self.path == "/elivibe":
                self.server.registry_hits.append(self.path)
                self.reply(
                    "application/json", json.dumps(self.server.packument).encode()
                )
                return
            if self.path in self.server.tarballs:
                self.server.registry_hits.append(self.path)
                self.reply("application/octet-stream", self.server.tarballs[self.path])
                return
        self.reject()

    def do_POST(self):
        if (
            self.path != "/v1/chat/completions"
            or self.headers.get("Authorization") is not None
        ):
            self.reject()
            return
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append(payload)
        if (
            payload.get("model") != PRIMARY
            or payload.get("stream") is not True
            or not self.server.replies
        ):
            self.reject("unexpected inference request")
            return
        response = self.server.replies.pop(0)
        if isinstance(response, Path):
            schemas = {
                tool["function"]["name"]: tool["function"]["parameters"]
                for tool in payload.get("tools", [])
            }
            if schemas and payload.get("tool_choice") != "none":
                if "write" not in schemas:
                    self.reject("tools advertised, but synthetic write unavailable")
                    return
                arguments = {"path": str(response), "content": "Synthetic fixture.\n"}
                if "i" in schemas["write"].get("required", []):
                    arguments["i"] = "Writing synthetic fixture"
                delta = {
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": f"smoke-{response.stem}",
                            "type": "function",
                            "function": {
                                "name": "write",
                                "arguments": json.dumps(arguments),
                            },
                        }
                    ]
                }
                finish = "tool_calls"
            else:
                # A provider-level no-tools choice needs no simulated call.
                delta, finish = {"content": self.server.replies.pop(0)}, "stop"
        else:
            delta, finish = {"content": response}, "stop"
        chunks = []
        for data, reason in (({"role": "assistant", **delta}, None), ({}, finish)):
            chunk = {
                "id": "local",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": PRIMARY,
                "choices": [{"index": 0, "delta": data, "finish_reason": reason}],
            }
            chunks.append(f"data: {json.dumps(chunk)}\n\n")
        self.reply("text/event-stream", ("".join(chunks) + "data: [DONE]\n\n").encode())

    def reply(self, content_type, body):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def reject(self, reason="unexpected endpoint or authorization"):
        self.server.unexpected.append((self.command, self.path, reason))
        self.send_error(400)

    do_CONNECT = reject

    def log_message(self, *_args):
        pass


def message_text(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return "".join(part["text"] for part in content if part["type"] == "text")


def shows(output, text):
    return json.dumps(text)[1:-1] in output


class Rpc:
    def __init__(self, extensions, *, hosted, netns):
        self.extensions = extensions
        self.hosted = hosted
        self.netns = netns
        self.frames = queue.Queue()
        self.transcript = []
        self.sequence = 0

    def __enter__(self):
        self.stderr = tempfile.TemporaryFile()
        proc = None
        try:
            proc = self.proc = subprocess.Popen(
                [
                    OMP,
                    "--mode=rpc",
                    "--offline",
                    "--no-rules",
                    "--no-context-files",
                    "--no-title",
                    "--no-judge",
                    "--no-spotlight",
                    "--no-lsp",
                    "--approval-mode=yolo",
                    f"--model=loopback/{PRIMARY}",
                    *(f"--extension={path}" for path in self.extensions),
                ],
                cwd=WORK,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.stderr,
            )
            # Keep stdin open and send no RPC requests until the live OMP is checked.
            verify_omp_process(proc.pid, self.hosted, self.netns, "OMP RPC")
            self.reader = threading.Thread(target=self.read, daemon=True)
            self.reader.start()
        except BaseException:
            try:
                if proc is not None:
                    with proc:
                        proc.kill()
            finally:
                self.stderr.close()
            raise
        return self

    def __exit__(self, typ, _value, _trace):
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.reader.join(timeout=1)
        self.proc.stdout.close()
        if typ or self.proc.returncode:
            self.stderr.seek(0)
            sys.stderr.write(self.stderr.read().decode(errors="replace")[-3000:])
        self.stderr.close()
        if not typ:
            assert self.proc.returncode == 0, f"OMP exited with {self.proc.returncode}"

    def read(self):
        for line in self.proc.stdout:
            try:
                self.frames.put(json.loads(line))
            except ValueError:
                self.frames.put(
                    {"type": "invalid-json", "line": line.decode(errors="replace")}
                )
        self.frames.put({"type": "eof"})

    def receive(self, predicate):
        deadline = monotonic() + 10
        while monotonic() < deadline:
            try:
                frame = self.frames.get(timeout=max(0, deadline - monotonic()))
            except queue.Empty:
                break
            self.transcript.append(frame)
            assert frame["type"] not in {"extension_error", "invalid-json", "eof"}, (
                frame
            )
            if predicate(frame):
                return frame
        raise AssertionError(
            f"RPC timed out; recent frame types: {[f['type'] for f in self.transcript[-10:]]}"
        )

    def submit(self, kind, **fields):
        self.sequence += 1
        id_ = str(self.sequence)
        self.proc.stdin.write(
            (json.dumps({"id": id_, "type": kind, **fields}) + "\n").encode()
        )
        self.proc.stdin.flush()
        return id_

    def response(self, id_):
        response = self.receive(
            lambda f: f.get("id") == id_ and f["type"] == "response"
        )
        assert response["success"], response
        return response.get("data") or {}

    def request(self, kind, **fields):
        return self.response(self.submit(kind, **fields))

    def prompt(self, message):
        start = len(self.transcript)
        response = self.request("prompt", message=message)
        if response.get("agentInvoked") is not False:
            id_ = str(self.sequence)
            already_seen = next(
                (
                    f
                    for f in self.transcript[start:]
                    if f["type"] == "prompt_result" and f.get("id") == id_
                ),
                None,
            )
            result = already_seen or self.receive(
                lambda f: f.get("id") == id_ and f["type"] == "prompt_result"
            )
            assert result["status"] == "completed", result
            if result["agentInvoked"] and not result["sessionSettled"]:
                self.receive(lambda f: f["type"] == "session_settled")
        # Capture the settled native transcript instead of relying on streamed text.
        entries = self.request("get_entries")
        return json.dumps([self.transcript[start:], entries])

    def commands(self):
        commands = self.request("get_available_commands")["commands"]
        by_name = {command["name"].lstrip("/"): command for command in commands}
        for name in ("elivibe", "skill:elivibe"):
            assert sum(command["name"].lstrip("/") == name for command in commands) <= 1
        return by_name


def configure(port):
    agent = Path(os.environ["PI_CODING_AGENT_DIR"])
    config = {
        "memory": {"backend": "off"},
        "autolearn": {"enabled": False},
        "compaction": {"enabled": False, "midTurnEnabled": False},
        "retry": {"enabled": False, "modelFallback": False},
        "update": {"auto": False},
        "advisor": {"enabled": False},
        "prewalk": {"enabled": False},
    }
    base = f"http://127.0.0.1:{port}"
    (Path.home() / ".npmrc").write_text(f"registry={base}/\n")
    (agent / "config.yml").write_text(json.dumps(config))
    (agent / "models.yml").write_text(
        json.dumps(
            {
                "providers": {
                    "loopback": {
                        "api": "openai-completions",
                        "baseUrl": f"{base}/v1",
                        "authHeader": False,
                        "auth": "none",
                        "models": [
                            {
                                "id": PRIMARY,
                                "name": PRIMARY,
                                "reasoning": False,
                                "input": ["text"],
                                "contextWindow": 32000,
                                "maxTokens": 1000,
                                "cost": dict.fromkeys(
                                    ("input", "output", "cacheRead", "cacheWrite"), 0
                                ),
                            }
                        ],
                    },
                }
            }
        )
    )


def native(*args):
    result = subprocess.run(
        [OMP, *args],
        cwd=WORK,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, (args, result.stderr[-2000:])
    return result.stdout


def unpack(spec, root):
    root.mkdir()
    with tarfile.open(spec, "r:gz") as archive:
        members = archive.getmembers()
        assert len({member.name for member in members}) == len(members), spec
        assert all(member.isfile() or member.isdir() for member in members), spec
        archive.extractall(root, filter="data")


def payload(root, *, npm=False):
    files = {}
    for path in root.rglob("*"):
        assert not path.is_symlink(), path
        if not path.is_dir():
            assert path.is_file(), path
            files[path.relative_to(root)] = path.read_bytes()
    expected = {Path("package.json"), Path("LICENSE"), ADAPTER, CORE, SKILL}
    if npm:
        expected.add(Path("README.md"))
    assert files.keys() in (expected, expected | {Path("NOTICE")}), root
    manifest = json.loads(files[Path("package.json")])
    assert manifest["name"] == "elivibe" and manifest["license"] == "MIT"
    assert manifest.get("omp") == {"extensions": [f"./{ADAPTER}"]}, manifest
    assert not manifest.get("private") and not manifest.get("dependencies"), manifest
    assert not manifest.get("scripts"), manifest
    skill = files[SKILL]
    assert skill.startswith(b"---\n")
    assert b"disable-model-invocation: true" in skill.split(b"---", 2)[1].splitlines()
    return manifest, files


def stage_registry(sink, manifest):
    name, version = manifest["name"], manifest["version"]
    previous = "0.0.0-smoke.1"
    assert version != previous
    archive = Path("/inputs/candidate.tgz")
    fixture = io.BytesIO()
    # Only the fixture manifest version differs; initial install uses the exact npm pack bytes.
    with (
        tarfile.open(archive, "r:gz") as source,
        tarfile.open(fileobj=fixture, mode="w:gz") as destination,
    ):
        for member in source:
            if member.name == "package/package.json":
                body = json.dumps({**manifest, "version": previous}).encode()
                member.size = len(body)
                destination.addfile(member, io.BytesIO(body))
            elif member.isfile():
                with source.extractfile(member) as data:
                    destination.addfile(member, data)
            else:
                destination.addfile(member)
    versions = {}
    for number, body in (
        (version, archive.read_bytes()),
        (previous, fixture.getvalue()),
    ):
        route = f"/{name}/-/{name}-{number}.tgz"
        sink.tarballs[route] = body
        versions[number] = {
            **manifest,
            "version": number,
            "dist": {
                "tarball": f"http://127.0.0.1:{sink.server_port}{route}",
                "shasum": hashlib.sha1(body, usedforsecurity=False).hexdigest(),
                "integrity": "sha512-"
                + base64.b64encode(hashlib.sha512(body).digest()).decode(),
            },
        }
    sink.packument = {
        "name": name,
        "dist-tags": {"latest": version},
        "versions": versions,
    }
    return version, previous


def exercise(sink, peers, *, hosted, netns):
    expected_requests = 0

    def registration():
        listing = json.loads(native("plugin", "list", "--json"))
        assert not listing["marketplace"], listing
        names = {plugin["name"]: plugin for plugin in listing["npm"]}
        assert len(names) == len(listing["npm"]), names
        return names

    def assert_registration(version=None):
        plugins = registration()
        assert plugins.pop("smoke-unrelated") == unrelated_registration
        if version is None:
            assert not plugins, plugins
            return None
        plugin = plugins.pop("elivibe")
        assert not plugins and plugin["enabled"] and plugin["version"] == version, (
            plugin
        )
        return Path(plugin["path"])

    def discovery(rpc, *, adapter=False, skill=False):
        commands = rpc.commands()
        assert commands["smoke-unrelated"]["source"] == "extension"
        for name, source, present in (
            ("elivibe", "extension", adapter),
            ("skill:elivibe", "skill", skill),
        ):
            if present:
                assert commands[name]["source"] == source, commands[name]
            else:
                assert name not in commands, commands

    def texts(call, role):
        return [
            message_text(msg["content"])
            for msg in call["messages"]
            if msg["role"] == role
        ]

    def step(rpc, prompt, *replies, policy=None, depth=None, optional_veto=False):
        nonlocal expected_requests
        assert not sink.replies and not sink.unexpected, sink.unexpected
        first = len(sink.requests)
        sink.replies.extend(replies)
        output = rpc.prompt(prompt)
        calls = sink.requests[first:]
        count = len(replies)
        if (
            optional_veto
            and calls
            and (not calls[0].get("tools") or calls[0].get("tool_choice") == "none")
        ):
            count -= 1
        assert len(calls) == count and not sink.replies and not sink.unexpected, (
            prompt,
            len(calls),
            count,
            sink.unexpected,
        )
        expected_requests += count
        for index, call in enumerate(calls, first + 1):
            instructions = "\n".join(texts(call, "system") + texts(call, "developer"))
            wire = [
                (message["role"], message_text(message.get("content")))
                for message in call["messages"]
            ]
            for marker in (EXPLICIT, LIGHT, FULL):
                assert instructions.count(marker) == int(marker == policy) and sum(
                    text.count(marker) for _, text in wire
                ) == int(marker == policy), (
                    prompt,
                    marker,
                    f"request {index}",
                    [
                        (
                            role,
                            text.count(marker),
                            text[-180:] if role == "tool" else text[:100],
                        )
                        for role, text in wire[-16:]
                    ],
                    [
                        [text[-180:] for text in texts(request, "tool")[-1:]]
                        for request in calls
                    ],
                    [frame.get("type") for frame in rpc.transcript[-15:]],
                )
            if depth:
                assert instructions.count(depth) == 1, (prompt, "wrong depth guidance")
            assert "SMOKE_SOURCE_REPORT" not in instructions, (
                "report copied into policy"
            )
            assert description not in instructions and str(SKILL) not in instructions, (
                prompt,
                "user-invoked skill was advertised to the model",
            )
        if replies:
            assert shows(output, replies[-1]), (prompt, "expected answer missing")
        return output, calls

    def skill_call(rpc, skill_path):
        question = "Explain why a queue commit is not proof of delivery."
        _, calls = step(rpc, f"/skill:elivibe {question}", ANSWER)
        user = texts(calls[0], "user")[-1]
        directory = re.search(r"^\[Skill directory: (.+)\]$", user, re.MULTILINE)
        assert directory and Path(directory[1]).samefile(skill_path.parent), user
        assert user.count(skill_body) == 1 and question in user, user

    def explicit(
        rpc, prompt, reply, *, previous, deepen=None, combined=False, veto=False
    ):
        prior = texts(rpc.request("get_messages"), "assistant")
        source_position = prior.index(previous[0]) + 1
        replies = (Path("must-not-write.txt"), reply) if veto else (reply,)
        _, calls = step(rpc, prompt, *replies, policy=EXPLICIT, optional_veto=veto)
        for call in calls:
            assistants = texts(call, "assistant")
            for text in previous:
                assert assistants.count(text) == 1, (
                    prompt,
                    "source or prior explanation changed",
                )
            instructions = "\n".join(texts(call, "system") + texts(call, "developer"))
            assert f"The selected source is assistant message {source_position} (" in (
                instructions
            ), (prompt, "eliVibe selected the wrong source")
            if deepen is not None:
                position = prior.index(deepen) + 1
                assert (
                    f"Deepen assistant message {position} without treating the explanation "
                    "as verified evidence." in instructions
                ), (prompt, "eliVibe selected the wrong prior explanation")
            assert (
                "Use the report before the eliVibe heading as the source"
                in instructions
            ) == combined, (prompt, "wrong treatment of a combined answer")
            assert texts(call, "user")[-1] == prompt, (
                prompt,
                "not the actual slash request",
            )
        user = [
            message
            for message in rpc.request("get_messages")["messages"]
            if message["role"] == "user"
        ][-1]
        assert (
            user.get("attribution") == "user"
            and message_text(user["content"]) == prompt
        ), user
        if veto:
            assert not (WORK / replies[0]).exists(), (
                "explicit explanation executed a write"
            )
            if len(calls) == 2:
                assert any(TOOL_REFUSAL in text for text in texts(calls[1], "tool")), (
                    "host did not report the scoped refusal"
                )

    def native_message(rpc, text):
        found = [
            message
            for message in rpc.request("get_messages")["messages"]
            if message["role"] == "assistant"
            and message_text(message["content"]) == text
        ]
        assert len(found) == 1 and found[0]["timestamp"] > 0, (
            "original assistant report was absent, replaced or duplicated"
        )
        assert found[0]["provider"] == "loopback" and found[0]["model"] == PRIMARY
        return found[0]

    assert not registration(), "OMP did not start with an empty profile"
    consumer_file = WORK / "user-edits.txt"
    consumer_file.write_text("Keep my edits.\n")
    unrelated = TRIAL / "unrelated"
    unrelated.mkdir()
    (unrelated / "package.json").write_text(
        json.dumps(
            {
                "name": "smoke-unrelated",
                "version": "1.0.0",
                "omp": {"extensions": ["./index.ts"]},
            }
        )
    )
    (unrelated / "index.ts").write_text(
        'export default pi => pi.registerCommand("smoke-unrelated", {'
        'description: "Unrelated local registration", handler: async () => {}});\n'
    )
    native("plugin", "link", str(unrelated))
    unrelated_registration = registration()["smoke-unrelated"]

    unpack("/inputs/candidate.tar.gz", TRIAL / "native")
    unpack("/inputs/candidate.tgz", TRIAL / "npm")
    linked = TRIAL / "native/elivibe-omp"
    npm = TRIAL / "npm/package"
    _, native_files = payload(linked)
    npm_manifest, npm_files = payload(npm, npm=True)
    assert native_files == {
        name: data for name, data in npm_files.items() if name != Path("README.md")
    }
    native_skill = native_files[SKILL]
    portable_skill = "elivibe/SKILL.md"
    portable_codex = "elivibe/agents/openai.yaml"
    with ZipFile("/inputs/standalone.zip") as archive:
        expected = [portable_skill, portable_codex, "LICENSE"]
        if Path("NOTICE") in native_files:
            expected.append("NOTICE")
            assert archive.read("NOTICE") == native_files[Path("NOTICE")]
        assert archive.namelist() == expected
        assert archive.read(portable_skill) == native_skill
        assert archive.read(portable_codex) == CODEX_POLICY
        assert archive.read("LICENSE") == native_files[Path("LICENSE")]
    _, frontmatter, body = native_skill.decode().split("---", 2)
    description = next(
        line.removeprefix("description: ")
        for line in frontmatter.splitlines()
        if line.startswith("description: ")
    )
    skill_body = body.strip()

    native("plugin", "link", str(linked))
    version, previous = stage_registry(sink, npm_manifest)

    def assert_install(number):
        root = assert_registration(number)
        manifest, files = payload(root, npm=True)
        if number == version:
            assert files == npm_files
        else:
            assert files.keys() == npm_files.keys()
            assert manifest == {**npm_manifest, "version": number}
            assert all(
                data == npm_files[name]
                for name, data in files.items()
                if name != Path("package.json")
            )
        return root

    assert assert_registration(version).samefile(linked)
    with Rpc(peers, hosted=hosted, netns=netns) as rpc:
        discovery(rpc, adapter=True, skill=True)
        step(
            rpc, "Return an ordinary answer without teaching.", "SMOKE_LINKED_ORDINARY"
        )
        skill_call(rpc, linked / SKILL)
    linked_edit = linked / "owner-note.txt"
    linked_edit.write_text("Editable linked checkout.\n")
    native("plugin", "uninstall", "elivibe")
    assert_registration()
    assert linked_edit.read_text() == "Editable linked checkout.\n"
    assert (linked / SKILL).read_bytes() == native_skill

    native("plugin", "install", f"elivibe@{version}")
    installed = assert_install(version)
    assert not installed.samefile(linked) and not installed.samefile(npm)
    native("plugin", "uninstall", "elivibe")
    assert_registration()
    native("plugin", "install", f"elivibe@{previous}")
    assert_install(previous)
    for number in (version, previous):
        native("plugin", "install", f"elivibe@{number}", "--force")
        root = assert_install(number)
        with Rpc(peers, hosted=hosted, netns=netns) as rpc:
            discovery(rpc, adapter=True, skill=True)
            skill_call(rpc, root / SKILL)
    for number in (version, previous):
        assert f"/elivibe/-/elivibe-{number}.tgz" in sink.registry_hits, (
            sink.registry_hits
        )

    native("plugin", "uninstall", "elivibe")
    assert_registration()
    assert not installed.exists(), "the npm installation remained after removal"
    with Rpc(peers, hosted=hosted, netns=netns) as rpc:
        discovery(rpc)
        step(rpc, "Answer after removing the npm plugin.", "SMOKE_ADAPTER_REMOVED")
    print(
        f"Registry lifecycle: fresh {version}, fixture {previous} → {version} → {previous}, "
        "uninstalled; kept the unrelated registration.",
        flush=True,
    )
    native("plugin", "install", f"elivibe@{version}")
    assert_install(version)

    with Rpc(peers, hosted=hosted, netns=netns) as rpc:
        discovery(rpc, adapter=True, skill=True)
        if "ponytail" in rpc.commands():
            step(rpc, "/ponytail full")
        step(rpc, "/elivibe")
        # Default Manual: ordinary work retains the real tools and does not activate eliVibe.
        start = "Write source.txt as a fixture and report what the queue commit proves."
        _, work_calls = step(rpc, start, Path("source.txt"), ORIGINAL)
        assert (WORK / "source.txt").read_text() == "Synthetic fixture.\n"
        assert texts(work_calls[-1], "tool"), (
            "ordinary work did not receive a tool result"
        )
        report = native_message(rpc, ORIGINAL)
        tool_names = {tool["function"]["name"] for tool in work_calls[0]["tools"]}
        if any("context-mode" in path for path in peers):
            assert {"ctx_execute", "ctx_search"} <= tool_names, tool_names
        if any("ponytail" in path for path in peers):
            assert "PONYTAIL MODE ACTIVE" in "\n".join(texts(work_calls[0], "system"))

        first = SECTION.lstrip("\n") + ANSWER
        followup = SECTION.lstrip("\n") + FOLLOWUP
        more = SECTION.lstrip("\n") + MORE
        explicit(rpc, "/elivibe", first, previous=(ORIGINAL,), veto=True)
        explanation = native_message(rpc, first)
        explicit(
            rpc,
            "/elivibe Why could replay happen after application?",
            followup,
            previous=(ORIGINAL, first),
        )
        explicit(
            rpc,
            "/elivibe more",
            more,
            previous=(ORIGINAL, first, followup),
            deepen=followup,
        )
        assert native_message(rpc, ORIGINAL) == report
        assert native_message(rpc, first) == explanation
        question = "Does the report say that the subscriber actually applied the event?"
        _, calls = step(
            rpc, question, "SMOKE_ORDINARY_FOLLOWUP: No, that was not verified."
        )
        assert texts(calls[0], "user")[-1] == question
        assert all(
            text in texts(calls[0], "assistant") for text in (ORIGINAL, first, followup)
        )
        explicit(
            rpc,
            "/elivibe more",
            SECTION.lstrip("\n") + "SMOKE_MORE_AFTER_ORDINARY_QUESTION",
            previous=(ORIGINAL, more),
            deepen=more,
        )

        for mode, policy in (("light", LIGHT), ("full", FULL)):
            step(rpc, f"/elivibe {mode}")
            name = f"{mode}.txt"
            source = (
                f"SMOKE_{mode.upper()}_SOURCE: Wrote the fixture, but ran no tests."
            )
            answer = (
                source
                + SECTION
                + f"SMOKE_{mode.upper()}_EXPLANATION: A write does not test the reader."
            )
            step(
                rpc,
                f"Write {name} and hand back the result.",
                Path(name),
                answer,
                policy=policy,
            )
            assert (WORK / name).read_text() == "Synthetic fixture.\n"
            native_message(rpc, answer)
        explicit(
            rpc,
            "/elivibe more",
            SECTION.lstrip("\n") + "SMOKE_FULL_MORE",
            previous=(answer,),
            deepen=answer,
            combined=True,
        )
        step(rpc, "Only output JSON. No eliVibe.", '{"status":"SMOKE_FORMAT"}')
        auto = "Choose the level of detail appropriate to the actual concept."
        for depth, guidance in (
            (
                "brief",
                "Prefer a brief explanation without omitting a necessary distinction.",
            ),
            (
                "detailed",
                "Explain the relevant mechanism and tradeoffs in more depth when supported.",
            ),
            ("adaptive", auto),
            ("auto", auto),
        ):
            step(rpc, f"/elivibe depth {depth}")
            step(
                rpc,
                "Return a report at this depth.",
                f"SMOKE_DEPTH_{depth}",
                policy=FULL,
                depth=guidance,
            )

        step(rpc, "/elivibe off")
        off_report = "SMOKE_OFF_SOURCE: This is a report in Off mode."
        step(rpc, "Return a report in Off mode.", off_report)
        explicit(
            rpc,
            "/elivibe",
            SECTION.lstrip("\n") + "SMOKE_OFF_EXPLANATION",
            previous=(off_report,),
        )
        for retired in ("model", "judge", "consent", "judge-consent"):
            output, _ = step(rpc, f"/elivibe {retired}")
            assert "retired" in output.lower() or "no longer" in output.lower(), (
                retired,
                "missing migration notice",
            )

    native("plugin", "uninstall", "elivibe")
    assert_registration()
    assert not installed.exists(), "the npm installation remained after removal"

    standalone = Path.home() / ".agents" / SKILL
    codex = Path.home() / ".agents" / CODEX_SKILL
    codex.parent.mkdir(parents=True)
    with ZipFile("/inputs/standalone.zip") as archive:
        standalone.write_bytes(archive.read(portable_skill))
        codex.write_bytes(archive.read(portable_codex))
    with Rpc(peers, hosted=hosted, netns=netns) as rpc:
        discovery(rpc, skill=True)
        step(
            rpc,
            "Answer without invoking the hidden skill.",
            "SMOKE_STANDALONE_ORDINARY",
        )
        skill_call(rpc, standalone)
    codex.unlink()
    codex.parent.rmdir()
    standalone.unlink()
    with Rpc(peers, hosted=hosted, netns=netns) as rpc:
        discovery(rpc)
    assert_registration()
    assert linked_edit.read_text() == "Editable linked checkout.\n"
    assert consumer_file.read_text() == "Keep my edits.\n"
    assert {path.name for path in WORK.iterdir()} == {
        "user-edits.txt",
        "source.txt",
        "light.txt",
        "full.txt",
    }
    assert (
        len(sink.requests) == expected_requests
        and not sink.unexpected
        and not sink.replies
    )
    print(
        f"OMP {OMP_VERSION} synthetic localhost: {expected_requests} ordinary streaming requests, "
        "no authorization or separate route; explicit explanation tools did not run, "
        "normal work retained its tools. Original report and exact follow-up context remained in the session."
    )
    print(
        "Native link and standalone skill discovery/removal passed; consumer files preserved."
    )
    if peers:
        print(
            "Optional interoperability: "
            + ", ".join(Path(path).parts[2] for path in peers)
        )


def isolated(hosted: bool):
    os.environ.pop(
        "LD_LIBRARY_PATH", None
    )  # Only the sandbox's Python startup needs its private runtime.
    netns = verify_namespace(hosted, os.environ.get("SMOKE_HOST_NETNS", ""))
    required = (
        "HOME",
        "PI_CODING_AGENT_DIR",
        "TMPDIR",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_CACHE_HOME",
        "XDG_STATE_HOME",
    )
    assert all(Path(os.environ[key]).is_relative_to(TRIAL) for key in required)
    assert all(not list(Path(os.environ[key]).iterdir()) for key in required), (
        "profile paths must start empty"
    )
    WORK.mkdir()
    verify_omp_cli(hosted, netns)
    version_output = native("--version")
    assert re.search(
        rf"(?<![\d.]){re.escape(OMP_VERSION)}(?![\w.-])", version_output
    ), version_output
    with ThreadingHTTPServer(("127.0.0.1", 0), Sink) as sink:
        sink.requests = []
        sink.replies = []
        sink.unexpected = []
        sink.registry_hits = []
        sink.packument = {}
        sink.tarballs = {}
        configure(sink.server_port)
        threading.Thread(target=sink.serve_forever, daemon=True).start()
        try:
            exercise(
                sink,
                [
                    path
                    for path in (
                        "/inputs/ponytail/pi-extension/index.js",
                        "/inputs/context-mode/omp/index.js",
                    )
                    if Path(path).is_file()
                ],
                hosted=hosted,
                netns=netns,
            )
        finally:
            sink.shutdown()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-hosted-namespace":
        verify_namespace(True, sys.argv[2])
    elif sys.argv[1:] in (["--isolated", "hosted"], ["--isolated", "local"]):
        isolated(sys.argv[2] == "hosted")
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--omp", default=shutil.which("omp") or "omp")
        parser.add_argument(
            "--archive", type=Path, required=True, help="verified candidate archive"
        )
        parser.add_argument(
            "--npm-archive",
            type=Path,
            required=True,
            help="candidate .tgz from npm pack --ignore-scripts --offline",
        )
        parser.add_argument(
            "--skill-archive",
            type=Path,
            required=True,
            help="verified standalone skill ZIP",
        )
        parser.add_argument("--ponytail", type=Path)
        parser.add_argument("--context-mode", type=Path)
        parser.add_argument(
            "--hosted", action="store_true", help="require the hosted AppArmor profile"
        )
        isolate(parser.parse_args())
