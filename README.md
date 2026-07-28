# AWS IAM Access Review and Contractor Offboarding

This guide explains both **what was done** and **why it matters**. It is written for
a recruiter, a technical reviewer, or someone encountering AWS identity security
for the first time.

## Scenario and scope

FinSecure Labs is a fictional financial-technology company with a private S3
application bucket. A routine access review found three common problems:

- the Developers group had broad S3 access;
- a former contractor had an active programmatic access key;
- a security-audit role trusted the entire AWS account.

The objective was to correct those risks without breaking the approved developer
or auditor workflows, then retain evidence that the work occurred.

> Lab safety: use a dedicated AWS lab account. Do not deliberately weaken a
> production account. Replace the fictional names if they conflict with existing
> resources.

## Architecture and services

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/72da9383-ebe5-43f3-b596-140ea9954260" />


## Naming used in the lab

| Resource | Lab name | Purpose |
|---|---|---|
| S3 bucket | `finsecure-app-data-<unique-suffix>` | Private application data |
| IAM group | `Developers` | Developer permission assignment |
| Developer users | `dev-alex`, `dev-sam` | Example human identities |
| Contractor user | `contractor-jane` | Offboarding scenario |
| Auditor user | `security-auditor` | Approved role user |
| Broad S3 policy | `FinSecure-DeveloperBroadS3` | Deliberately risky baseline |
| Restricted S3 policy | `FinSecure-DeveloperAppBucketOnly` | Least-privilege replacement |
| Audit role | `SecurityAuditRole` | Temporary security-review permissions |

Executable templates use `${ACCOUNT_ID}` and `${APP_BUCKET_NAME}`. In published
screenshots and reports, identifiers are partly masked—for example,
`0266XXXXXXXX`. A masked ID must never be pasted into a live policy.

---

## Phase 1 — Establish the evidence baseline

### Task 1: Enable CloudTrail management-event logging

**Action**

1. Open **CloudTrail → Trails → Create trail**.
2. Use a clear name such as `finsecure-management-events`.
3. Create or select a private S3 log bucket.
4. Make the trail multi-Region.
5. Include management events with both **Read** and **Write** activity.
6. Confirm **Logging** is on.

**Reason**

CloudTrail records API activity. Enabling it before the risky scenario is created
means identity creation, permission changes, credential removal, and role use can
all be traced later.

<img width="1454" height="490" alt="cloudtrail" src="https://github.com/user-attachments/assets/54b454b8-a000-42bd-99f7-e37fcdec3b05" />

*Figure 01 — The multi-Region trail is logging management events.*

### Task 2: Enable an external-access analyzer

**Action**

1. Open **IAM → Access Analyzer → Analyzers**.
2. Create an **External access analyzer** for the current account.
3. Wait for its status to become **Active**.

**Reason**

An external-access analyzer identifies supported resources that can be accessed
from outside the account. It complements this project’s custom IAM checks.

![Access Analyzer active](../evidence/screenshots/02-access-analyzer-active.png)

*Figure 02 — The account-level external-access analyzer is active.*

---

## Phase 2 — Build a realistic risky starting point

### Task 3: Create a private application bucket

**Action**

1. Create an S3 bucket using a globally unique name.
2. Keep **Block all public access** enabled.
3. Enable default encryption.
4. Upload a harmless sample file, such as `sample-transaction.csv`.

**Reason**

The bucket gives the developer policy a real resource to protect. The scenario is
about excessive identity permissions, not public S3 access, so the bucket remains
private.

<img width="1556" height="387" alt="Screenshot_1" src="https://github.com/user-attachments/assets/3244c773-c41f-4309-9ee5-ef10c084cdd3" />

*Figure 03 — The application bucket is private and encrypted. Partly mask the
unique bucket suffix if it could identify the account.*

### Task 4: Create the people and Developers group

**Action**

1. Create the `Developers` IAM group.
2. Create `dev-alex`, `dev-sam`, `security-auditor`, and `contractor-jane`.
3. Add the two developer users to `Developers`.
4. Do not create console passwords for identities that do not need console access.

**Reason**

