# Synthetic assessment report

Offline synthetic inputs only. Not audit evidence or application approval.
No overall verdict. PASS is limited to the stated check and supplied evidence.
Policy: illustrative app credential lifetime maximum 731 days; no dates or expiry evaluation.

## synthetic-portal

| Check | Status | Basis / boundary |
| --- | --- | --- |
| ownership | PASS | Owner recorded; accountability not independently verified. |
| cmdb_linkage | PASS | Independent CSV records confirmed service linkage and business owner. |
| credential_lifetime | PASS | Reported app credential lifetimes meet the synthetic 731-day limit. |
| workforce_assignment | PASS | Workforce assignment requirement reported enabled. |
| conditional_access | UNKNOWN | No Conditional Access coverage evaluation; workload controls require separate review. |
| exceptions | REVIEW | Exception authority, dates and lifecycle are not evaluated. |

## synthetic-unresolved

| Check | Status | Basis / boundary |
| --- | --- | --- |
| ownership | UNKNOWN | Owner evidence missing. |
| cmdb_linkage | UNKNOWN | No independent CMDB confirmation supplied. |
| credential_lifetime | UNKNOWN | Credential inventory missing. |
| workforce_assignment | UNKNOWN | Workforce assignment evidence missing. |
| conditional_access | UNKNOWN | No Conditional Access coverage evaluation; workload controls require separate review. |
| exceptions | REVIEW | Exception authority, dates and lifecycle are not evaluated. |

## synthetic-worker

| Check | Status | Basis / boundary |
| --- | --- | --- |
| ownership | PASS | Owner recorded; accountability not independently verified. |
| cmdb_linkage | REVIEW | Candidate linkage is not human-confirmed. |
| credential_lifetime | FAIL | An app credential exceeds the synthetic 731-day lifetime limit. |
| workforce_assignment | NOT_APPLICABLE | Workforce assignment check does not apply to workload identities. |
| conditional_access | NOT_APPLICABLE | No Conditional Access coverage evaluation; workload controls require separate review. |
| exceptions | REVIEW | Exception authority, dates and lifecycle are not evaluated. |
