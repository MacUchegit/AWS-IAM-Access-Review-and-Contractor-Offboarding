#!/usr/bin/env python3
"""
IAM scanner for the FinSecure Labs project.

It checks only the three risks used in the project:

1. An IAM user has an active access key.
2. A custom permission policy uses wildcards.
3. A role trusts everyone or an entire AWS account.

The script only reads AWS configuration. It does not change anything.
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import boto3
from botocore.exceptions import BotoCoreError, ClientError, ProfileNotFound


# Every discovered risk is added to this list.
findings = []

# A valid AWS account ID contains exactly 12 numbers.
ACCOUNT_ID = re.compile(r"^\d{12}$")


def as_list(value):
    """Convert one value into a list so it is easy to loop through."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def get_all(client, operation, result_name, **options):
    """
    Retrieve all results from an AWS API.

    AWS sometimes divides a response into pages. The paginator makes sure
    the scanner reads every page.
    """
    paginator = client.get_paginator(operation)

    for page in paginator.paginate(**options):
        for item in page.get(result_name, []):
            yield item


def read_policy(document):
    """Convert an AWS policy document into a Python dictionary."""
    if isinstance(document, dict):
        return document

    return json.loads(unquote(document))


def add_finding(resource, risk, severity, evidence, recommendation):
    """Add one risk to the findings list."""
    findings.append(
        {
            "resource": resource,
            "risk": risk,
            "severity": severity,
            "evidence": evidence,
            "recommendation": recommendation,
        }
    )


def scan_users(iam):
    """Find IAM users with active long-term access keys."""
    for user in get_all(iam, "list_users", "Users"):
        user_name = user["UserName"]

        access_keys = get_all(
            iam,
            "list_access_keys",
            "AccessKeyMetadata",
            UserName=user_name,
        )

        for key in access_keys:
            if key["Status"] == "Active":
                add_finding(
                    resource=f"user/{user_name}",
                    risk="IAM user has an active access key",
                    severity="Medium",
                    evidence=(
                        f"Active key ending in {key['AccessKeyId'][-4:]}; "
                        f"created {key['CreateDate'].isoformat()}"
                    ),
                    recommendation=(
                        "Confirm who owns the key and whether it is still needed. "
                        "Deactivate and delete unused keys."
                    ),
                )


def scan_policies(iam):
    """Find attached custom policies that use wildcard permissions."""
    policies = get_all(
        iam,
        "list_policies",
        "Policies",
        Scope="Local",
        OnlyAttached=True,
    )

    for policy in policies:
        policy_name = policy["PolicyName"]

        response = iam.get_policy_version(
            PolicyArn=policy["Arn"],
            VersionId=policy["DefaultVersionId"],
        )
        document = read_policy(response["PolicyVersion"]["Document"])

        for statement_number, statement in enumerate(
            as_list(document.get("Statement")), start=1
        ):
            # A Deny statement does not grant access, so check only Allow.
            if statement.get("Effect") != "Allow":
                continue

            actions = as_list(statement.get("Action"))
            resources = as_list(statement.get("Resource"))

            # "*" means every action. "s3:*" means every S3 action.
            broad_actions = [
                action
                for action in actions
                if action == "*" or str(action).endswith(":*")
            ]
            broad_resource = "*" in resources

            if broad_actions or broad_resource:
                if "*" in broad_actions:
                    severity = "Critical"
                else:
                    severity = "High"

                add_finding(
                    resource=f"policy/{policy_name}",
                    risk="Permission policy contains wildcard access",
                    severity=severity,
                    evidence=(
                        f"Statement {statement_number}: "
                        f"Action={actions}, Resource={resources}"
                    ),
                    recommendation=(
                        "Replace wildcard actions with the required actions. "
                        "Use specific resource ARNs where AWS supports them."
                    ),
                )


def is_broad_principal(principal):
    """Check whether a role trusts everyone or an entire AWS account."""
    if principal == "*":
        return True

    if not isinstance(principal, dict):
        return False

    for aws_principal in as_list(principal.get("AWS")):
        aws_principal = str(aws_principal)

        if aws_principal == "*":
            return True

        # Example: 123456789012
        if ACCOUNT_ID.fullmatch(aws_principal):
            return True

        # Example: arn:aws:iam::123456789012:root
        if aws_principal.endswith(":root"):
            return True

    return False


def scan_roles(iam):
    """Find IAM roles with broad trust policies."""
    for role in get_all(iam, "list_roles", "Roles"):
        role_name = role["RoleName"]
        trust_policy = read_policy(role["AssumeRolePolicyDocument"])

        for statement_number, statement in enumerate(
            as_list(trust_policy.get("Statement")), start=1
        ):
            if statement.get("Effect") != "Allow":
                continue

            principal = statement.get("Principal")

            if is_broad_principal(principal):
                add_finding(
                    resource=f"role/{role_name}",
                    risk="Role trust policy allows a broad principal",
                    severity="High",
                    evidence=(
                        f"Statement {statement_number}: Principal={principal}"
                    ),
                    recommendation=(
                        "Trust only the intended user or role. Require MFA when "
                        "a human user assumes the role."
                    ),
                )


def create_report(account_id):
    """Build the final report and count each severity."""
    severity_order = {"Critical": 0, "High": 1, "Medium": 2}

    findings.sort(
        key=lambda item: (
            severity_order.get(item["severity"], 99),
            item["resource"],
        )
    )

    summary = {
        "critical": sum(item["severity"] == "Critical" for item in findings),
        "high": sum(item["severity"] == "High" for item in findings),
        "medium": sum(item["severity"] == "Medium" for item in findings),
        "total": len(findings),
    }

    return {
        "scan_date": datetime.now(timezone.utc).date().isoformat(),
        "account_id": account_id,
        "summary": summary,
        "findings": findings,
        "note": "Review every finding before making changes.",
    }


def get_arguments():
    """Read the profile and output path entered in the command."""
    parser = argparse.ArgumentParser(
        description="Scanner for three common IAM risks."
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="AWS CLI profile name, for example finsecure-lab.",
    )
    parser.add_argument(
        "--output",
        default="reports/iam-scan.json",
        help="Where the JSON report will be saved.",
    )
    return parser.parse_args()


def main():
    """Connect to AWS, run the checks, and save the JSON report."""
    arguments = get_arguments()

    try:
        session = boto3.Session(
            profile_name=arguments.profile,
            region_name="us-east-1",
        )

        iam = session.client("iam")
        sts = session.client("sts")

        account_id = sts.get_caller_identity()["Account"]
        print(f"Scanning AWS account {account_id}...")

        scan_users(iam)
        scan_policies(iam)
        scan_roles(iam)

        report = create_report(account_id)

        output_path = Path(arguments.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

        summary = report["summary"]
        print(f"Report saved to: {output_path.resolve()}")
        print(
            "Findings: "
            f"{summary['critical']} critical, "
            f"{summary['high']} high, "
            f"{summary['medium']} medium"
        )

    except (ProfileNotFound, BotoCoreError, ClientError) as error:
        print(f"Scanner failed: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())