# Intended criteria and executable subset

This independently authored public synthetic reference illustrates a small subset of onboarding checks. It is not the historical pilot's complete catalogue, implementation or results. The intended criteria below are broader than the executable subset and are not a claim of coverage or adoption.

| Intended criterion | This reference | Boundary |
| --- | --- | --- |
| Identified and accountable ownership | `ownership`: presence only | Independent accountability verification remains human review |
| Confirmed service relationship and business owner | `cmdb_linkage`: separate confirmation CSV, candidate conflict detection | Does not query a CMDB or authenticate confirmation |
| Appropriate app/workload credential lifetime | `credential_lifetime`: reported days against illustrative 731-day limit | SSO signing/platform verification excluded; dates, expiry and rotation not implemented |
| Workforce assignment restriction | `workforce_assignment`: strict boolean | Not applicable to workload identities; no membership/role review |
| Conditional Access and authentication assurance | `conditional_access`: UNKNOWN for workforce | No policy coverage, exclusions, MFA or effective-access evaluation |
| Workload identity protection | Workforce checks marked NOT_APPLICABLE | No workload access-policy coverage evaluation |
| Approved, bounded exceptions | `exceptions`: REVIEW | No approval, dates, exception expiry or lifecycle logic |
| Protocol/configuration quality and service readiness | Review-only | No SAML/OIDC configuration, certificate health or operational testing |
| Joiner/mover/leaver and periodic recertification | Review-only | No lifecycle implementation |

A PASS is local to a supplied fact and check. There is no overall application approval, automated remediation, live collector or tenant connection. Missing evidence is not a safe default. The report exposes review and unknown boundaries even for the otherwise clean synthetic example.
