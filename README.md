# AWS IAM Access Review and Contractor Offboarding

> A cloud security project that detects excessive AWS access,
> removes an abandoned contractor credential, applies least privilege, and proves
> every important change with an audit trail.

## Executive summary

FinSecure Labs discovered three realistic access-governance problems:

1. `dev-alex` could access every S3 bucket instead of only the application bucket.
2. A former contractor still had an active long-term access key.
3. A security audit role trusted an entire AWS account instead of one approved auditor.

I built a small Python scanner to find those risks, remediated them in AWS IAM,
validated the replacement policy, and used AWS CloudTrail to show who changed what
and when.

| Outcome | Before | After |
|---|---|---|
| Developer S3 access | Broad `s3:*` on `*` | Required actions on one application bucket |
| Contractor access | Active access key and IAM user | Key deactivated, key deleted, user deleted |
| Audit-role trust | Entire account trusted | One named auditor trusted; MFA required |
| Scanner result | 2 High, 1 Medium | 0 findings |
| Audit evidence | CloudTrail enabled | Creation, remediation, and role-use events captured |

This is a defensive lab project. The scanner uses read-only AWS API calls and does
not alter cloud resources.

Repository quality checks validate Python syntax, unit-tested detection/redaction
logic, JSON files, local documentation links, all 38 screenshot provisions, and
identifier masking on every push or pull request.

## The business problem, in plain language

Cloud access often grows faster than it is reviewed. Someone may receive broad
permissions to finish a task quickly, or leave a company while a programmatic key
remains active. Either situation increases the chance of accidental data exposure
or unauthorized access.

This project demonstrates a repeatable access-review process:

```mermaid
flowchart LR
    A[Record the starting state] --> B[Create realistic IAM risks]
    B --> C[Detect risks with Python]
    C --> D[Apply least privilege and offboard]
    D --> E[Validate policies]
    E --> F[Prove changes with CloudTrail]
```

The important point is not simply that an IAM policy was edited. The project shows
the full control cycle: identify risk, make a justified change, verify the result,
and preserve evidence for an auditor.

## Architecture and services

```mermaid
flowchart TB
    DEV[dev-alex] --> GROUP[Developers group]
    GROUP --> POLICY[Application-bucket policy]
    POLICY --> S3[(Private S3 bucket)]
    AUDITOR[security-auditor] -->|AssumeRole + MFA| ROLE[SecurityAuditRole]
    ROLE --> AUDIT[Read-only security review]
    SCANNER[Python IAM risk scanner] -->|Read-only API calls| IAM[AWS IAM]
    CT[AWS CloudTrail] -->|Management events| EVIDENCE[Audit evidence]
    IAM --> CT
    S3 --> CT
```

| Component | Purpose |
|---|---|
| AWS IAM | Users, groups, policies, access keys, and role trust |
| Amazon S3 | Private application-data resource used to demonstrate scoped access |
| AWS CloudTrail | Evidence of identity creation, policy changes, offboarding, and role use |
| IAM Access Analyzer | Static validation of risky and remediated policies |
| Python + Boto3 | A readable, read-only scanner for the three risks in this lab |

## Project walkthrough

The full evidence-led procedure is in
[docs/PROJECT-WALKTHROUGH.md](docs/PROJECT-WALKTHROUGH.md). The five stages are:

1. **Record:** enable CloudTrail management-event logging and an external-access
   analyzer before creating the IAM scenario.
2. **Build:** create a private S3 bucket and a deliberately risky IAM scenario.
3. **Detect:** run the beginner Python scanner and record the baseline findings.
4. **Remediate:** scope S3 access, offboard the contractor, and restrict role trust.
5. **Prove:** validate policies, rescan, and collect the corresponding CloudTrail events.

### Selected evidence

![CloudTrail logging enabled](evidence/screenshots/01-cloudtrail-logging-on.png)

*Figure 01 — CloudTrail management-event logging is enabled before identity changes
are tested, so the later evidence has a trustworthy starting point.*

![Risky developer policy](evidence/screenshots/05-risky-s3-policy.png)

*Figure 05 — The baseline developer policy grants broad S3 access. This is the
misconfiguration the project is designed to detect and correct.*

![Before scan](evidence/screenshots/10-before-scan-report.png)

*Figure 10 — The first scan records two High findings and one Medium finding,
providing a measurable baseline.*

![Least-privilege policy](evidence/screenshots/18-remediated-s3-policy.png)

*Figure 18 — The replacement policy limits developers to the required actions on
the FinSecure application bucket.*

![Restricted role trust](evidence/screenshots/22-restricted-role-trust.png)

*Figure 22 — The audit role now trusts only the named auditor and requires MFA.*

![After scan](evidence/screenshots/27-after-scan-report.png)

*Figure 27 — The final scan contains no findings for the three risks this
beginner scanner evaluates.*

![CloudTrail trust-policy update](evidence/screenshots/32-cloudtrail-update-assume-role-policy.png)

*Figure 32 — CloudTrail records the role trust-policy change, creating evidence
that the access boundary was deliberately narrowed.*

