# Security policy

## Supported versions

See [published releases](https://github.com/taibenvenuti/elivibe/releases) and the [maintained distribution record](https://github.com/taibenvenuti/elivibe/blob/main/docs/status.md) for current availability. There is no security support commitment. See [compatibility](docs/compatibility.md) for evaluated targets. Product checks are not an independent security audit.

## Reporting privately

Use [GitHub private vulnerability reporting](https://github.com/taibenvenuti/elivibe/security/advisories/new) on `taibenvenuti/elivibe` (sign-in required), or open the repository's **Security → Advisories → Report a vulnerability**. The repository has private reporting enabled. `taibenvenuti` is the sole maintainer.

If that button is unavailable, there is no approved interim inbox. Do not disclose the vulnerability in public issues, pull requests, comments, or an unverified channel.

Include the eliVibe version or commit, host and version, whether you used the OMP adapter or a packaged or standalone skill, exact invocation, OMP mode if applicable, observed impact, and the smallest safe reproduction using synthetic data. For v0.1.0 side requests, note which role and transport were involved if relevant. Redact credentials, endpoint secrets, IPs and identifying content; don't attach actual reports or full transcripts. Don't test against anyone else's accounts, data, or credentials.

If you suspect disclosure, stop sending affected content, notify the account or data owner through their approved incident channel, and follow their process for credentials and provider-side data. In the OMP adapter from v1.0.0 onward, `/elivibe off` stops automatic teaching only; explicit explanation commands can still start ordinary turns. In v0.1.0, `/elivibe off` stops the adapter pipeline; see [tagged v0.1.0 controls](https://github.com/taibenvenuti/elivibe/blob/v0.1.0/docs/privacy.md) for grants. A skill-only install has no eliVibe Off mode; follow the host's policy and stop invoking the skill in affected conversations. Changing a setting or removing a skill never recalls a request already sent. See [privacy and controls](docs/privacy.md).
