# AWS-IAM-Access-Review-and-Contractor-Offboarding

Project Walkthrough

This guide explains both what was done and why it matters. It is written fora recruiter, a technical reviewer, or someone encountering AWS identity securityfor the first time.

Scenario and scope

FinSecure Labs is a fictional financial-technology company with a private S3application bucket. A routine access review found three common problems:

the Developers group had broad S3 access;

a former contractor had an active programmatic access key;

a security-audit role trusted the entire AWS account.

The objective was to correct those risks without breaking the approved developeror auditor workflows, then retain evidence that the work occurred.

Lab safety: use a dedicated AWS lab account. Do not deliberately weaken aproduction account. Replace the fictional names if they conflict with existingresources.

Naming used in the lab

Resource

Lab name

Purpose

S3 bucket

finsecure-app-data-<unique-suffix>

Private application data

IAM group

Developers

Developer permission assignment

Developer users

dev-alex, dev-sam

Example human identities

Contractor user

contractor-jane

Offboarding scenario

Auditor user

security-auditor

Approved role user

Broad S3 policy

FinSecure-DeveloperBroadS3

Deliberately risky baseline

Restricted S3 policy

FinSecure-DeveloperAppBucketOnly

Least-privilege replacement

Audit role

SecurityAuditRole

Temporary security-review permissions

Executable templates use ${ACCOUNT_ID} and ${APP_BUCKET_NAME}. In publishedscreenshots and reports, identifiers are partly masked—for example,0266XXXXXXXX. A masked ID must never be pasted into a live policy.

Phase 1 — Establish the evidence baseline

Task 1: Secure the lab account

Action

Sign in as the root user only for initial account setup.

Enable MFA for the root user.

Confirm there are no root access keys.

Create an administrative identity for routine lab administration.

Sign out of root and use the administrative identity for the remaining work.

Reason

The root user has unrestricted account control. Protecting it and avoiding dailyroot use reduces the impact of a stolen password.



Figure 01 — Root MFA is enabled and no root access keys exist. Hide the accountemail and any MFA device details.

Task 2: Add a cost budget

Action

Open Billing and Cost Management → Budgets.

Create a monthly cost budget for the lab, such as USD 5.

Add an email alert before the budget reaches 100%.

Reason

Security labs should include cost control. A budget does not cap spending, but itprovides an early warning if a resource was left running.



Figure 02 — A small monthly lab budget and notification threshold are configured.Redact the notification email address.

Task 3: Enable CloudTrail management-event logging

Action

Open CloudTrail → Trails → Create trail.

Use a clear name such as finsecure-management-events.

Create or select a private S3 log bucket.

Make the trail multi-Region.

Include management events with both Read and Write activity.

Confirm Logging is on.

Reason

CloudTrail records API activity. Enabling it before the risky scenario is createdmeans identity creation, permission changes, credential removal, and role use canall be traced later.



Figure 03 — The multi-Region trail is logging management events.

Task 4: Enable an external-access analyzer

Action

Open IAM → Access Analyzer → Analyzers.

Create an External access analyzer for the current account.

Wait for its status to become Active.

Reason

An external-access analyzer identifies supported resources that can be accessedfrom outside the account. It complements this project’s custom IAM checks.



Figure 04 — The account-level external-access analyzer is active.

Phase 2 — Build a realistic risky starting point

Task 5: Create a private application bucket

Action

Create an S3 bucket using a globally unique name.

Keep Block all public access enabled.

Enable default encryption.

Upload a harmless sample file, such as sample-transaction.csv.

Reason

The bucket gives the developer policy a real resource to protect. The scenario isabout excessive identity permissions, not public S3 access, so the bucket remainsprivate.



Figure 05 — The application bucket is private and encrypted. Partly mask theunique bucket suffix if it could identify the account.

Task 6: Create the people and Developers group

Action

Create the Developers IAM group.

Create dev-alex, dev-sam, security-auditor, and contractor-jane.

Add the two developer users to Developers.

Do not create console passwords for identities that do not need console access.

Reason

Groups make permission assignment easier to review than attaching the same policyto several users. The contractor and auditor are kept separate because they havedifferent business purposes.



Figure 06 — The example users exist and the developer users belong to theDevelopers group. Partly mask generated user IDs.

Task 7: Attach an intentionally broad S3 policy

Action

Reviewpolicies/risky/developer-broad-s3.json.

Create FinSecure-DeveloperBroadS3.

