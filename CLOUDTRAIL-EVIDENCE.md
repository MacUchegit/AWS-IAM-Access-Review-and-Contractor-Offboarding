# AWS CloudTrail Audit Evidence

This evidence register supports the
[AWS IAM Access Review and Contractor Offboarding](PROJECT-WALKTHROUGH.md)
project. It shows that the IAM remediation was not merely described: AWS
CloudTrail independently recorded the policy changes, credential removal,
identity deletion, and approved role use.

The evidence is numbered `CT-01` through `CT-10`. This separate numbering keeps
the evidence references stable if tasks or screenshots in the main walkthrough
change later.

## What CloudTrail contributes

The Python IAM risk scanner identified the original access risks and confirmed
that they were removed after remediation. CloudTrail answers a different
question: **who changed what, when, and against which AWS resource?**

AWS CloudTrail records authenticated IAM and AWS STS API activity from the AWS
Management Console, AWS CLI, SDKs, and APIs. Recent management events can be
reviewed through Event history, while the multi-Region trail preserves an
ongoing copy in Amazon S3.

> **Region note:** The IAM events in this evidence display `us-east-1`. IAM is a
> global AWS service, so this does not mean that the application bucket or the
> rest of the lab was deployed in `us-east-1`.

## Evidence summary

| Evidence | CloudTrail record | What it proves | Status |
|---|---|---|---|
| CT-01 | Trail configuration | Management-event evidence collection was enabled | Captured |
| CT-02 | `CreatePolicy` | The restricted replacement policy was created | Captured |
| CT-03 | `AttachGroupPolicy` | The replacement policy was applied to the developer group | Captured |
| CT-04 | `DetachGroupPolicy` | The broad policy stopped affecting the group | Captured |
| CT-05 | `DeletePolicy` | The obsolete broad policy was removed | Recapture recommended |
| CT-06 | `UpdateAssumeRolePolicy` | The audit-role trust boundary was changed | Recapture recommended |
| CT-07 | `UpdateAccessKey` | The contractor key was disabled first | Captured |
| CT-08 | `DeleteAccessKey` | The contractor key was permanently removed | Captured |
| CT-09 | `DeleteUser` | The former contractor identity was deleted | Captured |
| CT-10 | `AssumeRole` | The intended auditor could still use the secured role | Correct event required |

---

## CT-01 — CloudTrail management-event logging

**What it proves**

The multi-Region trail was configured before the remediation evidence was
collected. Log-file validation was enabled and the logs were protected with
server-side KMS encryption.

**Why it matters**

Security changes are more credible when an independent audit service records
them. A multi-Region trail also reduces the chance that relevant management
events are missed because an action occurred in another Region.

**The screenshot should show**

- trail name;
- multi-Region status;
- logging status;
- log-file validation;
- encryption configuration.

![CloudTrail trail configuration](../evidence/screenshots/ct-01-cloudtrail-configuration.png)

*Figure CT-01 — The multi-Region CloudTrail trail is configured to preserve
management-event evidence with log-file validation and KMS encryption. Account,
bucket, and KMS identifiers are partially masked.*

---

## CT-02 — Create the least-privilege developer policy

**Event**

```text
CreatePolicy
```

**What it proves**

CloudTrail recorded the creation of
`FinSecure-DeveloperAppBucketOnly`, the replacement policy that limits developer
access to the approved application bucket.

**Why it matters**

Creating the replacement policy established the safer permission model before
the broad policy was removed. This order reduced the risk of disrupting the
approved developer workflow.

**The screenshot should show**

- `eventName: CreatePolicy`;
- event time;
- initiating identity;
- `policyName: FinSecure-DeveloperAppBucketOnly`.

![CreatePolicy remediation event](../evidence/screenshots/ct-02-create-policy-remediation.png)

*Figure CT-02 — CloudTrail records creation of the least-privilege
`FinSecure-DeveloperAppBucketOnly` policy and attributes the action to the lab
administrator.*

---

## CT-03 — Attach the replacement policy to the developer group

**Event**

```text
AttachGroupPolicy
```

**What it proves**

The safer policy was attached to the developer group and therefore began
controlling the permissions inherited by `dev-alex`.

**Why it matters**

A policy that merely exists does not change anyone's permissions. This event
proves that the replacement policy was actually applied to the group.

**The screenshot should show**

