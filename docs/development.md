# Developing eliVibe

Consumers use [installation](installation.md); they don't need this toolchain. Work from the public product checkout with full Git history. The [status ledger](status.md) names the reviewed baseline and the current evidence, not just the checks we intend to run.

## Product checks

The pinned Linux development job uses CPython 3.14.4, Node 24.21.0, npm 11.19.0, uv 0.12.5 and actionlint 1.7.12. From the repository root on Linux x64:

```sh
sh dev/check --setup
```

This sets up locked Python and Node **development** dependencies and checksum-verified actionlint. After setup, use `sh dev/check`. The command checks the product manifest/lock, workflow syntax, local Markdown links/anchors and shell example syntax, commit subjects, Ruff format/lint, product and adapter tests, strict no-emit TypeScript against OMP 19.2.1, and disposable semantic-version rule fixtures. Markdown syntax is not a network or consumer-install check. A fake host can establish parser and lifecycle behavior, not actual routing or teaching quality. Do not unset your proxies or change your personal OMP profile to make a mock pass.

## Native OMP smoke

Use the [official OMP 19.2.1 Linux x64 binary](https://github.com/can1357/oh-my-pi/releases/download/v19.2.1/omp-linux-x64), SHA-256 `e8b937f9bf023baa147bdd300ad5421af0a6ef8b1f350c47a9a93d5fca94feca`, Python 3.14, and working unprivileged bubblewrap namespaces. [CI](../.github/workflows/ci.yml) supplies the exact checkout's packages. To exercise the candidate built in the [release instructions](release.md#version-and-contents), run from the checkout, using the same shell variables:

```sh
python3.14 dev/omp_smoke.py --omp "$(command -v omp)" \
  --archive "$assets/elivibe-omp-$version.tar.gz" --skill-archive "$assets/elivibe-$version.zip" \
  --npm-archive "$registry/elivibe-$version.tgz"
```

Keep developer scripts in `dev/`, not root `tools/`: OMP discovers scripts in an installed plugin's `tools/` as custom tools, including when installed from a Git checkout.

The native sandbox checks its own non-root identity, dropped capabilities, distinct loopback-only network namespace and lack of an external route. Hosted mode additionally requires the expected enforced AppArmor stack. The [runner preflight](../.github/native-namespace.sh) is for disposable hosted Ubuntu runners only. Do not run it on a workstation or relax global policy to make a smoke pass. Synthetic loopback responses make request payloads inspectable without exposing a developer's normal profile or credentials. They do not establish provider support, reader outcomes or live quality.

## Teaching and first-use review

Use a meaningful [synthetic handoff](qa-examples.md). In a working, authorized OMP conversation, enter `/elivibe`, ask one focused question and try `/elivibe more`. Compare with the untouched report: can a reader explain why the system behaves that way or make a better-informed decision? A passing payload assertion, a scripted answer and an actual model-generated response answer different questions. Label each precisely; do not attribute implementer observations to independent readers. Record sanitized excerpts and meaningful failures only. Do not copy private sessions, ask for extra provider access or start an external evaluation service.

## Dependency and repository policy

Use reviewed updates with exact dev pins, lockfile integrity, `npm ci --ignore-scripts`, pinned CI actions and no saved checkout credentials. No development dependencies belong in a runtime archive. Keep PR checks read-only and separate from privileged release operations. Review and squash on protected `main`; use a Conventional Commit PR title. Sole-maintainer review is not independent approval. See the [release gates](release.md) before any external write.