Attach it to the Developers group.

Reason

The policy grants all S3 actions against all resources. That is a realisticleast-privilege failure: application developers need one bucket, not every bucketin the account.



Figure 07 — The risky policy contains s3:* and Resource: *. This lab-onlymisconfiguration establishes the baseline.

Task 8: Create an overly broad audit-role trust policy

Action

Substitute the real account number for ${ACCOUNT_ID} intrust-policies/before/security-audit-role.json.

Create SecurityAuditRole with that trust policy.

Attach only the read-only permissions needed for the audit demonstration.

Reason

The initial trust policy allows any suitably authorized principal in the accountto attempt role assumption. The remediation will narrow that trust to one namedauditor and require MFA.



Figure 08 — The role trusts the account root principal, representing the entireaccount. The 12-digit account number is partly masked.

Task 9: Allow the intended auditor to request the role

Action

Substitute the real account number for ${ACCOUNT_ID} inpolicies/identity/allow-security-audit-role.json.

Attach the policy to security-auditor.

Reason

Role assumption has two sides: the caller needs permission to callsts:AssumeRole, and the role must trust the caller. This policy handles thecaller-permission side.



Figure 09 — The auditor may request only the named SecurityAuditRole.

Task 10: Give the contractor a temporary lab access key

Action

Create one access key for contractor-jane.

Record only what is required to test the lab.

Never publish the secret access key.

Reason

Long-term keys are a common offboarding risk. The scanner should find this activecredential, after which the remediation removes it.



Figure 10 — The contractor has an active access key. Publish only a partly maskedkey ID such as AKIAXXXXXXXXXXXXXXXX; remove the secret completely.

Phase 3 — Detect and prove the starting risk

Task 11: Authenticate the local workstation safely

Action

Install AWS CLI v2.32.0 or later and Python 3.10 or later.

Give the scan identity the actions inpolicies/identity/iam-risk-scanner-read-only.json.

Create or select the finsecure-lab AWS CLI profile.

Use aws login --profile finsecure-lab, or aws login --remote when the browseris on another device.

Verify the caller:

aws sts get-caller-identity --profile finsecure-lab

Reason

aws login provides temporary credentials for local development. Temporarycredentials are safer than putting a new long-term access key in a localcredentials file.



Figure 11 — The scanner runs from an authenticated local profile. Partly mask theaccount and principal identifiers in the terminal.

Task 12: Run the baseline scan

Action

pip install -r requirements.txt
python iam_risk_scanner.py \
  --profile finsecure-lab \
  --output reports/before-scan.json

Compare the private output withreports/before-scan.example.json.

Expected result

High: wildcard S3 permission policy;

High: broad role trust;

Medium: active contractor access key.

Reason

The baseline creates a measurable statement of risk before any remediation. Abefore/after comparison is stronger than claiming a policy “looks better.”



Figure 12 — The redacted baseline report contains two High and one Mediumfinding.

Task 13: Prove the intended auditor can use the role

Action

From the auditor context, call sts:AssumeRole for SecurityAuditRole with avalid MFA code where required. Use the returned temporary credentials only for theapproved audit test, then let them expire.

Reason

Testing the permitted path avoids a false sense of security. A control is usefulonly if it blocks unintended access while preserving legitimate work.



Figure 13 — get-caller-identity shows an assumed-role session. Remove temporarycredentials and session tokens completely.

Task 14: Capture creation events in CloudTrail

Capture CreateUser, CreateAccessKey, CreatePolicy, AttachGroupPolicy,CreateRole, and AssumeRole. The detailed procedure and captions are inCLOUDTRAIL-EVIDENCE.md, Figures 14–19.

Reason

These events prove how the risky baseline was created and that the role wasactually used; they make the project reproducible and auditable.

Phase 4 — Remediate the access risks

Task 15: Replace broad S3 access with least privilege

Action

Substitute the real bucket name for ${APP_BUCKET_NAME} inpolicies/remediated/developer-app-bucket-only.json.

Create FinSecure-DeveloperAppBucketOnly.

Attach it to Developers.

Test the allowed application-bucket actions.

Detach FinSecure-DeveloperBroadS3.

Delete the broad policy after verifying it is no longer attached.

Reason

The replacement separates bucket-level listing from object-level operations anduses specific ARNs. Attaching and testing the new policy before deleting the oldone reduces the chance of an avoidable outage.