- `eventName: AttachGroupPolicy`;
- developer group name;
- policy ARN ending in `FinSecure-DeveloperAppBucketOnly`;
- initiating identity and event time.

![AttachGroupPolicy remediation event](../evidence/screenshots/ct-03-attach-replacement-policy.png)

*Figure CT-03 — CloudTrail confirms that the least-privilege policy was attached
to the developer group, changing the permissions inherited by `dev-alex`.*

---

## CT-04 — Detach the broad developer policy

**Event**

```text
DetachGroupPolicy
```

**What it proves**

`FinSecure-DeveloperBroadS3` was detached from the developer group after the
replacement policy was applied.

**Why it matters**

This is the point at which the broad policy stopped granting `s3:*` permissions
to the group. It is direct evidence of least-privilege remediation.

**The screenshot should show**

- `eventName: DetachGroupPolicy`;
- developer group name;
- policy ARN ending in `FinSecure-DeveloperBroadS3`;
- initiating identity and event time.

![DetachGroupPolicy remediation event](../evidence/screenshots/ct-04-detach-broad-policy.png)

*Figure CT-04 — CloudTrail confirms that
`FinSecure-DeveloperBroadS3` was detached from the developer group, ending its
effect on `dev-alex`.*

---

## CT-05 — Delete the obsolete broad policy

**Event**

```text
DeletePolicy
```

**What it proves**

The unused `FinSecure-DeveloperBroadS3` policy was deleted after it was detached.

**Why it matters**

Deleting the obsolete policy reduces the possibility that someone could
accidentally attach it to another user, group, or role later.

**The screenshot should show**

- `eventName: DeletePolicy`;
- policy ARN ending in `FinSecure-DeveloperBroadS3`;
- initiating identity;
- event time.

![DeletePolicy remediation event](../evidence/screenshots/ct-05-delete-broad-policy.png)

*Figure CT-05 — CloudTrail records deletion of the obsolete
`FinSecure-DeveloperBroadS3` policy after it was safely detached.*

> **Evidence-quality note:** The supplied screenshot shows the broad policy
> resource, but the visible crop does not show `eventName: DeletePolicy`.
> Recapture the event with both the event name and policy ARN visible before
> publishing it.

---

## CT-06 — Restrict the audit-role trust policy

**Event**

```text
UpdateAssumeRolePolicy
```

**What it proves**

The trust relationship for `SecurityAuditRole` was changed from broad
account-level trust to the named `security-auditor` identity with MFA.

**Why it matters**

A role's permissions policy controls what the role can do, while its trust
policy controls who may enter the role. This event proves that the role's trust
boundary was deliberately tightened.

**The screenshot should show**

- `eventName: UpdateAssumeRolePolicy`;
- `roleName: SecurityAuditRole`;
- initiating identity;
- event time.

![UpdateAssumeRolePolicy event](../evidence/screenshots/ct-06-update-audit-role-trust.png)

*Figure CT-06 — CloudTrail records the trust-policy update that restricted
`SecurityAuditRole` to the approved auditor workflow.*

> **Evidence-quality note:** The supplied screenshot identifies
> `SecurityAuditRole`, but its crop does not show
> `eventName: UpdateAssumeRolePolicy`. Recapture it with the event name and role
> name visible together.

---

## CT-07 — Disable the contractor access key

**Event**

```text
UpdateAccessKey
```

**What it proves**

The former contractor's active access key was changed to `Inactive` before
permanent deletion.

**Why it matters**

Disabling the key immediately stops it from authenticating while providing a
brief verification point before irreversible deletion.

**The screenshot should show**

- `eventName: UpdateAccessKey`;
- contractor user name;
- `status: Inactive`;
- a partially masked access-key ID;
- event time.

![UpdateAccessKey remediation event](../evidence/screenshots/ct-07-disable-contractor-key.png)

*Figure CT-07 — CloudTrail records that the former contractor's access key was
changed to `Inactive` before deletion. The access-key ID is partially masked.*

---

## CT-08 — Delete the contractor access key

**Event**

```text
DeleteAccessKey
```

**What it proves**

The inactive long-term credential was permanently deleted.

**Why it matters**

Disabling a key is reversible. Deleting it removes the abandoned credential and
completes the credential-removal stage of offboarding.

**The screenshot should show**

- `eventName: DeleteAccessKey`;
- contractor user name;
- a partially masked access-key ID;
- event time.

