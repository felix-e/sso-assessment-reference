# Synthetic evidence contract

This is a new generic offline reference, not a release or complete reproduction of the historical tenant-connected pilot. All fixture identities and confirmations are invented. The evaluator does not establish authenticity, completeness or independent accountability. Outputs are not automatically audit evidence.

## JSON input

The root contains only `applications`, a list (possibly empty). Each application has a unique nonempty string `id` and `kind` exactly `workforce` or `workload`. Unknown fields and duplicate JSON keys are rejected.

Optional fields, omitted or null when unknown:

| Field | Accepted value | Meaning |
| --- | --- | --- |
| `owner` | Nonempty string | Recorded owner, not independently verified accountability |
| `candidate_service_id` | Nonempty string | Candidate only; no score or inference creates confirmation |
| `assignment_required` | JSON boolean | Reported workforce assignment setting |
| `credentials` | List of credential objects | Explicit inventory; null/missing is unknown, empty means explicitly none |

A credential has required `kind`: `app_secret`, `app_certificate`, `sso_signing_certificate` or `platform_verification`. Optional `lifetime_days` is a positive integer or null. Booleans, strings, fractional and nonpositive numbers are rejected. No other credential fields are accepted.

`app_secret` and `app_certificate` are app/workload credentials, for either application kind. The illustrative local limit is 731 days inclusive (the reference's two-year bound), **not a universal Microsoft requirement**. SSO signing certificates and platform service-principal verification material are excluded from that rule, not declared safe or healthy. Credential kinds are supplied facts, not inferred classifications. Missing inventory is UNKNOWN; an explicit inventory with only excluded kinds is NOT_APPLICABLE. Any excessive lifetime yields FAIL even if another lifetime is missing; otherwise missing applicable lifetimes yield UNKNOWN. No dates, expiry, rotation, revoked credentials or lifecycle are evaluated.

## Independent confirmation CSV

Exact ordered header: `application_id,service_id,business_owner,confirmed`.

One row at most per application; unknown application IDs are rejected by the CLI. `confirmed` must be literal lowercase `true` or `false`. A true row requires nonblank service ID and business owner. A false row may leave those fields empty. Extra/missing columns, duplicate IDs and malformed records are rejected. No trimming or fuzzy matching is performed on identifiers.

This separate synthetic source represents human confirmation; the tool cannot prove that a human performed it. A candidate alone yields UNKNOWN without a CSV row, or REVIEW with a false row. True confirmation with a conflicting candidate yields REVIEW; a true row without conflict yields PASS. Owner presence in JSON and owner presence in CSV do not prove independent accountability verification.

## Status vocabulary

- **PASS**: supplied evidence meets this narrow check, not application approval.
- **FAIL**: supplied evidence violates an implemented local check.
- **REVIEW**: human resolution needed or an explicitly unevaluated review boundary.
- **UNKNOWN**: relevant evidence missing or coverage not evaluated; never safe by default.
- **NOT_APPLICABLE**: this specific check is outside the declared identity/material scope, not an assurance statement.

Workforce assignment is PASS for true, FAIL for false, UNKNOWN for missing/null; workload assignment is NOT_APPLICABLE. Conditional Access coverage is always UNKNOWN for workforce and NOT_APPLICABLE to this workforce check for workload; workload-specific controls still need review. Exceptions are always REVIEW: no exception validity, approval, expiry or lifecycle checks exist. No overall verdict or remediation is produced.

## Execution boundary

Python 3.9+ standard library only. Inputs are local UTF-8 JSON/CSV. The CLI writes Markdown only after validation and rejects output paths that resolve to an input file; success exit code means evaluation completed, not checks passed. Input/output errors exit 2. An existing output is not removed on failure: do not mistake an old report for a fresh result. Reports sort by application ID and contain no timestamps. The YAML target example is documentation only and is never loaded. Use only synthetic inputs in this reference; do not put real tenant data or credentials here.
