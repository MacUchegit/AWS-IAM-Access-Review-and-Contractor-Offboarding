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
| Developer user | `dev-alex` | Example developer identity |
| Contractor user | `contractor-james` | Offboarding scenario |
| Auditor user | `security-auditor` | Approved role user |
| Broad S3 policy | `FinSecure-DeveloperBroadS3` | Deliberately risky baseline |
| Restricted S3 policy | `FinSecure-DeveloperAppBucketOnly` | Least-privilege replacement |
| Audit role | `SecurityAuditRole` | Temporary security-review permissions |

The policies were created and managed directly in AWS. In published screenshots
and reports, identifiers are partly masked—for example, `0266XXXXXXXX`. Masked
values are used only in the portfolio; the live AWS resources contain their real
identifiers.

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

## Phase 2 — Build a realistic risky starting point

### Task 2: Create a private application bucket

**Action**

1. Create an S3 bucket using a globally unique name.
2. Keep **Block all public access** enabled.
3. Enable default encryption.
4. Upload a harmless sample file, such as `text.txt`.

**Reason**

The bucket gives the developer policy a real resource to protect. The scenario is
about excessive identity permissions, not public S3 access, so the bucket remains
private.

<img width="1556" height="387" alt="Screenshot_1" src="https://github.com/user-attachments/assets/3244c773-c41f-4309-9ee5-ef10c084cdd3" />

*Figure 02 — The application bucket is private and encrypted. Partly mask the
unique bucket suffix if it could identify the account.*

### Task 3: Create the identities and Developers group

**Action**

1. Create the `Developers` IAM group.
2. Create `dev-alex`, `security-auditor`, and `contractor-james`.
3. Add `dev-alex` to `Developers`.
4. Do not create console passwords for identities that do not need console access.

**Reason**

The group keeps developer permissions separate and makes later policy changes
easy to review. The contractor and auditor remain outside the group because they
have different business purposes.

<img width="1453" height="453" alt="user-complete" src="https://github.com/user-attachments/assets/6e93c4a1-f8ac-4a72-983d-00296a6a4c98" />


*Figure 03 — The project identities and the lab-administration identity are
visible, and `dev-alex` belongs to the Developers group.*

### Task 4: Attach an intentionally broad S3 policy

**Action**

1. Open **IAM → Policies → Create policy**.
2. Create `FinSecure-DeveloperBroadS3` with `s3:*` against `Resource: *`.
3. Attach the customer-managed policy to the `Developers` group.

**Reason**

The policy grants all S3 actions against all resources. That is a realistic
least-privilege failure: the application developer needs one bucket, not every
bucket in the account.

<img width="1184" height="724" alt="dev-initial-policy" src="https://github.com/user-attachments/assets/9113ff96-767f-440c-8930-0bfe57afc9a9" />

*Figure 04 — The risky policy contains `s3:*` and `Resource: *`. This lab-only
misconfiguration establishes the baseline.*

### Task 5: Create an overly broad audit-role trust policy

**Action**

1. Open **IAM → Roles → Create role**.
2. Create `SecurityAuditRole` with the account root principal as the initial
   trusted principal.
3. Attach only the read-only permissions needed for the audit demonstration.

**Reason**

The initial trust policy allows any suitably authorized principal in the account
to attempt role assumption. The remediation will narrow that trust to one named
auditor and require MFA.

<img width="1412" height="631" alt="security-audit-role2" src="https://github.com/user-attachments/assets/e57c0fc5-7c20-434a-a872-48dec845bc1c" />

*Figure 05 — The role trusts the account root principal, representing the entire
account.*

### Task 6: Allow the intended auditor to request the role

**Action**

1. Create an identity policy that permits `sts:AssumeRole` only for
   `SecurityAuditRole`.
2. Attach the policy to `security-auditor`.

**Reason**

Role assumption has two sides: the caller needs permission to call
`sts:AssumeRole`, and the role must trust the caller. This policy handles the
caller-permission side.

<img width="1409" height="418" alt="security-audit-role3" src="https://github.com/user-attachments/assets/1167e250-21e9-4713-9ca8-faed608eaae1" />

*Figure 06 — The auditor may request only the named SecurityAuditRole.*

### Task 7: Give the contractor a temporary lab access key

**Action**

1. Create one access key for `contractor-james`.
2. Record only what is required to test the lab.
3. Never publish the secret access key.

**Reason**

