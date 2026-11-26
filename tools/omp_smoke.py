"""Exercise candidate archives in real, network-isolated OMP with synthetic inference."""

import argparse
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import monotonic, sleep
from zipfile import ZipFile

OMP_VERSION = "19.2.1"
# GitHub can1357/oh-my-pi v19.2.1, omp-linux-x64 release asset.
OMP_SHA256 = "e8b937f9bf023baa147bdd300ad5421af0a6ef8b1f350c47a9a93d5fca94feca"
TRIAL = Path("/trial")
WORK = TRIAL / "work"
OMP = "/runtime/omp"
PRIMARY, JUDGE, REWRITE = "smoke-primary", "smoke-judge", "smoke-rewrite"
METHOD = "Keep the technical report authoritative."
HINT_PROMPT = (
    "Compress into one routing hint of at most 12 words: WHEN to use; WHEN NOT only if it prevents confusion. "
    "Retain recognizable trigger words. Do not restate the skill name or market it. "
    "Output one line without bullets or quotes.\n\nSkill: elivibe\nDescription: "
)
SKILL_HINT = "Explain why technical results matter after a handoff."
MANUAL_TASK = (
    "SMOKE_EDIT_MANUAL: Write the fixture and hand back the result. Focus on why a queue commit "
    "does not prove the subscriber saw the event."
)
UNRELATED = "SMOKE_UNRELATED_CANARY"
REDACTION_CANARY = "ghp_A0b1C2d3E4f5G6h7I8j9K0l1M2n3O4p5Q6r7S8t9"
AUTH_PROBE = TRIAL / "auth-probe"
PROXY_ROUTE = "https://smoke.invalid/v1"  # Nonlocal, so OMP does not bypass the proxy.
# Loopback userinfo detects leaks.
PROXY_CANARY = "http://smoke-proxy-canary@127.0.0.1:9"
FULL_SECTION = "\n\n## eliVibe explanation\n\n"
EDIT = re.compile(r"SMOKE_EDIT_([A-Z]+)")


def isolate(args):
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
    for path in (args.archive, args.update_archive, args.skill_archive):
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
            str(args.update_archive.resolve()),
            "/inputs/update.tar.gz",
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
        ]
        subprocess.run(command, stdin=subprocess.DEVNULL, check=True, timeout=90)