Groups make permission assignment easier to review than attaching the same policy
to several users. The contractor and auditor are kept separate because they have
different business purposes.

![IAM users and group](../evidence/screenshots/04-iam-users-and-group.png)

*Figure 04 — The example users exist and the developer users belong to the
Developers group. Partly mask generated user IDs.*

### Task 5: Attach an intentionally broad S3 policy

**Action**

1. Review
   [`policies/risky/developer-broad-s3.json`](../policies/risky/developer-broad-s3.json).
2. Create `FinSecure-DeveloperBroadS3`.
3. Attach it to the `Developers` group.

**Reason**

The policy grants all S3 actions against all resources. That is a realistic
least-privilege failure: application developers need one bucket, not every bucket
in the account.

![Risky S3 policy](../evidence/screenshots/05-risky-s3-policy.png)

*Figure 05 — The risky policy contains `s3:*` and `Resource: *`. This lab-only
misconfiguration establishes the baseline.*

### Task 6: Create an overly broad audit-role trust policy

**Action**

1. Substitute the real account number for `${ACCOUNT_ID}` in
   [`trust-policies/before/security-audit-role.json`](../trust-policies/before/security-audit-role.json).
2. Create `SecurityAuditRole` with that trust policy.
3. Attach only the read-only permissions needed for the audit demonstration.

**Reason**

The initial trust policy allows any suitably authorized principal in the account
to attempt role assumption. The remediation will narrow that trust to one named
auditor and require MFA.

![Broad audit-role trust](../evidence/screenshots/06-broad-role-trust.png)

*Figure 06 — The role trusts the account root principal, representing the entire
account. The 10-digit account number is partly masked.*

### Task 7: Allow the intended auditor to request the role

**Action**

1. Substitute the real account number for `${ACCOUNT_ID}` in
   [`policies/identity/allow-security-audit-role.json`](../policies/identity/allow-security-audit-role.json).
2. Attach the policy to `security-auditor`.

**Reason**

Role assumption has two sides: the caller needs permission to call
`sts:AssumeRole`, and the role must trust the caller. This policy handles the
caller-permission side.

![Auditor AssumeRole permission](../evidence/screenshots/07-auditor-assumerole-policy.png)

*Figure 07 — The auditor may request only the named SecurityAuditRole.*

### Task 8: Give the contractor a temporary lab access key

**Action**

1. Create one access key for `contractor-jane`.
2. Record only what is required to test the lab.
3. Never publish the secret access key.

**Reason**

Long-term keys are a common offboarding risk. The scanner should find this active
credential, after which the remediation removes it.

![Contractor active access key](../evidence/screenshots/08-contractor-active-key.png)

*Figure 08 — The contractor has an active access key. Publish only a partly masked
key ID such as `AKIAXXXXXXXXXXXXXXXX`; remove the secret completely.*

---

## Phase 3 — Detect and prove the starting risk

### Task 9: Authenticate the local workstation safely

**Action**

1. Install AWS CLI v2.32.0 or later and Python 3.10 or later.
2. Give the scan identity the actions in
   [`policies/identity/iam-risk-scanner-read-only.json`](../policies/identity/iam-risk-scanner-read-only.json).
3. Create or select the `finsecure-lab` AWS CLI profile.
4. Use `aws login --profile finsecure-lab`, or `aws login --remote` when the browser
   is on another device.
5. Verify the caller:

   ```bash
   aws sts get-caller-identity --profile finsecure-lab
   ```

**Reason**

`aws login` provides temporary credentials for local development. Temporary
credentials are safer than putting a new long-term access key in a local
credentials file.

![Before-scan command](../evidence/screenshots/09-before-scan-cli.png)

*Figure 09 — The scanner runs from an authenticated local profile. Partly mask the
account and principal identifiers in the terminal.*

### Task 10: Run the baseline scan

**Action**

```bash
pip install -r requirements.txt
python iam_risk_scanner.py \
  --profile finsecure-lab \
  --output reports/before-scan.json
```

Compare the private output with
[`reports/before-scan.example.json`](../reports/before-scan.example.json).

**Expected result**