All 38 numbered screenshot locations and captions are listed in
[docs/SCREENSHOT-CATALOG.md](docs/SCREENSHOT-CATALOG.md). Placeholder images are
included so the repository remains readable before private lab screenshots are
added. Replace a placeholder with the redacted screenshot using the same filename.

## Beginner Python scanner

The scanner intentionally checks only the three risks in this project:

- active access keys belonging to IAM users;
- attached customer-managed policies with wildcard actions or resources;
- roles that trust everyone or an entire AWS account.

That small scope makes the logic explainable in an interview. It is a learning and
portfolio tool, not a replacement for AWS-native security services or an
enterprise IAM-governance platform.

### Run it

Prerequisites:

- Python 3.10 or later;
- AWS CLI v2;
- an authenticated AWS CLI profile with the read-only actions in
  [`policies/identity/iam-risk-scanner-read-only.json`](policies/identity/iam-risk-scanner-read-only.json).

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
aws login --profile finsecure-lab
python iam_risk_scanner.py --profile finsecure-lab --output reports/before-scan.json
```

If the computer cannot open the browser directly:

```bash
aws login --remote --profile finsecure-lab
```

The live outputs `reports/before-scan.json` and `reports/after-scan.json` are
ignored by Git. Publish only reviewed, redacted examples.

The scanner policy uses `Resource: "*"` because its list operations must inspect
the account’s IAM inventory. It grants only the six named read actions; it does
not use `Action: "*"` and cannot change IAM resources.

## Policy validation

The two S3 policies in this repository can be validated with IAM Access Analyzer:

```bash
aws accessanalyzer validate-policy \
  --policy-type IDENTITY_POLICY \
  --policy-document file://policies/risky/developer-broad-s3.json

aws accessanalyzer validate-policy \
  --policy-type IDENTITY_POLICY \
  --policy-document file://policies/remediated/developer-app-bucket-only.json
```

The replacement policy uses `${APP_BUCKET_NAME}` so the repository does not expose
a real bucket name. Substitute the lab bucket name before deployment or validation.
The trust-policy template similarly uses `${ACCOUNT_ID}` because a masked account
number is documentation, not valid executable JSON.

## Evidence and auditability

[docs/CLOUDTRAIL-EVIDENCE.md](docs/CLOUDTRAIL-EVIDENCE.md) maps each important
event to the security question it answers:

- Who created the identity or credential?
- Who attached or removed a permission?
- Who changed the role’s trust boundary?
- Was the contractor credential disabled and deleted?
- Could the approved auditor still assume the restricted role?

CloudTrail Event history is Region-specific and retains 90 days of management
events. IAM is a global service, so check **US East (N. Virginia), `us-east-1`**
first for IAM global-service events; check the STS endpoint Region used by the CLI
for `AssumeRole`. A multi-Region trail provides more dependable ongoing evidence.

## Security and redaction

Published evidence follows one consistent rule:

- account ID: `0266XXXXXXXX`;
- ARN: `arn:aws:iam::0266XXXXXXXX:policy/FinSecure-DeveloperAppBucketOnly`;
- access-key ID: `AKIAXXXXXXXXXXXXXXXX`;
- policy ID: `ANPAXXXXXXXXXXXXXXXXX`;
- user ID: `AIDAXXXXXXXXXXXXXXXXX`;
- role ID: `AROAXXXXXXXXXXXXXXXXX`.

Secrets are **never partially masked**. Secret access keys, session tokens,
passwords, MFA seeds/QR codes, browser sign-in codes, cookies, and authorization
headers must be removed completely. See
[docs/SECURITY-AND-REDACTION.md](docs/SECURITY-AND-REDACTION.md) before publishing.

The helper below creates a redacted copy; it does not replace manual review:

```bash
python tools/mask_identifiers.py raw-event.json redacted-event.json
```

## Repository map

```text
.
├── iam_risk_scanner.py
├── policies/
│   ├── risky/
│   ├── remediated/
│   └── identity/
├── trust-policies/
│   ├── before/
│   └── after/
├── reports/
├── evidence/screenshots/
├── docs/
├── tools/
└── tests/
```

## What I would improve in production

- use IAM Identity Center or workforce federation instead of routine IAM users;
- use short-lived credentials and organization-wide guardrails;
- centralize multi-account CloudTrail logs in a protected log-archive account;
- add automated key-age, MFA, administrator-access, `iam:PassRole`, and external
  S3-policy checks;
- schedule the scanner and send findings to a ticketing or alerting system;
- test authorized access and expected denials with automated integration tests.

## Interview summary

I can explain this project in one sentence:

> I performed an evidence-led AWS access review: a small Python tool found broad
> permissions, an abandoned long-term credential, and an unsafe role trust policy;
> I remediated each issue, validated the policies, rescanned, and used CloudTrail
> to prove the control worked.

Further prompts and honest talking points are in
[docs/INTERVIEW-TALKING-POINTS.md](docs/INTERVIEW-TALKING-POINTS.md).

## Cost awareness and cleanup

Use a dedicated lab account, retain the budget alert, and review AWS pricing before
leaving resources running. Delete temporary users, access keys, policies, roles,
buckets, analyzers, and trails when the lab is complete and the required evidence
has been exported. Keep the audit evidence only in an approved, access-controlled
location.
