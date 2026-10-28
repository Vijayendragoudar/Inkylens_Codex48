from types import SimpleNamespace

from backend.app.rules import run_deterministic_checks


def rule(**values):
    defaults = {
        "rule_key": "TERM-001",
        "rule_type": "forbidden_term",
        "title": "Avoid unsupported hype",
        "content": "revolutionary",
        "replacement": "Use a specific benefit.",
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_forbidden_term_is_reproducible_and_rule_linked():
    findings = run_deterministic_checks("A Revolutionary offer.", [rule()])

    assert len(findings) == 1
    assert findings[0].label == "forbidden terminology"
    assert findings[0].rule_keys == ["TERM-001"]
    assert "Revolutionary" in findings[0].excerpt


def test_preferred_term_offers_the_configured_replacement():
    findings = run_deterministic_checks(
        "Every customer is welcome.",
        [
            rule(
                rule_key="TERM-002",
                rule_type="preferred_term",
                title="Use guest instead of customer",
                content="customer",
                replacement="guest",
            )
        ],
    )

    assert findings[0].label == "preferred terminology"
    assert findings[0].suggestion == "Replace “customer” with “guest”."


def test_claim_restriction_is_unsupported_not_false():
    findings = run_deterministic_checks(
        "Results are guaranteed.",
        [
            rule(
                rule_key="CLAIM-001",
                rule_type="claim_constraint",
                title="No guarantees",
                content="guaranteed",
                replacement=None,
            )
        ],
    )

    assert findings[0].label == "unsupported/unverified"
    assert "false" not in findings[0].explanation.lower()


def test_all_caps_is_a_low_severity_accessibility_check():
    findings = run_deterministic_checks("TRY THIS TODAY", [])

    assert findings[0].category == "accessibility"
    assert findings[0].severity == "low"