- High: wildcard S3 permission policy;
- High: broad role trust;
- Medium: active contractor access key.

**Reason**

The baseline creates a measurable statement of risk before any remediation. A
before/after comparison is stronger than claiming a policy “looks better.”

![Before-scan report](../evidence/screenshots/10-before-scan-report.png)

*Figure 10 — The redacted baseline report contains two High and one Medium
finding.*

### Task 11: Prove the intended auditor can use the role

**Action**

From the auditor context, call `sts:AssumeRole` for `SecurityAuditRole` with a
valid MFA code where required. Use the returned temporary credentials only for the
approved audit test, then let them expire.

**Reason**

Testing the permitted path avoids a false sense of security. A control is useful
only if it blocks unintended access while preserving legitimate work.

![Audit role session](../evidence/screenshots/11-audit-role-session.png)

*Figure 11 — `get-caller-identity` shows an assumed-role session. Remove temporary
credentials and session tokens completely.*

### Task 12: Capture creation events in CloudTrail

Capture `CreateUser`, `CreateAccessKey`, `CreatePolicy`, `AttachGroupPolicy`,
`CreateRole`, and `AssumeRole`. The detailed procedure and captions are in
[CLOUDTRAIL-EVIDENCE.md](CLOUDTRAIL-EVIDENCE.md), Figures 12–17.

**Reason**

These events prove how the risky baseline was created and that the role was
actually used; they make the project reproducible and auditable.

---

## Phase 4 — Remediate the access risks

### Task 13: Replace broad S3 access with least privilege

**Action**

1. Substitute the real bucket name for `${APP_BUCKET_NAME}` in
   [`policies/remediated/developer-app-bucket-only.json`](../policies/remediated/developer-app-bucket-only.json).
2. Create `FinSecure-DeveloperAppBucketOnly`.
3. Attach it to `Developers`.
4. Test the allowed application-bucket actions.
5. Detach `FinSecure-DeveloperBroadS3`.
6. Delete the broad policy after verifying it is no longer attached.

**Reason**

The replacement separates bucket-level listing from object-level operations and
uses specific ARNs. Attaching and testing the new policy before deleting the old
one reduces the chance of an avoidable outage.

![Remediated S3 policy](../evidence/screenshots/18-remediated-s3-policy.png)

*Figure 18 — Required S3 actions are limited to the application bucket and its
objects.*

![Developers fixed policy](../evidence/screenshots/19-developers-fixed-policy.png)

*Figure 19 — The Developers group has the replacement policy and no longer has the
broad policy.*

### Task 14: Offboard the contractor

**Action**

1. Confirm `contractor-jane` is the intended lab identity.
2. Change the access key status to **Inactive**.
3. Confirm there is no dependency on the key.
4. Delete the access key.
5. Remove any attached or inline permissions.
6. Delete the IAM user.

**Reason**

Deactivation provides a safe verification point; deletion then removes the
long-term credential permanently. Removing the user closes the abandoned identity
path.

![Contractor key inactive](../evidence/screenshots/20-contractor-key-inactive.png)

*Figure 20 — The contractor key is inactive before deletion.*

![Contractor user removed](../evidence/screenshots/21-contractor-user-removed.png)

*Figure 21 — The contractor user no longer appears in the IAM user list.*

### Task 15: Restrict the audit role and require MFA

**Action**

1. Substitute the real account number for `${ACCOUNT_ID}` in
   [`trust-policies/after/security-audit-role.json`](../trust-policies/after/security-audit-role.json).
2. Update the `SecurityAuditRole` trust relationship.
3. Verify that the principal is only `security-auditor`.
4. Verify that `aws:MultiFactorAuthPresent` must be `true`.

**Reason**

The named principal removes account-wide trust. MFA adds a second proof of identity
before a human can enter the security-audit role.

![Restricted audit-role trust](../evidence/screenshots/22-restricted-role-trust.png)

*Figure 22 — Role trust is restricted to the named auditor and MFA.*

### Task 16: Retest the approved role workflow

**Action**

