"""C4 SQL derivations for purpose outputs."""

from __future__ import annotations

from taskview import Completeness, CompletenessStatus, RelationMode, Role, RoleType, TaskView


def register_derivations(tv: TaskView) -> None:
    tv.declare_relation(
        "purpose_a_study",
        [
            Role("registry_id", RoleType.TEXT),
            Role("publication_id", RoleType.TEXT),
            Role("correspondence", RoleType.TEXT),
        ],
        mode=RelationMode.DERIVED,
        description="Purpose A row: registered outcome traceability per study.",
    )
    tv.register_derivation(
        "purpose_a_study",
        sql="""
        WITH studies AS (
          SELECT study_id, replace(study_id, 'registry:', '') AS registry_id
          FROM registered_primary_outcome
        ),
        linked_pub AS (
          SELECT s.study_id, s.registry_id, j.right_id AS publication_ref,
                 replace(j.right_id, 'publication:', '') AS publication_id,
                 j.disposition AS identity_disp
          FROM studies s
          JOIN study_identity_judgment j
            ON j.left_id = s.study_id AND j.right_id LIKE 'publication:%'
          WHERE j.disposition = 'ACCEPT'
          UNION
          SELECT s.study_id, s.registry_id, j.left_id AS publication_ref,
                 replace(j.left_id, 'publication:', '') AS publication_id,
                 j.disposition AS identity_disp
          FROM studies s
          JOIN study_identity_judgment j
            ON j.right_id = s.study_id AND j.left_id LIKE 'publication:%'
          WHERE j.disposition = 'ACCEPT'
        ),
        has_candidate AS (
          SELECT s.study_id,
                 max(CASE WHEN j.disposition = 'UNRESOLVED' THEN 1 ELSE 0 END) AS identity_unresolved
          FROM studies s
          LEFT JOIN study_identity_judgment j
            ON (j.left_id = s.study_id AND j.right_id LIKE 'publication:%')
            OR (j.right_id = s.study_id AND j.left_id LIKE 'publication:%')
          GROUP BY s.study_id
        )
        SELECT s.registry_id,
               coalesce(lp.publication_id, '') AS publication_id,
               CASE
                 WHEN lp.study_id IS NULL AND coalesce(hc.identity_unresolved, 0) = 1
                   THEN 'unresolved'
                 WHEN lp.study_id IS NULL
                   THEN 'not_traced'
                 WHEN oc.disposition = 'ACCEPT'
                   THEN 'asserted'
                 ELSE 'unresolved'
               END AS correspondence
        FROM studies s
        LEFT JOIN linked_pub lp ON lp.study_id = s.study_id
        LEFT JOIN outcome_correspondence_judgment oc
          ON oc.study_id = s.study_id AND oc.publication_id = lp.publication_ref
        LEFT JOIN has_candidate hc ON hc.study_id = s.study_id
        ORDER BY s.registry_id
        """,
        inputs=[
            "registered_primary_outcome",
            "study_identity_judgment",
            "outcome_correspondence_judgment",
        ],
    )

    tv.declare_relation(
        "purpose_b_link",
        [
            Role("left", RoleType.TEXT),
            Role("right", RoleType.TEXT),
            Role("epistemic", RoleType.TEXT),
        ],
        mode=RelationMode.DERIVED,
        description="Purpose B row: cross-source study reconciliation link.",
    )
    tv.register_derivation(
        "purpose_b_link",
        sql="""
        SELECT left_id AS left,
               right_id AS right,
               CASE disposition
                 WHEN 'ACCEPT' THEN 'SAME_STUDY'
                 WHEN 'REJECT' THEN 'DISTINCT'
                 ELSE 'UNRESOLVED'
               END AS epistemic
        FROM study_identity_judgment
        ORDER BY left, right
        """,
        inputs=["study_identity_judgment"],
    )

    tv.declare_relation(
        "purpose_c_study",
        [
            Role("registry_id", RoleType.TEXT),
            Role("dataset_id", RoleType.TEXT),
            Role("status", RoleType.TEXT),
        ],
        mode=RelationMode.DERIVED,
        description="Purpose C row: primary-outcome reanalysis readiness per registry study.",
    )
    tv.register_derivation(
        "purpose_c_study",
        sql="""
        WITH studies AS (
          SELECT study_id, replace(study_id, 'registry:', '') AS registry_id
          FROM registered_primary_outcome
        ),
        linked_dataset AS (
          SELECT s.study_id, s.registry_id, j.right_id AS dataset_ref,
                 replace(j.right_id, 'dataset:', '') AS dataset_id,
                 j.disposition AS identity_disp
          FROM studies s
          JOIN study_identity_judgment j
            ON j.left_id = s.study_id AND j.right_id LIKE 'dataset:%'
          UNION
          SELECT s.study_id, s.registry_id, j.left_id AS dataset_ref,
                 replace(j.left_id, 'dataset:', '') AS dataset_id,
                 j.disposition AS identity_disp
          FROM studies s
          JOIN study_identity_judgment j
            ON j.right_id = s.study_id AND j.left_id LIKE 'dataset:%'
        ),
        identity_status AS (
          SELECT s.study_id,
                 max(CASE WHEN ld.identity_disp = 'ACCEPT' THEN ld.dataset_id END) AS accepted_dataset_id,
                 max(CASE WHEN ld.identity_disp = 'ACCEPT' THEN ld.dataset_ref END) AS accepted_dataset_ref,
                 max(CASE WHEN ld.identity_disp = 'UNRESOLVED' THEN 1 ELSE 0 END) AS has_unresolved_dataset
          FROM studies s
          LEFT JOIN linked_dataset ld ON ld.study_id = s.study_id
          GROUP BY s.study_id
        )
        SELECT s.registry_id,
               CASE
                 WHEN ist.has_unresolved_dataset = 1 AND ist.accepted_dataset_id IS NULL
                   THEN ''
                 ELSE coalesce(ist.accepted_dataset_id, '')
               END AS dataset_id,
               CASE
                 WHEN ist.has_unresolved_dataset = 1 AND ist.accepted_dataset_id IS NULL
                   THEN 'unresolved'
                 WHEN ist.accepted_dataset_ref IS NULL
                   THEN 'insufficient'
                 WHEN vs.disposition = 'ACCEPT'
                   THEN 'ready'
                 WHEN vs.disposition = 'REJECT'
                   THEN 'insufficient'
                 ELSE 'unresolved'
               END AS status
        FROM studies s
        JOIN identity_status ist ON ist.study_id = s.study_id
        LEFT JOIN variable_sufficiency_judgment vs
          ON vs.study_id = s.study_id AND vs.dataset_id = ist.accepted_dataset_ref
        ORDER BY s.registry_id
        """,
        inputs=[
            "registered_primary_outcome",
            "study_identity_judgment",
            "variable_sufficiency_judgment",
        ],
    )


def run_derivations(tv: TaskView) -> None:
    tv.run_derivation(
        "purpose_a_study",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="registered_primary_outcome",
        ),
    )
    tv.run_derivation(
        "purpose_b_link",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="study_identity_judgment",
        ),
    )
    tv.run_derivation(
        "purpose_c_study",
        completeness=Completeness(
            CompletenessStatus.COMPLETE,
            universe="registered_primary_outcome",
        ),
    )