Long-term keys are a common offboarding risk. The scanner should find this active
credential, after which the remediation removes it.

<img width="1381" height="537" alt="contractor-access-keys" src="https://github.com/user-attachments/assets/e23366d2-211b-42be-a0d5-2f2dbd16d3ce" />


*Figure 07 — The contractor has an active access key.*

---

## Phase 3 — Detect and prove the starting risk

### Task 8: Authenticate the local workstation safely

**Action**

1. Install AWS CLI v2.32.0 or later and Python 3.10 or later.
2. Configure or select the `finsecure-lab` AWS CLI profile used for the lab.
3. Keep AWS credentials outside the project repository.
4. Verify the caller:

   ```cmd
   aws sts get-caller-identity --profile finsecure-lab
   ```

**Reason**

Verifying the caller prevents the scanner from running against the wrong AWS
account. Keeping credentials outside the repository prevents accidental
credential exposure.

<img width="970" height="213" alt="python-run1" src="https://github.com/user-attachments/assets/44e232d8-8e64-4c98-a822-fc4e9871d31a" />

*Figure 08 — The scanner runs from an authenticated local profile.*

### Task 9: Run the baseline scan

**Action**

```cmd
pip install -r requirements.txt
python iam_risk_scanner.py --profile finsecure-lab --output reports/before-scan.json
```

<img width="970" height="405" alt="python-run" src="https://github.com/user-attachments/assets/cbe20be4-0887-4e28-a351-b21e71c6f4b9" />

*Figure 09 — The baseline Python scanner completes and writes the
before-remediation report.*

**Expected result**