1. Confirm role assumption without MFA is denied.
2. Confirm the intended auditor can assume the role with MFA.
3. Run `aws sts get-caller-identity` inside the role session.

**Reason**

The expected denial proves the new condition is enforced; the expected success
proves the legitimate workflow still works.

![Audit role after remediation](../evidence/screenshots/23-audit-role-after.png)

*Figure 23 — The approved auditor successfully uses the restricted role with MFA.*

---

## Phase 5 — Validate, rescan, and preserve evidence

### Task 17: Validate the policies before and after

**Action**

Use the IAM console policy editor’s validation or:

```bash
aws accessanalyzer validate-policy \
  --policy-type IDENTITY_POLICY \
  --policy-document file://policies/risky/developer-broad-s3.json

aws accessanalyzer validate-policy \
  --policy-type IDENTITY_POLICY \
  --policy-document file://policies/remediated/developer-app-bucket-only.json
```

Record the real output in the two validation-report templates in `reports/`.

**Reason**

Access Analyzer validation provides an AWS-native review in addition to the
custom scanner. Validation findings are not the same as runtime authorization, so
both policy review and functional testing remain necessary.

![Policy validation before](../evidence/screenshots/24-policy-validation-before.png)

*Figure 24 — Validation findings for the risky baseline are recorded without
altering the AWS response.*

![Policy validation after](../evidence/screenshots/25-policy-validation-after.png)

*Figure 25 — The replacement policy’s validation result is recorded.*

### Task 18: Run the final scan

**Action**

```bash
python iam_risk_scanner.py \
  --profile finsecure-lab \
  --output reports/after-scan.json
```

Review the result before publishing. The example is
[`reports/after-scan.example.json`](../reports/after-scan.example.json).

**Expected result**

The three scoped risks produce zero findings.

**Reason**

The second scan is a control check: it verifies that the risky policy, broad trust,
and active contractor key are no longer present.

![After-scan command](../evidence/screenshots/26-after-scan-cli.png)

*Figure 26 — The final scanner run completes successfully.*

![After-scan report](../evidence/screenshots/27-after-scan-report.png)

*Figure 27 — The final redacted report contains zero findings for the scanner’s
defined scope.*

### Task 19: Capture remediation events

Capture `CreatePolicy`, `AttachGroupPolicy`, `DetachGroupPolicy`, `DeletePolicy`,
`UpdateAssumeRolePolicy`, `UpdateAccessKey`, `DeleteAccessKey`, `DeleteUser`, and
the successful post-remediation `AssumeRole`. See Figures 28–36 in
[CLOUDTRAIL-EVIDENCE.md](CLOUDTRAIL-EVIDENCE.md).

**Reason**

The event sequence proves that the safer policy was introduced, the risky policy
was retired, the contractor was removed, and the role remained usable through the
approved path.

### Task 20: Perform final acceptance checks

**Action**

1. Confirm the external-access analyzer has no unexplained findings.
2. Confirm S3 Block Public Access is still on.
3. Confirm the application bucket works for the approved developer actions.
4. Confirm an unrelated bucket or forbidden action is denied.
5. Confirm the audit role requires MFA.
6. Confirm the contractor user and key no longer exist.
7. Confirm the final scanner report and CloudTrail evidence are saved and redacted.

![Final Access Analyzer review](../evidence/screenshots/37-access-analyzer-final.png)

*Figure 37 — Final external-access findings are reviewed and explained.*

![Final S3 public-access check](../evidence/screenshots/38-s3-block-public-access-final.png)

*Figure 38 — S3 Block Public Access remains enabled after IAM remediation.*

## Definition of done

The project is complete when:

- the three baseline risks can be explained in business terms;
- the before report is preserved;
- each remediation has a least-privilege reason;
- allowed and denied behavior has been tested;
- the final scanner returns no in-scope findings;
- CloudTrail records the key actions;
- all published evidence passes the redaction checklist.

## Cleanup

After exporting approved evidence, delete lab-only identities and keys first, then
policies and roles, followed by empty S3 buckets and other temporary resources.
Review the bill and confirm no unexpected resource remains. Keep a trail or log
archive only if its ongoing storage and protection are intentional.
