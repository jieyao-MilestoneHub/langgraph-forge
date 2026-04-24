# Security Policy

## Supported versions

During the `0.x` series, only the **current minor release** receives security
fixes. Older minor versions are end-of-life the moment a new minor ships.

| Version | Supported |
|---|---|
| 0.1.x | yes (current) |
| < 0.1 | no |

Once `1.0.0` ships, the policy moves to current minor + previous minor.

## Reporting a vulnerability

**Do not open a public GitHub issue for security bugs.**

Report privately through GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
feature on the `CoreNovus/langgraph-forge` repository, under the
**Security** tab.

Include:

- A description of the issue and its impact.
- Steps to reproduce (or a proof-of-concept script).
- The affected version(s).
- Any suggested remediation (optional).

## Response targets

- **Acknowledgement**: within 3 business days.
- **Initial assessment**: within 7 business days.
- **Fix or mitigation timeline**: communicated within 14 business days of
  confirming the vulnerability.

We operate a **90-day coordinated disclosure window** by default: the fix
ships, a CVE is requested where applicable, and the reporter is credited in
the release notes unless they request otherwise. The window can be shortened
if the issue is already being exploited or extended by mutual agreement.

## Scope

In scope:

- The `langgraph-forge` Python package and its CLI.
- The scaffolded project templates (including credentials-handling examples).
- The release pipeline (`.github/workflows/publish.yml`).

Out of scope:

- Vulnerabilities in upstream dependencies (langgraph, langchain, typer,
  pydantic, boto3, ...) -- report those upstream directly; we'll bump pins
  as fixes land.
- Cloud provider SDKs / runtimes (AWS Bedrock, GCP Vertex, Azure AI) --
  report to the vendor.
- Social engineering of maintainers or users.

## Thanks

Every confirmed report earns a credit line in the corresponding release
notes (opt-in; anonymous reports are equally welcome).
