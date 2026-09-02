from __future__ import annotations

from research.semantic_integration.domains.diligence.constructor_v2.agent import MODEL
from research.semantic_integration.domains.diligence.constructor_v2.prompts import (
    FORBIDDEN_PROMPT_TOKENS,
    PASS_ORDER,
    PROMPTS,
)
from research.semantic_integration.domains.diligence.constructor_v2.runtime.contracts import (
    IDENTITY_CONTRACT,
    PURPOSE_B,
    PURPOSE_C,
)
from research.semantic_integration.domains.diligence.constructor_v2.runtime.verifier import (
    admit,
    verify_identity_disposition,
)


def test_model_is_composer():
    assert MODEL == "composer-2.5"
    assert "fast" not in MODEL


def test_prompts_omit_oracle_tokens():
    assert PASS_ORDER == ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8")
    for key, text in PROMPTS.items():
        for token in FORBIDDEN_PROMPT_TOKENS:
            assert token not in text, (key, token)
        assert "open_ar_assignment_restriction" not in text
    assert IDENTITY_CONTRACT.semantic_family_hint == "IDENTITY"
    assert "ACCEPT" not in PURPOSE_B.disposition_mapping


def test_verifier_rejects_unresolved_preservation_for_same():
    packet = {
        "selected_observations": [
            {
                "excerpt": "Legal has not determined which registry entity is the contracting party. Treat that registry link as unresolved."
            }
        ]
    }
    result = verify_identity_disposition(
        left="billing:Acme Inc.",
        right="registry:1",
        proposed="SAME_ENTITY",
        packet=packet,
        support_claim="names are similar",
    )
    assert result["result"] == "NOT_SUPPORTED"
    assert admit("SAME_ENTITY", result) == "UNRESOLVED"


def test_verifier_accepts_establishing_same():
    packet = {
        "selected_observations": [
            {"excerpt": "CRM Ltd is the operating name. Invoices use Limited. That is the same legal entity."}
        ]
    }
    result = verify_identity_disposition(
        left="crm:A",
        right="billing:Limited",
        proposed="SAME_ENTITY",
        packet=packet,
        support_claim="same legal entity",
    )
    assert result["result"] == "SUPPORTED"


def test_verifier_accepts_establishing_distinct():
    packet = {
        "selected_observations": [
            {"excerpt": "Industrial Systems Ltd is a different company; it has no current MSA."}
        ]
    }
    result = verify_identity_disposition(
        left="crm:A",
        right="registry:99",
        proposed="DISTINCT",
        packet=packet,
        support_claim="different company",
    )
    assert result["result"] == "SUPPORTED"


def test_verifier_does_not_use_fixture_names():
    import inspect
    from research.semantic_integration.domains.diligence.constructor_v2.runtime import verifier

    source = inspect.getsource(verifier)
    for token in ("Northbridge", "Delaware", "Wyoming"):
        assert token not in source


def test_purpose_c_allowed_kinds_are_declared():
    assert set(PURPOSE_C.allowed_kinds) == {"exclusivity", "auto_renewal", "rolling_term"}


def test_axis_c_certified_projection_exact(tmp_path):
    from research.semantic_integration.domains.diligence.constructor_v2.axis_c import run_axis_c

    payload = run_axis_c(tmp_path)
    assert payload["all_exact"] is True
    assert payload["source_reads"] == 0
    assert payload["invalid_kinds"]["invalid_purpose_kinds"] == 0
    assert payload["world_validation"]["ungrounded_assertions"] == 0
    assert payload["scores"]["B"]["exact"] is True
    assert payload["scores"]["D"]["pass"] is True


def test_axis_b_certified_all_zero(tmp_path):
    from research.semantic_integration.domains.diligence.constructor_v2.axis_b import run_axis_b

    payload = run_axis_b(tmp_path)
    assert payload["all_zero"] is True