class Sink(BaseHTTPRequestHandler):
    def handle(self):
        self.server.connections.append(self.client_address)
        super().handle()

    def do_GET(self):
        self.server.unexpected.append(
            (self.path, self.headers.get("Authorization") is not None)
        )
        self.send_error(400)

    do_CONNECT = do_GET

    def do_POST(self):
        if (
            self.path != "/v1/chat/completions"
            or self.headers.get("Authorization") is not None
        ):
            self.server.unexpected.append(
                (self.path, self.headers.get("Authorization") is not None)
            )
            self.send_error(400)
            return
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        model = payload["model"]
        finish = "stop"
        is_skill_hint = (
            model == PRIMARY
            and payload["messages"]
            == [{"role": "user", "content": self.server.hint_request}]
            and not payload.get("tools")
        )
        if payload.get("stream") is False and not is_skill_hint:
            if not self.server.followups:
                source = message_text(payload["messages"][-1]["content"])
                marker = re.search(r"SMOKE_ORIGINAL_[A-Z]+", source)
                self.server.unexpected.append(
                    ("unplanned isolated request", model, marker[0] if marker else "")
                )
                self.send_error(400)
                return
            expected_model, marker = self.server.followups.pop(0)
            assert model == expected_model, (expected_model, model)
            self.server.requests.append(payload)
            self.server.served.append(
                ("judge" if model == JUDGE else "explain", marker)
            )
            if marker == "CANCEL":
                self.server.cancel_started.set()
                assert self.server.cancel_release.wait(6), (
                    "test did not release held judgment"
                )
            if marker == "REDIRECT":
                self.send_response(307)
                self.send_header("Location", "/redirect-catcher")
                self.end_headers()
                return
            if model == JUDGE:
                text = {"ANSWER": "skip", "INVALID": "malformed choice"}.get(
                    marker, "brief"
                )
            else:
                text = supplement(marker)
            body = {
                "choices": [
                    {
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": finish,
                    }
                ]
            }
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())
            except ConnectionError:
                if marker != "CANCEL":
                    raise
            finally:
                if marker == "CANCEL":
                    self.server.cancel_replied.set()
            return
        (
            self.server.skill_hint_requests if is_skill_hint else self.server.requests
        ).append(payload)
        if is_skill_hint:
            delta = {"content": SKILL_HINT}
        else:
            assert model == PRIMARY, f"unexpected model {model}"
            last = payload["messages"][-1]
            marker = next(
                (
                    match[1]
                    for message in reversed(payload["messages"])
                    if (match := EDIT.search(json.dumps(message)))
                    and message["role"] == "user"
                ),
                None,
            )
            if marker and last["role"] == "user" and EDIT.search(json.dumps(last)):
                schema = next(
                    tool["function"]["parameters"]
                    for tool in payload["tools"]
                    if tool["function"]["name"] == "write"
                )
                arguments = {
                    "path": f"{marker}.txt",
                    "content": f"SMOKE_DATA_{marker}\n",
                }
                if "i" in schema.get("required", []):
                    arguments["i"] = "Writing synthetic fixture"
                delta = {
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": f"smoke-{marker}",
                            "type": "function",
                            "function": {
                                "name": "write",
                                "arguments": json.dumps(arguments),
                            },
                        }
                    ]
                }
                finish = "tool_calls"
            elif marker and last["role"] == "tool":
                report = original(marker)
                if self.server.full:
                    report += FULL_SECTION + supplement(marker)
                delta = {"content": report}
            elif "SMOKE_REVIEW" in json.dumps(last):
                delta = {"content": original("REVIEW")}
            elif "SMOKE_FULL_SINGLE" in json.dumps(last):
                delta = {
                    "content": original("REVIEW") + FULL_SECTION + supplement("SINGLE")
                }
            elif "SMOKE_OPTOUT" in json.dumps(last):
                delta = {"content": original("OPTOUT")}
            elif "SMOKE_FORMAT" in json.dumps(last):
                delta = {"content": original("FORMAT")}
            else:
                delta = {"content": original("ANSWER")}
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk, reason in (({"role": "assistant", **delta}, None), ({}, finish)):
            data = {
                "id": "local",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": model,
                "choices": [{"index": 0, "delta": chunk, "finish_reason": reason}],
            }
            self.wfile.write(f"data: {json.dumps(data)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, *_args):
        pass


def long_handoff():
    cuts = (
        (
            "before encoding",
            "no frame exists",
            "the caller receives the original encoding error",
        ),
        (
            "after encoding",
            "only process memory has the frame",
            "a restart loses the frame",
        ),
        (
            "before append",
            "only a sequence number is reserved",
            "a gap is legal in the journal",
        ),
        (
            "during append",
            "the journal has a partial frame",
            "recovery stops at the checksum mismatch",
        ),
        (
            "after append",
            "the kernel can read the frame",
            "readability alone does not establish durability",
        ),
        (
            "before sync",
            "the journal still has buffered writes",
            "power-loss durability remains unproven",
        ),
        (
            "during sync",
            "the sync result is unknown",
            "the caller retries with the same event identity",
        ),
        (
            "after sync",
            "the complete frame survives restart",
            "the producer can acknowledge the append",
        ),
        (
            "before indexing",
            "the journal is ahead of the index",
            "startup rebuilds the index from the journal",
        ),
        (
            "during indexing",
            "the previous index generation remains visible",
            "readers keep a consistent view",
        ),
        (
            "after indexing",
            "the event is eligible for delivery",
            "eligibility does not prove receipt",
        ),
        (
            "before delivery",
            "the subscriber has not been called",
            "the worker can resume from its cursor",
        ),
        (
            "after delivery",
            "the subscriber may have applied the event",
            "retry can deliver the event again",
        ),
        (
            "during cursor update",
            "the durable cursor may lag delivery",
            "startup can replay the same event",
        ),
        (
            "after cursor update",
            "the worker restarts after this event",
            "cursor advance is not an end-to-end audit",
        ),
        (
            "during replay",
            "the event identity is unchanged",
            "a subscriber can use it to deduplicate work",
        ),
    )
    evidence = "\n\n".join(
        f"{index}. Crash {phase}: {state}, so {consequence}. "
        "This is an expected state transition from inspection of the control flow, not a result from a crash test. "
        "A useful follow-up would record the durable journal tail, the replay cursor, and the subscriber's observed "
        "effects separately. Comparing those observations after restart would show which boundary was crossed; "
        "a successful producer return alone cannot distinguish these cases."
        for index, (phase, state, consequence) in enumerate(cuts, 1)
    )
    return (
        "SMOKE_ORIGINAL_MANUAL: I wrote MANUAL.txt as a fixture for the queue handoff. This turn did not change "
        "the queue or run integration tests. The design under discussion separates producer acknowledgement "
        "from subscriber acknowledgement. An append receipt means the producer can stop retrying that append; "
        "it does not attest to subscriber receipt or any downstream side effect.\n\n"
        "The receipt contains the journal offset; the offset is not an acknowledgement from the subscriber.\n\n"
        "The crash windows below describe the fixture design, not production measurements. The journal "
        "checksum is checked while replaying frames; it detects a malformed tail but cannot attest to "
        "the application outcome. A cursor controls where replay resumes; it is not a receipt from the subscriber.\n\n"
        f"{evidence}\n\n"
        "The only action observed here was writing the requested fixture. Before release, test restart with "
        "subscriber delivery interrupted after acknowledgement and verify idempotency separately."
    )


def message_text(content):
    if isinstance(content, str):
        return content
    return "".join(part["text"] for part in content if part["type"] == "text")


def shows(output, text):
    return json.dumps(text)[1:-1] in output


def original(marker):
    if marker == "MANUAL":
        return long_handoff()
    if marker == "BUDGET":
        checkpoints = "\n".join(
            hashlib.sha256(f"checkpoint-{index}".encode()).hexdigest()
            for index in range(32)
        )
        return (
            long_handoff().replace("SMOKE_ORIGINAL_MANUAL", "SMOKE_ORIGINAL_BUDGET", 1)
            + "\n\nSynthetic checkpoint fingerprints, not proof of successful replay:\n"
            + checkpoints
        )
    if marker == "FORMAT":
        return '{"status":"SMOKE_FORMAT_RESULT"}'
    if marker == "SENSITIVE":
        return "SMOKE_ORIGINAL_SENSITIVE: Synthetic fixture API_KEY=smoke_fixture_only_123456."
    if marker == "REVIEW":
        return (
            "SMOKE_ORIGINAL_REVIEW: Approval is blocked until draft recovery is verified. "
            "Migration acknowledges persistence of the new draft index, not replay of the old journal entries. "
            "The migration fixture checked index construction only. Do not approve release without a replay check."
        )
    if marker == "ANSWER":
        return "SMOKE_ANSWER: The answer to this ordinary question is blue."
    return (
        f"SMOKE_ORIGINAL_{marker}: I created {marker}.txt with the requested fixture text. "
        "The file write succeeded. No tests were run; do not treat the file as tested."
    )


def supplement(marker):
    if marker == "MANUAL":
        return (
            "SMOKE_EXPLANATION_MANUAL: Think of the journal as the queue's receipt book, not the subscriber's inbox. "
            "A commit records that the event is available for replay; the subscriber is a separate reader that can "
            "fall behind or crash before applying it. A restart can therefore redeliver an event already applied, "
            "which is why applying it twice must be safe. The file write tested neither delivery nor replay."
        )
    if marker == "REVIEW":
        return (
            "SMOKE_EXPLANATION_REVIEW: Rebuilding the index is like producing a list of saved drafts. "
            "It does not open any of them. Replay is the separate step that reconstructs draft contents from "
            "the old journal, so passing the index check leaves the data-loss question open."
        )
    return (
        f"SMOKE_EXPLANATION_{marker}: A successful write means the fixture exists. It does not exercise "
        "the reader that consumes it, so it cannot show whether that reader accepts the format."
    )


class Rpc:
    def __init__(self, extensions):
        self.extensions = extensions
        self.frames = queue.Queue()
        self.transcript = []
        self.sequence = 0

    def __enter__(self):
        self.stderr = tempfile.TemporaryFile()
        self.proc = subprocess.Popen(
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
        self.reader = threading.Thread(target=self.read, daemon=True)
        self.reader.start()
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
        # Agent settlement need not wait for an extension's later supplementary message.
        entries = self.request("get_entries")
        return json.dumps([self.transcript[start:], entries])

    def commands(self):
        commands = self.request("get_available_commands")["commands"]
        by_name = {command["name"].lstrip("/"): command for command in commands}
        assert (
            sum(command["name"].lstrip("/") == "skill:elivibe" for command in commands)
            <= 1
        )
        return by_name


def configure(port, *, secrets=False):
    agent = Path(os.environ["PI_CODING_AGENT_DIR"])
    config = {
        "memory": {"backend": "off"},
        "autolearn": {"enabled": False},
        "compaction": {"enabled": False, "midTurnEnabled": False},
        "retry": {"enabled": False, "modelFallback": False},
        "update": {"auto": False},
        "advisor": {"enabled": False},
        "prewalk": {"enabled": False},
        "secrets": {"enabled": secrets},
    }

    def provider(api, url, *names, denied=False):
        auth = (
            {"apiKey": f"!touch {AUTH_PROBE}; printf smoke-probe-only"}
            if denied
            else {"auth": "none"}
        )
        return {
            "api": api,
            "baseUrl": url,
            "authHeader": False,
            **auth,
            "models": [
                {
                    "id": name,
                    "name": name,
                    "reasoning": False,
                    "input": ["text"],
                    "contextWindow": 32000,
                    "maxTokens": 500,
                    "cost": dict.fromkeys(
                        ("input", "output", "cacheRead", "cacheWrite"), 0
                    ),
                }
                for name in names
            ],
        }

    base = f"http://127.0.0.1:{port}/v1"
    (agent / "config.yml").write_text(json.dumps(config))
    (agent / "models.yml").write_text(
        json.dumps(
            {
                "providers": {
                    "loopback": provider(
                        "openai-completions", base, PRIMARY, JUDGE, REWRITE
                    ),
                    "unsupported": provider(
                        "anthropic-messages", base, "unsupported", denied=True
                    ),
                    "remote-http": provider(
                        "openai-completions",
                        f"http://192.0.2.1:{port}/v1",
                        "remote",
                        denied=True,
                    ),
                    "proxy-fixture": provider(
                        "openai-completions",
                        PROXY_ROUTE,
                        "proxied",
                        denied=True,
                    ),
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


def extract(label):
    root = TRIAL / label
    root.mkdir()
    with tarfile.open(f"/inputs/{label}.tar.gz", "r:gz") as archive:
        archive.extractall(root, filter="data")
    path = root / "elivibe-omp"
    manifest = json.loads((path / "package.json").read_text())
    assert manifest["name"] == "elivibe" and manifest["private"] is True
    skill_link = path / "skills"
    assert skill_link.is_symlink() and skill_link.readlink() == Path("skill")
    skill = path / "skill/elivibe/SKILL.md"
    assert (skill_link / "elivibe/SKILL.md").samefile(skill)
    return path, manifest["version"], skill


def exercise(sink, peers):
    expected_requests = 0
    agent = Path(os.environ["PI_CODING_AGENT_DIR"])
    profile_configs = (agent / "config.yml", agent / "models.yml")

    def check(prompt, primary=0, *, followups=(), full=False, skill=False):
        nonlocal expected_requests
        first = len(sink.requests)
        sink.followups = list(followups)
        sink.full = full
        paths_before = set(WORK.rglob("*")) if prompt.startswith("/elivibe") else None
        profile_before = (
            tuple(path.read_bytes() for path in profile_configs)
            if paths_before is not None
            else None
        )
        output = rpc.prompt(prompt)
        models = [PRIMARY] * primary + [model for model, _ in followups]
        if followups:
            last_model, marker = followups[-1]
            expected = (
                supplement(marker)
                if last_model != JUDGE and marker != "REDIRECT"
                else None
            )
            # Agent settlement does not wait for the light-mode hook or its display message.
            deadline = monotonic() + 3
            initial = output
            while len(sink.requests) < first + len(models) or (
                expected and not shows(output, expected)
            ):
                if monotonic() >= deadline:
                    break
                sleep(0.02)
                output = initial + json.dumps(rpc.request("get_entries"))
            assert not expected or shows(output, expected), (
                prompt,
                "supplement did not arrive",
            )
            if expected:
                entries = rpc.request("get_entries")["entries"]
                delivered = [
                    entry["content"]
                    for entry in entries
                    if entry.get("customType") == "elivibe-handoff"
                    and expected in entry["content"]
                ]
                assert len(delivered) == 1 and delivered[0].startswith(
                    f"eliVibe (loopback/{last_model}; supplementary"
                )
                assert "original above)" in delivered[0]
        calls = sink.requests[first:]
        actual = [call["model"] for call in calls]
        assert actual == models, (prompt, models, actual)
        expected_requests += len(models)
        assert not sink.followups, (prompt, "missing follow-up")
        if paths_before is not None:
            assert set(WORK.rglob("*")) == paths_before, (
                prompt,
                "command changed consumer paths",
            )
            assert (
                tuple(path.read_bytes() for path in profile_configs) == profile_before
            ), (prompt, "command changed native profile configuration")
        for call in calls[:primary]:
            system = "".join(
                message_text(msg["content"])
                for msg in call["messages"]
                if msg["role"] == "system"
            )
            assert system.count(METHOD) == int(full), (
                prompt,
                "canonical system prompt absent or duplicated",
            )
            if full:
                assert "visibly distinct supplement in the same response" in system
                assert SKILL_HINT in system or description[:40] in system, (
                    "native skill listing was absent in full mode"
                )
                assert (
                    "Do not read or invoke the standalone eliVibe skill again" in system
                )
            wire = json.dumps(call["messages"])
            assert wire.count(METHOD) == int(full or skill), (
                prompt,
                "standalone skill body absent or duplicated",
            )
            for marker in ("MANUAL", "ALTERNATE", "LIGHT", "REVIEW"):
                assert f"SMOKE_EXPLANATION_{marker}" not in wire, (
                    prompt,
                    "supplement leaked to model context",
                )
        for call, (model, marker) in zip(calls[primary:], followups, strict=True):
            assert call["stream"] is False and not call.get("tools"), (
                model,
                "follow-up received tools",
            )
            assert [msg["role"] for msg in call["messages"]] == ["system", "user"], (
                model,
                "follow-up received extra messages",
            )
            system, user = call["messages"]
            body = message_text(user["content"])
            assert user["content"] in (body, [{"type": "text", "text": body}]), (
                model,
                "unexpected user content parts",
            )
            assert body == original(marker).strip(), (
                model,
                "handoff changed or extra context was sent",
            )
            wire = json.dumps(call["messages"])
            assert UNRELATED not in wire and "SMOKE_DATA_MANUAL" not in wire, (
                model,
                "prior user/tool data leaked",
            )
            instructions = message_text(system["content"])
            assert instructions.count(METHOD) == int(model != JUDGE), (
                model,
                "unexpected canonical methodology count on the follow-up",
            )
            if model == JUDGE:
                assert (
                    "missing concept, relationship, or causal distinction"
                    in instructions
                )
                assert call["max_tokens"] == 16
                assert len(body.encode()) + len(instructions.encode()) <= 8192
                assert "well-written handoff" in instructions
            else:
                assert (
                    "Return only the teaching supplement, not a rewrite" in instructions
                )
                expected_budget = 350 if len(followups) == 2 else 500
                assert call["max_tokens"] == expected_budget, (
                    marker,
                    "unexpected explanation token cap",
                )
        return output, calls

    def notice(start, *parts):
        def matches(frame):
            return (
                frame["type"] == "extension_ui_request"
                and frame.get("method") == "notify"
                and all(part in frame["message"] for part in parts)
            )

        if not any(matches(frame) for frame in rpc.transcript[start:]):
            rpc.receive(matches)

    def check_notice(prompt, *parts):
        start = len(rpc.transcript)
        check(prompt)
        notice(start, *parts)

    def approve(model, *, judge=False):
        action, role = (
            ("judge-consent", "judgment") if judge else ("consent", "explanation")
        )
        command = f"/elivibe {action} {model}"
        check_notice(command, f"Review eliVibe {role} route", model, "Hide Secrets")
        check_notice(f"{command} confirm", f"Approved {model} for {role}")

    def select_primary(model):
        result = rpc.request("set_model", provider="loopback", modelId=model)
        assert result["id"] == model

    def check_skill(prompt, skill):
        _, calls = check(prompt, 1, skill=True)
        user = message_text(calls[0]["messages"][-1]["content"])
        location = re.search(r"^\[Skill directory: (.+)\]$", user, re.MULTILINE)
        assert location and Path(location[1]).samefile(skill.parent), (
            prompt,
            "wrong skill source",
        )

    def check_peers(call):
        tool_names = {tool["function"]["name"] for tool in call["tools"]}
        assert "write" in tool_names
        if any("context-mode" in peer for peer in peers):
            assert {"ctx_execute", "ctx_search"} <= tool_names, tool_names
        if any("ponytail" in peer for peer in peers):
            system = json.dumps(
                [msg for msg in call["messages"] if msg["role"] == "system"]
            )
            assert (
                "PONYTAIL MODE ACTIVE" in system
                and "Be lazy about the solution" in system
            ), "Ponytail instructions did not reach the primary model"

    def preferences():
        return [
            entry["data"]
            for entry in rpc.request("get_entries")["entries"]
            if entry.get("customType") == "elivibe-settings"
        ]

    def edit(tag, *, full=False, followups=()):
        task = (
            MANUAL_TASK
            if tag == "MANUAL"
            else f"SMOKE_EDIT_{tag}: Write the fixture and hand back the result."
        )
        output, calls = check(task, 2, full=full, followups=followups)
        assert (WORK / f"{tag}.txt").read_text() == f"SMOKE_DATA_{tag}\n"
        assert shows(output, original(tag).strip()), (tag, "original report missing")
        if full:
            assert shows(output, original(tag) + FULL_SECTION + supplement(tag)), (
                tag,
                "same-turn explanation missing",
            )
        else:
            assert shows(output, supplement(tag)) == any(
                model != JUDGE for model, _ in followups
            ), (tag, "unexpected supplemental report state")
        return calls

    def native_report(text):
        messages = [
            message
            for message in rpc.request("get_messages")["messages"]
            if message["role"] == "assistant"
            and message_text(message["content"]) == text
        ]
        assert len(messages) == 1, "original report was replaced or duplicated"
        assert (
            isinstance(messages[0]["timestamp"], int) and messages[0]["timestamp"] > 0
        )
        return messages[0]

    def registration():
        listing = json.loads(native("plugin", "list", "--json"))
        assert not listing["marketplace"], listing
        names = {plugin["name"]: plugin for plugin in listing["npm"]}
        assert len(names) == len(listing["npm"]), names
        return names

    def link(folder, version):
        native("plugin", "link", str(folder))
        plugins = registration()
        assert plugins.pop("smoke-unrelated") == unrelated_registration
        pkg = plugins.pop("elivibe")
        assert (
            not plugins
            and pkg["enabled"]
            and pkg["version"] == version
            and Path(pkg["path"]).samefile(folder)
        ), pkg

    def discovery():
        commands = rpc.commands()
        assert commands["elivibe"]["source"] == "extension"
        assert commands["skill:elivibe"]["source"] == "skill"
        assert commands["smoke-unrelated"]["source"] == "extension"

    WORK.mkdir()
    assert not registration(), "OMP did not start with an empty profile"
    (WORK / "untouched.txt").write_text("Consumer-owned file.\n")
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
        "export default pi => {\n"
        '  pi.registerCommand("smoke-unrelated", {'
        'description: "Unrelated local registration", handler: async () => {}});\n'
        # Switch through the real host while the adapter's credential lookup is pending.
        '  pi.registerCommand("smoke-model-switch", {description: "Switch the live model during credential lookup",\n'
        "    handler: async (_, ctx) => {\n"
        "      const registry = ctx.modelRegistry;\n"
        "      const getApiKey = registry.getApiKey;\n"
        "      registry.getApiKey = async (...args) => {\n"
        "        registry.getApiKey = getApiKey;\n"
        "        const key = await getApiKey.apply(registry, args);\n"
        f'        if (args[0].id !== "{PRIMARY}" || !await pi.setModel(registry.find("loopback", "{REWRITE}")))\n'
        '          throw new Error("Synthetic credential hook did not switch the active model");\n'
        f'        if (ctx.model?.id !== "{PRIMARY}" || ctx.models.current()?.id !== "{REWRITE}")\n'
        '          throw new Error("Native command snapshot/live model contract changed");\n'
        '        ctx.ui.notify("SMOKE_NATIVE_MODEL_SWITCHED", "info");\n'
        "        return key;\n"
        "      };\n"
        "    }});\n"
        '  pi.registerCommand("smoke-configure-proxy", {description: "Set a synthetic provider proxy",\n'
        f'    handler: async () => {{ process.env.PI_PROXY_PROXY_FIXTURE = "http://127.0.0.1:{sink.server_port}"; }}}});\n'
        # Warm OMP's real provider-proxy cache through its inference transport, then remove the env that produced it.
        '  pi.registerCommand("smoke-retain-proxy", {description: "Retain then remove a synthetic provider proxy",\n'
        "    handler: async (_, ctx) => {\n"
        '      const { getProxyForProvider, shouldBypassProxy } = await import("@oh-my-pi/pi-ai/utils/proxy");\n'
        '      const { transportFetch } = await import("@oh-my-pi/pi-ai/utils/transport-fetch");\n'
        f'      const proxy = "{PROXY_CANARY}";\n'
        '      const model = ctx.modelRegistry.find("proxy-fixture", "proxied");\n'
        f'      if (model?.api !== "openai-completions" || model.baseUrl !== "{PROXY_ROUTE}")\n'
        '        throw new Error("Registered proxy fixture model does not match the synthetic route");\n'
        f'      const url = "{PROXY_ROUTE}/probe";\n'
        '      if (shouldBypassProxy(new URL(url))) throw new Error("Host bypasses the synthetic proxy route");\n'
        "      const seen = [];\n"
        '      const receiver = async (_url, init) => { seen.push(init?.proxy === proxy); return new Response("{}"); };\n'
        "      process.env.PI_PROXY_PROXY_FIXTURE = proxy;\n"
        "      await transportFetch(model, receiver)(url);\n"
        "      delete process.env.PI_PROXY_PROXY_FIXTURE;\n"
        '      if (process.env.PI_PROXY_PROXY_FIXTURE !== undefined) throw new Error("Synthetic proxy environment was not removed");\n'
        '      if (getProxyForProvider("proxy-fixture") !== proxy) throw new Error("OMP resolver lost the warm proxy cache entry");\n'
        "      await transportFetch(model, receiver)(url);\n"
        '      if (seen.length !== 2 || !seen.every(Boolean)) throw new Error("OMP transport did not use the retained proxy cache");\n'
        '      ctx.ui.notify("SMOKE_PROXY_CACHE_RETAINED", "info");\n'
        "    }});\n"
        '  pi.on("session_before_switch", (_, ctx) => {\n'
        '    setImmediate(() => ctx.ui.notify("SMOKE_NATIVE_SWITCH_STARTED", "info"));\n'
        "  });\n"
        "};\n"
    )
    native("plugin", "link", str(unrelated))
    unrelated_registration = registration()["smoke-unrelated"]
    installed, version, skill = extract("candidate")
    updated, next_version, next_skill = extract("update")
    assert version != next_version, "lifecycle fixture must have a distinct version"
    description = next(
        line.removeprefix("description: ")
        for line in skill.read_text().splitlines()
        if line.startswith("description: ")
    )
    sink.hint_request = HINT_PROMPT + description
    assert skill.read_bytes() == next_skill.read_bytes(), (
        "lifecycle fixture must contain the same skill"
    )
    link(installed, version)
    with Rpc(peers) as rpc:
        discovery()
        if "ponytail" in rpc.commands():
            check("/ponytail full")
        check_notice("/elivibe status", "eliVibe: manual", "not approved")
        auto_primary = f"explanation model: auto; effective loopback/{PRIMARY}"
        override = f"explanation model: override loopback/{REWRITE}; effective loopback/{REWRITE}"
        check_notice("/elivibe model", auto_primary)
        check(f"Answer this unrelated question about colors. {UNRELATED}", 1)
        assert len(original("MANUAL")) > 6_000
        edit("MANUAL")
        report = native_report(original("MANUAL"))
        check_notice("/elivibe", "kept the original", "consent")
        primary_consent = f"/elivibe consent loopback/{PRIMARY}"
        check_notice(
            f"{primary_consent} confirm", "No matching eliVibe explanation route review"
        )
        check_notice(
            primary_consent, "Review eliVibe explanation route", "Hide Secrets"
        )
        check_notice("/elivibe", "kept the original", "consent")
        check_notice(
            f"{primary_consent} confirm", f"Approved loopback/{PRIMARY} for explanation"
        )
        output, _ = check("/elivibe", followups=[(PRIMARY, "MANUAL")])
        assert shows(output, supplement("MANUAL"))
        assert native_report(original("MANUAL")) == report
        assert not preferences(), (
            "default query or approval created eliVibe preferences"
        )
        check_notice("/elivibe", "already supplemented")

        edit("NATIVE")
        check("/smoke-model-switch")
        start = len(rpc.transcript)
        check_notice("/elivibe", "selected destination changed")
        notice(start, "SMOKE_NATIVE_MODEL_SWITCHED")
        native_report(original("NATIVE"))
        assert not shows(json.dumps(rpc.request("get_entries")), supplement("NATIVE"))

        rewrite_consent = f"/elivibe consent loopback/{REWRITE}"
        check_notice(rewrite_consent, "Review eliVibe explanation route")
        select_primary(PRIMARY)
        check_notice(f"{rewrite_consent} confirm", "exact effective provider/model")
        select_primary(REWRITE)
        check_notice(
            f"{rewrite_consent} confirm", "No matching eliVibe explanation route review"
        )
        select_primary(PRIMARY)

        check(f"/elivibe model loopback/{REWRITE}")
        check_notice("/elivibe model", override)
        check(f"/elivibe judge loopback/{JUDGE}")
        selected = preferences()
        check_notice(
            f"/elivibe model other-provider/{REWRITE}",
            "exact installed provider/model",
            "no fallback",
        )
        check_notice("/elivibe model", override)
        assert preferences() == selected, (
            "model query or rejected selector changed session preferences"
        )
        for binding, refusal in (
            ("unsupported/unsupported", "not supported for isolated requests"),
            ("remote-http/remote", "HTTPS or literal loopback HTTP"),
        ):
            for action in ("model", "judge", "consent", "judge-consent"):
                check_notice(f"/elivibe {action} {binding}", refusal)
        assert not AUTH_PROBE.exists(), "a denied route resolved credentials"
        assert preferences() == selected, "denied routes changed settings"
        edit("DENIED")
        check_notice(
            "/elivibe",
            f"No approved explanation destination for loopback/{REWRITE}",
            "consent",
        )
        approve(f"loopback/{REWRITE}")
        edit("ALTERNATE")
        select_primary(JUDGE)
        check_notice("/elivibe model", override)
        check("/elivibe", followups=[(REWRITE, "ALTERNATE")])
        select_primary(PRIMARY)
        check("/elivibe")
        edit("REDIRECT")
        start = len(rpc.transcript)
        output, _ = check("/elivibe", followups=[(REWRITE, "REDIRECT")])
        notice(start, "kept the original")
        assert not shows(output, supplement("REDIRECT"))
        native_report(original("REDIRECT"))

        check("/elivibe full")
        calls = edit("FULL", full=True)
        check_peers(calls[0])
        native_report(original("FULL") + FULL_SECTION + supplement("FULL"))
        edit("AGAIN", full=True)
        single, _ = check(
            "SMOKE_FULL_SINGLE: Hand back the fixture review without tools.",
            1,
            full=True,
        )
        single_report = original("REVIEW") + FULL_SECTION + supplement("SINGLE")
        assert shows(single, single_report), (
            "full mode did not explain in its single inference"
        )
        native_report(single_report)
        for marker, prompt in (
            ("OPTOUT", "SMOKE_OPTOUT: No eliVibe."),
            ("FORMAT", "SMOKE_FORMAT: Reply with JSON only."),
        ):
            output, _ = check(prompt, 1)
            assert shows(output, original(marker))
            native_report(original(marker))
        check("/elivibe")

        check("/elivibe light")
        edit("UNJUDGED")  # Explanation consent is not judge consent.
        approve(f"loopback/{JUDGE}", judge=True)
        negative, _ = check(
            "What color is the fixture sky?", 1, followups=[(JUDGE, "ANSWER")]
        )
        assert shows(negative, original("ANSWER")) and not shows(
            negative, supplement("ANSWER")
        )
        start = len(rpc.transcript)
        edit("INVALID", followups=[(JUDGE, "INVALID")])
        notice(start, "kept the original", "judgment")
        native_report(original("INVALID"))
        start = len(rpc.transcript)
        assert len(original("BUDGET").encode()) > 8192
        edit("BUDGET")
        notice(start, "8 KiB UTF-8 limit")
        native_report(original("BUDGET").strip())
        edit("LIGHT", followups=[(JUDGE, "LIGHT"), (REWRITE, "LIGHT")])
        native_report(original("LIGHT"))
        check("/elivibe")
        review, _ = check(
            "SMOKE_REVIEW: Hand back the fixture review; no tools are needed.",
            1,
            followups=[(JUDGE, "REVIEW"), (REWRITE, "REVIEW")],
        )
        assert shows(review, original("REVIEW")) and shows(review, supplement("REVIEW"))
        native_report(original("REVIEW"))

        select_primary(JUDGE)
        check_notice("/elivibe model", override)
        check("/elivibe model auto")
        check_notice(
            "/elivibe model", f"explanation model: auto; effective loopback/{JUDGE}"
        )
        select_primary(PRIMARY)
        check_notice("/elivibe model", auto_primary)
        approve(f"loopback/{PRIMARY}")
        edit("AUTO", followups=[(JUDGE, "AUTO"), (PRIMARY, "AUTO")])
        prior = rpc.request("get_state")["sessionFile"]
        assert prior and Path(prior).is_relative_to(TRIAL)
        edit("CANCEL", followups=[(JUDGE, "CANCEL")])
        assert sink.cancel_started.wait(2), "held judge request did not reach loopback"
        start = len(rpc.transcript)
        switch = rpc.submit("new_session")
        notice(start, "SMOKE_NATIVE_SWITCH_STARTED")
        sink.cancel_release.set()
        assert sink.cancel_replied.wait(3), "late positive judgment was not released"
        assert not rpc.response(switch)["cancelled"]
        check_notice("/elivibe status", "eliVibe: manual", "not approved")
        assert not rpc.request("switch_session", sessionPath=prior)["cancelled"]
        check_notice("/elivibe status", "eliVibe: light", "not approved")
        assert not shows(json.dumps(rpc.request("get_entries")), supplement("CANCEL"))
        native_report(original("CANCEL"))
        check_notice("/elivibe", "kept the original", "consent")
        for entry in preferences():
            assert "consent" not in entry and "judgeConsent" not in entry

        check("/elivibe off")
        edit("OFF")
        check_notice("/elivibe", "off mode does not make supplementary requests")
        check_skill(
            "/skill:elivibe Explain the fixture while the adapter is off.", skill
        )
        assert not rpc.request("new_session")["cancelled"]
        check("/elivibe full")
        check_skill("/skill:elivibe Explain the fixture in this turn.", skill)

    with Rpc(peers) as rpc:
        proxy_model = "proxy-fixture/proxied"
        check(f"/elivibe model {proxy_model}")
        approve(proxy_model)
        check("/smoke-configure-proxy")
        edit("PROXY")
        connections = len(sink.connections)
        check_notice("/elivibe", "cannot honor the process proxy")
        assert len(sink.connections) == connections, "proxy refusal opened a socket"
        assert not AUTH_PROBE.exists(), "proxy refusal resolved credentials"
        native_report(original("PROXY"))
        assert not shows(json.dumps(rpc.request("get_entries")), supplement("PROXY"))
        check("/elivibe model auto")
        approve(f"loopback/{PRIMARY}")
        check("/elivibe", followups=[(PRIMARY, "PROXY")])

    with Rpc(peers) as rpc:
        proxy_model = "proxy-fixture/proxied"
        check(f"/elivibe model {proxy_model}")
        approve(proxy_model)
        check_notice("/smoke-retain-proxy", "SMOKE_PROXY_CACHE_RETAINED")
        edit("RETAINED")
        connections = len(sink.connections)
        report_requests = len(sink.requests)
        check_notice("/elivibe", "cannot establish direct transport")
        assert len(sink.connections) == connections, "retained proxy opened a socket"
        assert len(sink.requests) == report_requests and not sink.followups, (
            "retained proxy sent a report request"
        )
        assert not AUTH_PROBE.exists(), "retained proxy resolved credentials"
        native_report(original("RETAINED"))
        entries = json.dumps(rpc.request("get_entries"))
        assert not shows(entries, supplement("RETAINED"))
        assert "smoke-proxy-canary" not in entries + json.dumps(rpc.transcript), (
            "public output exposed the synthetic proxy"
        )
        retained = (
            len(sink.connections) - connections,
            len(sink.requests) - report_requests,
        )

    configure(sink.server_port, secrets=True)
    with Rpc(peers) as rpc:
        _, calls = check(
            f"Remember this synthetic spelling fixture: {REDACTION_CANARY}", 1
        )
        assert REDACTION_CANARY not in json.dumps(calls[0]["messages"]), (
            "native Hide Secrets did not redact"
        )
        edit("HIDDEN")
        check_notice("/elivibe", "kept the original", "consent")
        native_report(original("HIDDEN"))
        approve(f"loopback/{PRIMARY}")
        edit("SENSITIVE")
        check_notice("/elivibe", "blocks recognizable sensitive material")
        native_report(original("SENSITIVE"))
    configure(sink.server_port)

    link(updated, next_version)
    with Rpc(peers) as rpc:
        discovery()
        check_notice("/elivibe status", "eliVibe: manual", "not approved")
        check_skill("/skill:elivibe Explain the fixture after the update.", next_skill)
    link(installed, version)
    with Rpc(peers) as rpc:
        discovery()
        check_notice("/elivibe status", "eliVibe: manual", "not approved")
        check_skill("/skill:elivibe Explain the fixture after rollback.", skill)

    native("plugin", "uninstall", "elivibe")
    assert registration() == {"smoke-unrelated": unrelated_registration}
    for folder, packaged_skill in ((installed, skill), (updated, next_skill)):
        assert (
            packaged_skill.is_file() and (folder / "adapters/omp/index.ts").is_file()
        ), "uninstall removed a link target"
    with Rpc(peers) as rpc:
        commands = rpc.commands()
        assert (
            not {"elivibe", "skill:elivibe"} & commands.keys()
            and "smoke-unrelated" in commands
        ), commands.keys()
        if "ponytail" in commands:
            check("/ponytail full")
        _, calls = check("Answer this after removing the package.", 1)
        check_peers(calls[0])

    standalone = Path.home() / ".agents/skills/elivibe/SKILL.md"
    standalone.parent.mkdir(parents=True)
    with ZipFile("/inputs/standalone.zip") as archive:
        standalone.write_bytes(archive.read("elivibe/SKILL.md"))
    assert standalone.read_bytes() == skill.read_bytes(), (
        "portable and bundled skill bytes differ"
    )
    with Rpc(peers) as rpc:
        commands = rpc.commands()
        assert (
            "elivibe" not in commands and commands["skill:elivibe"]["source"] == "skill"
        )
        check_skill(
            "/skill:elivibe Explain the fixture without the adapter.", standalone
        )
    standalone.unlink()
    with Rpc(peers) as rpc:
        assert not {"elivibe", "skill:elivibe"} & rpc.commands().keys()
    assert registration() == {"smoke-unrelated": unrelated_registration}
    assert len(sink.requests) == expected_requests, "unaccounted loopback requests"
    assert not sink.unexpected, sink.unexpected
    assert not AUTH_PROBE.exists(), "a denied route resolved credentials"
    hint_count = len(sink.skill_hint_requests)
    assert 1 <= hint_count <= 4, ("unexpected native skill hint requests", hint_count)
    expected_files = {
        f"{tag}.txt": f"SMOKE_DATA_{tag}\n"
        for tag in (
            "MANUAL",
            "NATIVE",
            "DENIED",
            "ALTERNATE",
            "REDIRECT",
            "FULL",
            "AGAIN",
            "UNJUDGED",
            "INVALID",
            "BUDGET",
            "LIGHT",
            "AUTO",
            "CANCEL",
            "OFF",
            "PROXY",
            "RETAINED",
            "HIDDEN",
            "SENSITIVE",
        )
    }
    expected_files["untouched.txt"] = "Consumer-owned file.\n"
    assert {
        path.relative_to(WORK).as_posix(): path.read_text() for path in WORK.rglob("*")
    } == expected_files
    isolated_calls = sum(call.get("stream") is False for call in sink.requests)
    print(
        f"OMP {OMP_VERSION} smoke passed: native link {version}, update {next_version}, rollback to {version}, "
        "uninstall, standalone skill install/removal, and preserved unrelated registration/consumer files."
    )
    print(
        f"Retained-proxy refusal: 0 credential probes, {retained[0]} socket(s), {retained[1]} report request(s); "
        "isolated requests served by role and marker: "
        f"{dict(Counter(f'{role}:{marker}' for role, marker in sink.served))}."
    )
    print(
        f"{len(original('MANUAL'))}-character handoff; {expected_requests - isolated_calls} ordinary requests, "
        f"{isolated_calls} tool-free requests, and {hint_count} native skill metadata request(s)."
    )
    if peers:
        print(
            "Optional interoperability: "
            + ", ".join(Path(path).parts[2] for path in peers)
        )


def isolated():
    os.environ.pop(
        "LD_LIBRARY_PATH", None
    )  # Only the sandbox's Python startup needs its private runtime.
    assert os.readlink("/proc/self/ns/net") != os.environ["SMOKE_HOST_NETNS"], (
        "network not isolated"
    )
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
    version_output = native("--version")
    assert re.search(
        rf"(?<![\d.]){re.escape(OMP_VERSION)}(?![\w.-])", version_output
    ), version_output
    WORK.rmdir()
    with ThreadingHTTPServer(("127.0.0.1", 0), Sink) as sink:
        sink.connections = []
        sink.served = []
        sink.requests = []
        sink.skill_hint_requests = []
        sink.unexpected = []
        sink.followups = []
        sink.cancel_started = threading.Event()
        sink.cancel_release = threading.Event()
        sink.cancel_replied = threading.Event()
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
            )
        finally:
            sink.shutdown()


if __name__ == "__main__":
    if sys.argv[1:] == ["--isolated"]:
        isolated()
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--omp", default=shutil.which("omp") or "omp")
        parser.add_argument(
            "--archive", type=Path, required=True, help="verified candidate archive"
        )
        parser.add_argument(
            "--update-archive",
            type=Path,
            required=True,
            help="second version for native relinking",
        )
        parser.add_argument(
            "--skill-archive",
            type=Path,
            required=True,
            help="verified standalone skill ZIP",
        )
        parser.add_argument("--ponytail", type=Path)
        parser.add_argument("--context-mode", type=Path)
        isolate(parser.parse_args())