![DeleteAccessKey remediation event](../evidence/screenshots/ct-08-delete-contractor-key.png)

*Figure CT-08 — CloudTrail confirms permanent deletion of the former
contractor's long-term access key. The key ID is partially masked and no secret
value is published.*

---

## CT-09 — Delete the contractor identity

**Event**

```text
DeleteUser
```

**What it proves**

The former contractor's IAM user was deleted after the associated credential
and permissions were removed.

**Why it matters**

Deleting the user closes the abandoned identity path and prevents the identity
from being reused later without going through a new approved onboarding process.

**The screenshot should show**

- `eventName: DeleteUser`;
- contractor user name;
- initiating identity;
- event time.

![DeleteUser remediation event](../evidence/screenshots/ct-09-delete-contractor-user.png)

*Figure CT-09 — CloudTrail confirms deletion of the former contractor's IAM
identity after its access key and permission dependencies were removed.*

---

## CT-10 — Prove the secured audit role still works

**Event**

```text
AssumeRole
```

**What it must prove**

After the trust policy was restricted, the intended `security-auditor` could
still assume `SecurityAuditRole` through the approved MFA-protected workflow.

**Why it matters**

Good remediation removes unintended access without breaking legitimate work.
This event provides functional evidence that the secure audit path remained
available.

**The correct screenshot must show**

- `eventName: AssumeRole`;
- an intended human caller rather than `userIdentity.type: AWSService`;
- `requestParameters.roleArn` ending in `role/SecurityAuditRole`;
- a recognizable audit role-session name;
- successful response with no error code;
- MFA context where it is visible.

![SecurityAuditRole AssumeRole event](../evidence/screenshots/ct-10-security-auditor-assume-role.png)

*Figure CT-10 — CloudTrail records the approved auditor successfully assuming
`SecurityAuditRole` after its trust policy was restricted. Account identifiers,
temporary access-key IDs, and MFA-device identifiers are partially masked;
session tokens are removed completely.*

> **Do not use the supplied Resource Explorer screenshot.** It shows
> `userIdentity.type: AWSService`, `invokedBy:
> resource-explorer-2.amazonaws.com`, and an AWS service-linked role. It does
> not prove that `security-auditor` used `SecurityAuditRole`.

### How to find the correct CT-10 event

1. Sign in as `security-auditor` and complete the approved MFA-protected role
   switch to `SecurityAuditRole`.
2. Open **CloudTrail → Event history**.
3. Select the Region used for the AWS STS request.
4. Filter **Event name** by `AssumeRole`.
5. Open the matching events until
   `requestParameters.roleArn` ends in:

   ```text
   role/SecurityAuditRole
   ```

6. Confirm the caller represents the intended auditor, not an AWS service.
7. Capture the event name, caller, event time, role ARN, and role-session name.
8. Remove the complete `responseElements.credentials.sessionToken` value before
   publishing.

---

## Pre-publication redaction checklist

Before uploading any evidence to GitHub:

- partially mask the 12-digit AWS account ID, for example
  `0266XXXXXXXX`;
- partially mask principal IDs and access-key IDs;
- partially mask identifying S3 bucket suffixes and KMS key IDs;
- partially mask the public source IP address, for example
  `102.88.XXX.XXX`;
- remove secret access keys, session tokens, MFA codes, cookies, and
  authorization headers completely;
- leave the event name, event time, policy name, group name, role name, user
  name, and security-relevant request parameters visible;
- verify that every caption describes the exact event shown.

Opaque redaction should be applied to the image itself before it is uploaded.
Do not rely on a removable annotation layer.

## Evidence integrity notes

- CloudTrail Event history covers recent management events and is separate from
  the ongoing S3 delivery configured by a trail.
- The evidence records actions; it does not replace permission testing or the
  Python IAM risk scanner.
- A successful event should not show an `errorCode` or `errorMessage`.
- IAM names are case-sensitive in the evidence. Use the exact AWS resource names
  consistently throughout the walkthrough, architecture, captions, and
  screenshots.

## AWS references

- [Logging IAM and AWS STS API calls with AWS CloudTrail](https://docs.aws.amazon.com/IAM/latest/UserGuide/cloudtrail-integration.html)
- [Working with CloudTrail Event history](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html)
- [CloudTrail `userIdentity` reference](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-user-identity.html)
