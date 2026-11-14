"""Fail unless a pytest JUnit XML report shows real, passing tests.

Used by CI instead of trusting pytest's exit code: Qt's offscreen platform
can crash during *interpreter teardown* on CI runners (after every test has
passed and the report is written), which would otherwise fail the job.
"""
import sys
import xml.etree.ElementTree as ET


def main(path: str) -> int:
    suite = ET.parse(path).getroot().find("testsuite")
    if suite is None:
        print(f"check_junit: no <testsuite> in {path}", file=sys.stderr)
        return 2
    tests = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    print(f"check_junit: {tests} tests, {failures} failures/errors, "
          f"{skipped} skipped")
    if tests == 0 or tests == skipped:
        print("check_junit: nothing actually ran", file=sys.stderr)
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "test-results.xml"))