Figure 20 — Required S3 actions are limited to the application bucket and itsobjects.



Figure 21 — The Developers group has the replacement policy and no longer has thebroad policy.

Task 16: Offboard the contractor

Action

Confirm contractor-jane is the intended lab identity.

Change the access key status to Inactive.

Confirm there is no dependency on the key.

Delete the access key.

Remove any attached or inline permissions.

Delete the IAM user.

Reason

Deactivation provides a safe verification point; deletion then removes thelong-term credential permanently. Removing the user closes the abandoned identitypath.



Figure 22 — The contractor key is inactive before deletion.



Figure 23 — The contractor user no longer appears in the IAM user list.

Task 17: Restrict the audit role and require MFA

Action

Substitute the real account number for ${ACCOUNT_ID} intrust-policies/after/security-audit-role.json.

Update the SecurityAuditRole trust relationship.

Verify that the principal is only security-auditor.

Verify that aws:MultiFactorAuthPresent must be true.

Reason

The named principal removes account-wide trust. MFA adds a second proof of identitybefore a human can enter the security-audit role.



Figure 24 — Role trust is restricted to the named auditor and MFA.

Task 18: Retest the approved role workflow

Action

Confirm role assumption without MFA is denied.

Confirm the intended auditor can assume the role with MFA.

Run aws sts get-caller-identity inside the role session.

Reason

The expected denial proves the new condition is enforced; the expected successproves the legitimate workflow still works.



Figure 25 — The approved auditor successfully uses the restricted role with MFA.

Phase 5 — Validate, rescan, and preserve evidence

Task 19: Validate the policies before and after

Action

Use the IAM console policy editor’s validation or:

aws accessanalyzer validate-policy \
  --policy-type IDENTITY_POLICY \
  --policy-document file://policies/risky/developer-broad-s3.json

aws accessanalyzer validate-policy \
  --policy-type IDENTITY_POLICY \
  --policy-document file://policies/remediated/developer-app-bucket-only.json

Record the real output in the two validation-report templates in reports/.

Reason

Access Analyzer validation provides an AWS-native review in addition to thecustom scanner. Validation findings are not the same as runtime authorization, soboth policy review and functional testing remain necessary.



Figure 26 — Validation findings for the risky baseline are recorded withoutaltering the AWS response.



Figure 27 — The replacement policy’s validation result is recorded.

Task 20: Run the final scan

Action

python iam_risk_scanner.py \
  --profile finsecure-lab \
  --output reports/after-scan.json

Review the result before publishing. The example isreports/after-scan.example.json.

Expected result

The three scoped risks produce zero findings.

Reason

The second scan is a control check: it verifies that the risky policy, broad trust,and active contractor key are no longer present.



Figure 28 — The final scanner run completes successfully.



Figure 29 — The final redacted report contains zero findings for the scanner’sdefined scope.

Task 21: Capture remediation events

Capture CreatePolicy, AttachGroupPolicy, DetachGroupPolicy, DeletePolicy,UpdateAssumeRolePolicy, UpdateAccessKey, DeleteAccessKey, DeleteUser, andthe successful post-remediation AssumeRole. See Figures 30–38 inCLOUDTRAIL-EVIDENCE.md.

Reason

The event sequence proves that the safer policy was introduced, the risky policywas retired, the contractor was removed, and the role remained usable through theapproved path.

Task 22: Perform final acceptance checks

Action

Confirm the external-access analyzer has no unexplained findings.

Confirm S3 Block Public Access is still on.

Confirm the application bucket works for the approved developer actions.

Confirm an unrelated bucket or forbidden action is denied.

Confirm the audit role requires MFA.

Confirm the contractor user and key no longer exist.

Confirm the final scanner report and CloudTrail evidence are saved and redacted.



Figure 39 — Final external-access findings are reviewed and explained.



Figure 40 — S3 Block Public Access remains enabled after IAM remediation.

Definition of done

The project is complete when:

the three baseline risks can be explained in business terms;

the before report is preserved;

each remediation has a least-privilege reason;

allowed and denied behavior has been tested;

the final scanner returns no in-scope findings;

CloudTrail records the key actions;

all published evidence passes the redaction checklist.

Cleanup

After exporting approved evidence, delete lab-only identities and keys first, thenpolicies and roles, followed by empty S3 buckets and other temporary resources.Review the bill and confirm no unexpected resource remains. Keep a trail or logarchive only if its ongoing storage and protection are intentional.
