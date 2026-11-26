# Security policy

## Supported versions

There are no publicly supported versions. The v0.1.0 candidate is reviewed on the target described in [compatibility](docs/compatibility.md). These checks are not an independent security audit or a support commitment.

## Reporting privately

`taibenvenuti` is the sole maintainer. The only approved reporting route is GitHub private vulnerability reporting on `taibenvenuti/elivibe`. Once the maintainer has enabled and verified it, use **Security → Advisories → Report a vulnerability** on that repository. This policy is not evidence that the feature is active; public release requires verification first.

If that button is unavailable, there is no approved interim inbox. Do not disclose the vulnerability in public issues, pull requests, comments, or an unverified channel.

A useful report gives the affected version or commit, host and mode, observed impact, and the smallest safe reproduction using synthetic data. Include which role and transport were involved if relevant. Redact credentials, endpoint secrets, IPs and identifying content; don't attach full session transcripts or actual report contents. Don't test against anyone else's credentials, account, or data.

If you suspect a report was disclosed, stop isolated requests (`/elivibe off`), notify the relevant account or data owner through their approved incident channel, and follow their process for credentials and provider-side data. Revoking eliVibe grants does not recall an earlier request. See [privacy and controls](docs/privacy.md).