- High: wildcard S3 permission policy;
- High: broad role trust;
- Medium: active contractor access key.
[Before-remediation Scan report](https://github.com/MacUchegit/AWS-IAM-Access-Review-and-Contractor-Offboarding/blob/main/before-scan.json)

**Reason**

The baseline creates a measurable statement of risk before any remediation. A
before/after comparison is stronger than claiming a policy “looks better.”

<img width="1101" height="738" alt="before1" src="https://github.com/user-attachments/assets/f1ee9a96-1b65-4917-bd85-9c6cc2928c61" />

*Figure 10 — The redacted baseline report contains two High and one Medium
finding.*


### Task 10: Capture creation events in CloudTrail

Capture `CreateUser`, `CreateAccessKey`, `CreatePolicy`, `AttachGroupPolicy`,
and `CreateRole`. The detailed procedure and screenshot captions are in
[CLOUDTRAIL-EVIDENCE.md](https://github.com/MacUchegit/AWS-IAM-Access-Review-and-Contractor-Offboarding/blob/main/CLOUDTRAIL-EVIDENCE.md).

**Reason**

These events prove how the risky baseline was created and make the project
reproducible and auditable. The approved role-use event is captured after the
role workflow is tested later in the project.

---

## Phase 4 — Remediate the access risks

### Task 11: Replace broad S3 access with least privilege

**Action**

1. Create `FinSecure-DeveloperAppBucketOnly` directly in IAM, limiting the
   permitted S3 actions to the private application bucket and its objects.
2. Attach it to `Developers`.
3. Test the allowed application-bucket actions.
4. Detach `FinSecure-DeveloperBroadS3`.
5. Delete the broad policy after verifying it is no longer attached.

**Reason**

The replacement separates bucket-level listing from object-level operations and
uses specific ARNs. Attaching and testing the new policy before deleting the old
one reduces the chance of an avoidable outage.

<img width="1151" height="738" alt="dev-remediated-policy" src="https://github.com/user-attachments/assets/b1ebb687-7d44-4e6b-946c-739cc627e845" />

*Figure 11 — Required S3 actions are limited to the application bucket and its
objects.*

<img width="1021" height="560" alt="dev-remediated-group" src="https://github.com/user-attachments/assets/9f48beef-94b8-470a-b442-07f7531c9b1b" />


*Figure 12 — The Developers group has the replacement policy and no longer has the
broad policy.*

### Task 12: Offboard the contractor

**Action**

1. Confirm `contractor-james` is the intended lab identity.
2. Change the access key status to **Inactive**.
3. Confirm there is no dependency on the key.
4. Delete the access key.
5. Remove any attached or inline permissions.
6. Delete the IAM user.

**Reason**

Deactivation provides a safe verification point; deletion then removes the
long-term credential permanently. Removing the user closes the abandoned identity
path.

<img width="986" height="269" alt="contractor-access-keys-inactive" src="https://github.com/user-attachments/assets/615c2bf4-51a7-4ada-b705-66a78337dbd1" />


*Figure 13 — The contractor key is inactive before deletion.*

<img width="982" height="520" alt="contractor-offboarded" src="https://github.com/user-attachments/assets/6897980b-02d2-48f6-95b4-8eb097fef616" />

*Figure 14 — The contractor access-key list confirms that the long-term
credential has been removed.*

<img width="1447" height="345" alt="user-contractor-deleted" src="https://github.com/user-attachments/assets/a8ac7328-815f-497c-9b16-e166776a79bb" />


*Figure 15 — The contractor user no longer appears in the IAM user list.*

### Task 13: Restrict the audit role and require MFA

**Action**

1. Open the `SecurityAuditRole` trust relationship in IAM.
2. Replace the account-wide principal with the exact `security-auditor` ARN.
3. Verify that the principal is only `security-auditor`.
4. Verify that `aws:MultiFactorAuthPresent` must be `true`.

**Reason**

The named principal removes account-wide trust. MFA adds a second proof of identity
before a human can enter the security-audit role.

<img width="1074" height="744" alt="denied-role-access" src="https://github.com/user-attachments/assets/4ca303f1-e777-4b5b-b7b5-a9c05488a6ff" />

*Figure 16 — Role trust is restricted to the named auditor and MFA.*

### Task 14: Retest the approved role workflow

**Action**

1. Confirm role assumption without MFA is denied.
2. Confirm the intended auditor can assume the role with MFA.
3. Run `aws sts get-caller-identity` inside the role session.

**Reason**

The expected denial proves the new condition is enforced; the expected success
proves the legitimate workflow still works.

<img width="875" height="426" alt="security-audit-role-remediated" src="https://github.com/user-attachments/assets/bdd016a1-310f-415f-9c73-9ac777cf322e" />

*Figure 17 — The approved auditor successfully uses the restricted role with MFA.*

---

## Phase 5 — Rescan and preserve evidence

The Python IAM risk scanner is the project’s automated validation control. It
first established the risky baseline, then verified that the same risks were no
longer present after remediation.

### Task 15: Run the final scan

**Action**

```cmd
python iam_risk_scanner.py --profile finsecure-lab --output reports/after-scan.json
```

Review and redact the actual
[`after-scan.json`](https://github.com/MacUchegit/AWS-IAM-Access-Review-and-Contractor-Offboarding/blob/main/after-scan.json) result before publishing.

**Expected result**

The three scoped risks produce zero findings.

**Reason**

The second scan is a control check: it verifies that the risky policy, broad trust,
and active contractor key are no longer present.

<img width="996" height="155" alt="python-run-after" src="https://github.com/user-attachments/assets/6aed3d72-8a11-4279-b5ce-dc1afd8f99e2" />

*Figure 18 — The final scanner run completes successfully.*

<img width="819" height="331" alt="after1" src="https://github.com/user-attachments/assets/2af4966d-fbb2-45a4-a7af-c177b2b24032" />

*Figure 19 — The final redacted report contains zero findings for the scanner’s
defined scope.*

### Task 16: Capture remediation events

Capture `CreatePolicy`, `AttachGroupPolicy`, `DetachGroupPolicy`, `DeletePolicy`,
`UpdateAssumeRolePolicy`, `UpdateAccessKey`, `DeleteAccessKey`, `DeleteUser`, and
the successful post-remediation `AssumeRole`. The detailed procedure and
screenshot captions are in
[CLOUDTRAIL-EVIDENCE.md](https://github.com/MacUchegit/AWS-IAM-Access-Review-and-Contractor-Offboarding/blob/main/CLOUDTRAIL-EVIDENCE.md).

**Reason**

The event sequence proves that the safer policy was introduced, the risky policy
was retired, the contractor was removed, and the role remained usable through the
approved path.


## Definition of done

The project is complete when:

- the three baseline risks can be explained in business terms;
- the before report is preserved;
- each remediation has a least-privilege reason;
- allowed and denied behavior has been tested;
- the final scanner returns no in-scope findings;
- CloudTrail records the key actions.

## Cleanup

After exporting approved evidence, delete lab-only identities and keys first, then
policies and roles, followed by empty S3 buckets and other temporary resources.
Review the bill and confirm no unexpected resource remains. Keep a trail or log
archive only if its ongoing storage and protection are intentional.
