"""Synthetic, offline checks. No application approval or live collection."""
import argparse
import csv
import json
from pathlib import Path

MAX_LIFETIME_DAYS = 731  # Illustrative two-year limit, not a Microsoft requirement.
CREDENTIAL_KINDS = {"app_secret", "app_certificate", "sso_signing_certificate", "platform_verification"}
EXCLUDED_KINDS = {"sso_signing_certificate", "platform_verification"}


class InputError(ValueError):
    """Evidence does not satisfy the synthetic contract."""


def text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_evidence(data):
    if not isinstance(data, dict) or set(data) != {"applications"} or not isinstance(data["applications"], list):
        raise InputError("root must contain only an applications list")
    seen = set()
    for app in data["applications"]:
        if not isinstance(app, dict) or set(app) - {"id", "kind", "owner", "candidate_service_id", "assignment_required", "credentials"}:
            raise InputError("invalid application fields")
        if not text(app.get("id")) or app["id"] in seen:
            raise InputError("application id must be nonempty and unique")
        seen.add(app["id"])
        if app.get("kind") not in ("workforce", "workload"):
            raise InputError("kind must be workforce or workload")
        for key in ("owner", "candidate_service_id"):
            if app.get(key) is not None and not text(app[key]):
                raise InputError(key + " must be nonempty text or null")
        if app.get("assignment_required") is not None and type(app["assignment_required"]) is not bool:
            raise InputError("assignment_required must be boolean or null")
        credentials = app.get("credentials")
        if credentials is None:
            continue
        if not isinstance(credentials, list):
            raise InputError("credentials must be a list or null")
        for credential in credentials:
            if not isinstance(credential, dict) or set(credential) - {"kind", "lifetime_days"}:
                raise InputError("invalid credential fields")
            if not isinstance(credential.get("kind"), str) or credential["kind"] not in CREDENTIAL_KINDS:
                raise InputError("unsupported credential kind")
            days = credential.get("lifetime_days")
            if days is not None and (type(days) is not int or days <= 0):
                raise InputError("lifetime_days must be a positive integer or null")
    return data["applications"]


def load_confirmations(path):
    confirmations = {}
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != ["application_id", "service_id", "business_owner", "confirmed"]:
            raise InputError("invalid confirmation CSV header")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise InputError("invalid confirmation CSV row")
            if not text(row["application_id"]) or row["application_id"] in confirmations:
                raise InputError("confirmation application_id must be nonempty and unique")
            if row["confirmed"] not in ("true", "false"):
                raise InputError("confirmed must be literal true or false")
            if row["confirmed"] == "true" and not all(text(row[key]) for key in ("service_id", "business_owner")):
                raise InputError("confirmed linkage needs service_id and business_owner")
            confirmations[row["application_id"]] = row
    return confirmations


def credential_result(app):
    credentials = app.get("credentials")
    if credentials is None:
        return "UNKNOWN", "Credential inventory missing."
    relevant = [c for c in credentials if c["kind"] not in EXCLUDED_KINDS]
    if not relevant:
        return "NOT_APPLICABLE", "Explicit inventory has no app/workload credentials; SSO signing and platform verification material excluded."
    days = [c.get("lifetime_days") for c in relevant]
    if any(d is not None and d > MAX_LIFETIME_DAYS for d in days):
        return "FAIL", "An app credential exceeds the synthetic 731-day lifetime limit."
    if None in days:
        return "UNKNOWN", "App credential lifetime evidence incomplete."
    return "PASS", "Reported app credential lifetimes meet the synthetic 731-day limit."


def assess(app, confirmations):
    results = [("ownership", "PASS" if app.get("owner") else "UNKNOWN",
                "Owner recorded; accountability not independently verified." if app.get("owner") else "Owner evidence missing.")]
    confirmation = confirmations.get(app["id"])
    if confirmation is None:
        status, detail = "UNKNOWN", "No independent CMDB confirmation supplied."
    elif confirmation["confirmed"] != "true":
        status, detail = "REVIEW", "Candidate linkage is not human-confirmed."
    else:
        status, detail = "PASS", "Independent CSV records confirmed service linkage and business owner."
        if app.get("candidate_service_id") and app["candidate_service_id"] != confirmation["service_id"]:
            status, detail = "REVIEW", "Candidate and confirmed service differ; resolve the discrepancy."
    results.append(("cmdb_linkage", status, detail))
    results.append(("credential_lifetime", *credential_result(app)))
    if app["kind"] == "workload":
        status, detail = "NOT_APPLICABLE", "Workforce assignment check does not apply to workload identities."
    elif app.get("assignment_required") is None:
        status, detail = "UNKNOWN", "Workforce assignment evidence missing."
    elif app["assignment_required"]:
        status, detail = "PASS", "Workforce assignment requirement reported enabled."
    else:
        status, detail = "FAIL", "Workforce assignment requirement reported disabled."
    results.append(("workforce_assignment", status, detail))
    results.append(("conditional_access", "UNKNOWN" if app["kind"] == "workforce" else "NOT_APPLICABLE",
                    "No Conditional Access coverage evaluation; workload controls require separate review."))
    results.append(("exceptions", "REVIEW", "Exception authority, dates and lifecycle are not evaluated."))
    return results


def markdown_text(value):
    # Prevent evidence labels from introducing Markdown structure or raw HTML.
    for char in "\\`*_{}[]<>()#!|":
        value = value.replace(char, "\\" + char)
    return value.replace("\r", " ").replace("\n", " ")


def report(applications, confirmations):
    lines = ["# Synthetic assessment report", "", "Offline synthetic inputs only. Not audit evidence or application approval.",
             "No overall verdict. PASS is limited to the stated check and supplied evidence.",
             "Policy: illustrative app credential lifetime maximum 731 days; no dates or expiry evaluation.", ""]
    for app in sorted(applications, key=lambda item: item["id"]):
        lines += ["## " + markdown_text(app["id"]), "", "| Check | Status | Basis / boundary |", "| --- | --- | --- |"]
        for check, status, detail in assess(app, confirmations):
            lines.append("| {} | {} | {} |".format(check, status, detail))
        lines.append("")
    return "\n".join(lines)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON key: " + key)
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("confirmations", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.resolve() in {args.evidence.resolve(), args.confirmations.resolve()}:
            raise InputError("output must not replace an input file")
        with args.evidence.open(encoding="utf-8") as handle:
            data = json.load(handle, object_pairs_hook=unique_object)
        applications = validate_evidence(data)
        confirmations = load_confirmations(args.confirmations)
        if set(confirmations) - {app["id"] for app in applications}:
            raise InputError("confirmation refers to an unknown application")
        args.output.write_text(report(applications, confirmations), encoding="utf-8")
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, "Input/output error: {}\n".format(error))
    return 0  # Successful evaluation, not a compliance result.


if __name__ == "__main__":
    raise SystemExit(main())
