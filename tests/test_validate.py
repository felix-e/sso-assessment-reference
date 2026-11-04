import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.validate import InputError, assess, load_confirmations, report, validate_evidence

ROOT = Path(__file__).resolve().parents[1]


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.apps = validate_evidence(json.loads((ROOT / "fixtures/synthetic-evidence.json").read_text()))
        self.confirmations = load_confirmations(ROOT / "fixtures/cmdb-confirmations.csv")

    def statuses(self, app, confirmations=None):
        return {check: status for check, status, _ in assess(app, self.confirmations if confirmations is None else confirmations)}

    def test_clean_synthetic_workforce_and_excluded_material(self):
        statuses = self.statuses(self.apps[0])
        for check in ("ownership", "cmdb_linkage", "credential_lifetime", "workforce_assignment"):
            self.assertEqual(statuses[check], "PASS")
        self.assertEqual(statuses["conditional_access"], "UNKNOWN")
        self.assertEqual(statuses["exceptions"], "REVIEW")

    def test_workload_negative_and_candidate_not_confirmation(self):
        statuses = self.statuses(self.apps[1])
        self.assertEqual(statuses["credential_lifetime"], "FAIL")
        self.assertEqual(statuses["cmdb_linkage"], "REVIEW")
        self.assertEqual(statuses["workforce_assignment"], "NOT_APPLICABLE")
        self.assertEqual(statuses["conditional_access"], "NOT_APPLICABLE")
        self.assertEqual(self.statuses(self.apps[0], {})["cmdb_linkage"], "UNKNOWN")

    def test_missing_evidence_never_passes(self):
        statuses = self.statuses(self.apps[2])
        self.assertNotIn("PASS", statuses.values())
        for check in ("ownership", "cmdb_linkage", "credential_lifetime", "workforce_assignment"):
            self.assertEqual(statuses[check], "UNKNOWN")

    def test_assignment_false_and_confirmation_mismatch(self):
        app = copy.deepcopy(self.apps[0])
        app.update(assignment_required=False, candidate_service_id="SYN-OTHER")
        self.assertEqual(self.statuses(app)["workforce_assignment"], "FAIL")
        self.assertEqual(self.statuses(app)["cmdb_linkage"], "REVIEW")

    def test_credential_boundaries_and_missing_lifetime(self):
        app = copy.deepcopy(self.apps[0])
        for credentials, expected in [([], "NOT_APPLICABLE"),
                ([{"kind": "sso_signing_certificate", "lifetime_days": 900}], "NOT_APPLICABLE"),
                ([{"kind": "platform_verification"}], "NOT_APPLICABLE"),
                ([{"kind": "app_certificate", "lifetime_days": 731}], "PASS"),
                ([{"kind": "app_secret"}], "UNKNOWN"),
                ([{"kind": "app_secret"}, {"kind": "app_certificate", "lifetime_days": 732}], "FAIL")]:
            with self.subTest(credentials=credentials):
                app["credentials"] = credentials
                self.assertEqual(self.statuses(app)["credential_lifetime"], expected)

    def test_strict_types_and_shapes(self):
        for patch in [{"assignment_required": "true"}, {"assignment_required": 1}, {"owner": False},
                      {"credentials": {}}, {"credentials": [{"kind": []}]},
                      {"credentials": [{"kind": "app_secret", "lifetime_days": True}]},
                      {"credentials": [{"kind": "app_secret", "lifetime_days": "90"}]},
                      {"credentials": [{"kind": "app_secret", "lifetime_days": -1}]},
                      {"unexpected": 1}, {"kind": "other"}]:
            with self.subTest(patch=patch), self.assertRaises(InputError):
                validate_evidence({"applications": [dict(self.apps[0], **patch)]})
        for data in [None, {}, {"applications": {}}, {"applications": [self.apps[0], self.apps[0]]}]:
            with self.subTest(data=data), self.assertRaises(InputError):
                validate_evidence(data)

    def test_csv_validation(self):
        header = "application_id,service_id,business_owner,confirmed\n"
        for value in ["bad\n", header + "a,s,o,True\n", header + "a,s,,true\n",
                      header + "a,s,o,true,extra\n", header + "a,s,o,true\na,s,o,true\n",
                      header + 'a,"unterminated,s,true\n']:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.csv"
                path.write_text(value)
                with self.assertRaises((InputError, csv.Error)):
                    load_confirmations(path)

    def test_null_unknowns_and_workload_app_credentials(self):
        app = {"id": "null-example", "kind": "workload", "owner": None,
               "candidate_service_id": None, "assignment_required": None, "credentials": None}
        validate_evidence({"applications": [app]})
        self.assertEqual(self.statuses(app)["credential_lifetime"], "UNKNOWN")
        app["credentials"] = [{"kind": "app_secret", "lifetime_days": 90}]
        self.assertEqual(self.statuses(app)["credential_lifetime"], "PASS")
        self.assertEqual(self.statuses(app)["ownership"], "UNKNOWN")

    def test_report_reproducible_and_checked_in(self):
        generated = report(self.apps, self.confirmations)
        self.assertEqual(generated, report(list(reversed(self.apps)), self.confirmations))
        self.assertEqual(generated, (ROOT / "examples/assessment-report.md").read_text())
        self.assertIn("Not audit evidence or application approval", generated)

    def test_cli_refuses_to_overwrite_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "input.json"
            confirmations = Path(directory) / "confirmations.csv"
            evidence.write_bytes((ROOT / "fixtures/synthetic-evidence.json").read_bytes())
            confirmations.write_bytes((ROOT / "fixtures/cmdb-confirmations.csv").read_bytes())
            originals = {path: path.read_bytes() for path in (evidence, confirmations)}
            for output in originals:
                result = subprocess.run([sys.executable, str(ROOT / "src/validate.py"),
                    str(evidence), str(confirmations), "--output", str(output)], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"output must not replace an input file", result.stderr)
                self.assertEqual({path: path.read_bytes() for path in originals}, originals)

    def test_cli_success_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.md"
            evidence = Path(directory) / "input.json"
            command = [sys.executable, str(ROOT / "src/validate.py"), str(evidence),
                       str(ROOT / "fixtures/cmdb-confirmations.csv"), "--output", str(output)]
            evidence.write_text((ROOT / "fixtures/synthetic-evidence.json").read_text())
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(output.read_text(), report(self.apps, self.confirmations))
            output.unlink()
            for malformed in ["{", '{"applications": [], "applications": []}', '{"applications": []}']:
                evidence.write_text(malformed)
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Input/output error:", result.stderr)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
