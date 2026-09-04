"""Build a purpose-sufficient semantic spine over NPDES structured sources."""
from __future__ import annotations
from collections import defaultdict
from source import Source, interval_contains, parse_date
from world_api import Purpose, World
FY_BEGIN = '2024-10-01'
FY_END = '2025-09-30'

def _text(value: object) -> str:
    return '' if value is None else str(value).strip()

def construct(source: Source, world: World, purpose: Purpose) -> None:
    dmr_rows = source.rows('dmr_measurements.csv')
    permit_rows = source.rows('permit_limits.csv')
    documents = source.document_inventory()
    permit_ids: dict[str, str] = {}
    discharge_point_ids: dict[str, str] = {}
    parameter_ids: dict[str, str] = {}
    limit_ids: dict[str, str] = {}
    limit_value_ids: dict[str, str] = {}
    measurement_ids: dict[str, str] = {}
    period_ids: dict[str, str] = {}
    document_ids: dict[str, str] = {}
    for row in dmr_rows + permit_rows:
        permit_key = _text(row.get('EXTERNAL_PERMIT_NMBR'))
        if permit_key and permit_key not in permit_ids:
            permit_ids[permit_key] = world.referent('permit', {'number': permit_key})
        feature_key = _text(row.get('PERM_FEATURE_ID'))
        if feature_key and feature_key not in discharge_point_ids:
            discharge_point_ids[feature_key] = world.referent('discharge_point', {'feature_id': feature_key})
        param_key = _text(row.get('PARAMETER_CODE'))
        if param_key and param_key not in parameter_ids:
            parameter_ids[param_key] = world.referent('parameter', {'code': param_key})
        limit_key = _text(row.get('LIMIT_ID'))
        if limit_key and limit_key not in limit_ids:
            limit_ids[limit_key] = world.referent('limit', {'limit_id': limit_key})
        lvid = _text(row.get('LIMIT_VALUE_ID'))
        if lvid and lvid not in limit_value_ids:
            limit_value_ids[lvid] = world.referent('limit_value', {'limit_value_id': lvid})
    for row in dmr_rows:
        form_id = _text(row.get('DMR_FORM_VALUE_ID'))
        if form_id and form_id not in measurement_ids:
            measurement_ids[form_id] = world.referent('dmr_measurement', {'form_value_id': form_id})
        period_raw = _text(row.get('MONITORING_PERIOD_END_DATE'))
        period_iso = parse_date(period_raw) or period_raw
        if period_iso and period_iso not in period_ids:
            period_ids[period_iso] = world.referent('monitoring_period', {'end_date': period_iso})
    for doc in documents:
        sha = _text(doc.get('sha256'))
        if sha and sha not in document_ids:
            document_ids[sha] = world.referent('document', {'sha256': sha})
    world.relation('permit_feature', [('permit', 'REFERENT'), ('discharge_point', 'REFERENT'), ('feature_number', 'TEXT')], description='Permit discharge point linkage from source rows')
    permit_feature_rows = []
    seen_pf: set[tuple[str, str]] = set()
    for row in permit_rows:
        permit_key = _text(row.get('EXTERNAL_PERMIT_NMBR'))
        feature_key = _text(row.get('PERM_FEATURE_ID'))
        key = (permit_key, feature_key)
        if not permit_key or not feature_key or key in seen_pf:
            continue
        seen_pf.add(key)
        permit_feature_rows.append({'permit': permit_ids[permit_key], 'discharge_point': discharge_point_ids[feature_key], 'feature_number': _text(row.get('PERM_FEATURE_NMBR'))})
    world.map('permit_feature', permit_feature_rows)
    world.relation('limit_value_specification', [('limit_value', 'REFERENT'), ('limit', 'REFERENT'), ('parameter', 'REFERENT'), ('discharge_point', 'REFERENT'), ('limit_value_type_code', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('limit_unit_code', 'TEXT'), ('statistical_base_code', 'TEXT'), ('statistical_base_type_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_type_code', 'TEXT'), ('limit_freq_of_analysis_code', 'TEXT'), ('limit_sample_type_code', 'TEXT'), ('dmr_comment_text', 'TEXT'), ('limit_set_designator', 'TEXT'), ('limit_set_schedule_id', 'TEXT'), ('nmbr_of_submission', 'TEXT')], description='Permit limit value rows (one per schedule/submission variant)')
    limit_value_spec_rows = []
    for row in permit_rows:
        lvid = _text(row.get('LIMIT_VALUE_ID'))
        limit_key = _text(row.get('LIMIT_ID'))
        param_key = _text(row.get('PARAMETER_CODE'))
        feature_key = _text(row.get('PERM_FEATURE_ID'))
        if not all([lvid, limit_key, param_key, feature_key]):
            continue
        limit_value_spec_rows.append({'limit_value': limit_value_ids[lvid], 'limit': limit_ids[limit_key], 'parameter': parameter_ids[param_key], 'discharge_point': discharge_point_ids[feature_key], 'limit_value_type_code': _text(row.get('LIMIT_VALUE_TYPE_CODE')), 'limit_value_nmbr': _text(row.get('LIMIT_VALUE_NMBR')), 'limit_value_qualifier_code': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'limit_unit_code': _text(row.get('LIMIT_UNIT_CODE')), 'statistical_base_code': _text(row.get('STATISTICAL_BASE_CODE')), 'statistical_base_type_code': _text(row.get('STATISTICAL_BASE_TYPE_CODE')), 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'limit_type_code': _text(row.get('LIMIT_TYPE_CODE')), 'limit_freq_of_analysis_code': _text(row.get('LIMIT_FREQ_OF_ANALYSIS_CODE')), 'limit_sample_type_code': _text(row.get('LIMIT_SAMPLE_TYPE_CODE')), 'dmr_comment_text': _text(row.get('DMR_COMMENT_TEXT')), 'limit_set_designator': _text(row.get('LIMIT_SET_DESIGNATOR')), 'limit_set_schedule_id': _text(row.get('LIMIT_SET_SCHEDULE_ID')), 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION'))})
    world.map('limit_value_specification', limit_value_spec_rows)
    world.relation('limit_effective_interval', [('limit', 'REFERENT'), ('begin_date', 'TEXT'), ('end_date', 'TEXT')], description='Limit effective date interval from source')
    limit_interval_rows = []
    seen_limits: set[str] = set()
    for row in permit_rows:
        limit_key = _text(row.get('LIMIT_ID'))
        if not limit_key or limit_key in seen_limits:
            continue
        seen_limits.add(limit_key)
        limit_interval_rows.append({'limit': limit_ids[limit_key], 'begin_date': parse_date(row.get('LIMIT_BEGIN_DATE')) or '', 'end_date': parse_date(row.get('LIMIT_END_DATE')) or ''})
    world.map('limit_effective_interval', limit_interval_rows)
    world.relation('measurement_reported', [('measurement', 'REFERENT'), ('permit', 'REFERENT'), ('discharge_point', 'REFERENT'), ('parameter', 'REFERENT'), ('limit', 'REFERENT'), ('limit_value', 'REFERENT'), ('monitoring_period', 'REFERENT'), ('monitoring_location_code', 'TEXT'), ('value_type_code', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('dmr_value_qualifier_code', 'TEXT'), ('dmr_unit_code', 'TEXT'), ('nodi_code', 'TEXT'), ('nmbr_of_submission', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('limit_type_code', 'TEXT')], description='DMR measurement rows grounded in source')
    measurement_reported_rows = []
    for row in dmr_rows:
        form_id = _text(row.get('DMR_FORM_VALUE_ID'))
        permit_key = _text(row.get('EXTERNAL_PERMIT_NMBR'))
        feature_key = _text(row.get('PERM_FEATURE_ID'))
        param_key = _text(row.get('PARAMETER_CODE'))
        limit_key = _text(row.get('LIMIT_ID'))
        lvid = _text(row.get('LIMIT_VALUE_ID'))
        period_raw = _text(row.get('MONITORING_PERIOD_END_DATE'))
        period_iso = parse_date(period_raw) or period_raw
        if not all([form_id, permit_key, feature_key, param_key, limit_key, lvid, period_iso]):
            continue
        measurement_reported_rows.append({'measurement': measurement_ids[form_id], 'permit': permit_ids[permit_key], 'discharge_point': discharge_point_ids[feature_key], 'parameter': parameter_ids[param_key], 'limit': limit_ids[limit_key], 'limit_value': limit_value_ids[lvid], 'monitoring_period': period_ids[period_iso], 'monitoring_location_code': _text(row.get('MONITORING_LOCATION_CODE')), 'value_type_code': _text(row.get('VALUE_TYPE_CODE')), 'dmr_value_nmbr': _text(row.get('DMR_VALUE_NMBR')), 'dmr_value_qualifier_code': _text(row.get('DMR_VALUE_QUALIFIER_CODE')), 'dmr_unit_code': _text(row.get('DMR_UNIT_CODE')), 'nodi_code': _text(row.get('NODI_CODE')), 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION')), 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'limit_value_nmbr': _text(row.get('LIMIT_VALUE_NMBR')), 'limit_value_qualifier_code': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'limit_type_code': _text(row.get('LIMIT_TYPE_CODE'))})
    world.map('measurement_reported', measurement_reported_rows)
    world.relation('document_inventory_entry', [('document', 'REFERENT'), ('permit', 'REFERENT'), ('document_kind', 'TEXT'), ('filename', 'TEXT')], description='Available permit documents (metadata only)')
    document_inventory_rows = []
    for doc in documents:
        sha = _text(doc.get('sha256'))
        permit_key = _text(doc.get('permit'))
        if not sha or not permit_key or permit_key not in permit_ids:
            continue
        document_inventory_rows.append({'document': document_ids[sha], 'permit': permit_ids[permit_key], 'document_kind': _text(doc.get('document_kind')), 'filename': _text(doc.get('filename'))})
    world.map('document_inventory_entry', document_inventory_rows)

    def _period_key_from_referent(ref: str, mapping: dict[str, str]) -> str:
        for key, rid in mapping.items():
            if rid == ref:
                return key
        return ''
    referent_fields = {'measurement', 'permit', 'discharge_point', 'parameter', 'limit', 'limit_value', 'monitoring_period'}
    fy_measurement_rows = [r for r in measurement_reported_rows if interval_contains(_period_key_from_referent(r['monitoring_period'], period_ids), FY_BEGIN, FY_END)]
    world.relation('fy2025_measurement', [(name, 'REFERENT' if name in referent_fields else 'TEXT') for name in measurement_reported_rows[0].keys()], derived=True, description='Measurements whose monitoring period end falls in Federal FY2025')
    world.derive('fy2025_measurement', fy_measurement_rows, inputs=['measurement_reported'])
    spec_index: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in limit_value_spec_rows:
        spec_index[row['limit_value'], row['nmbr_of_submission']].append(row)
    measurement_permit_match_rows = []
    for mrow in fy_measurement_rows:
        key = (mrow['limit_value'], mrow['nmbr_of_submission'])
        specs = spec_index.get(key, [])
        for spec in specs:
            merged = dict(mrow)
            merged['permit_limit_schedule_id'] = spec['limit_set_schedule_id']
            merged['permit_dmr_comment_text'] = spec['dmr_comment_text']
            merged['permit_optional_monitoring_flag'] = spec['optional_monitoring_flag']
            merged['permit_limit_freq_code'] = spec['limit_freq_of_analysis_code']
            measurement_permit_match_rows.append(merged)
    world.relation('measurement_permit_match', [('measurement', 'REFERENT'), ('permit', 'REFERENT'), ('discharge_point', 'REFERENT'), ('parameter', 'REFERENT'), ('limit', 'REFERENT'), ('limit_value', 'REFERENT'), ('monitoring_period', 'REFERENT'), ('monitoring_location_code', 'TEXT'), ('value_type_code', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('dmr_value_qualifier_code', 'TEXT'), ('dmr_unit_code', 'TEXT'), ('nodi_code', 'TEXT'), ('nmbr_of_submission', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('limit_type_code', 'TEXT'), ('permit_limit_schedule_id', 'TEXT'), ('permit_dmr_comment_text', 'TEXT'), ('permit_optional_monitoring_flag', 'TEXT'), ('permit_limit_freq_code', 'TEXT')], derived=True, description='FY2025 measurements joined to matching permit limit specification rows')
    world.derive('measurement_permit_match', measurement_permit_match_rows, inputs=['fy2025_measurement', 'limit_value_specification'])
    feature_to_permit = {_text(row.get('PERM_FEATURE_ID')): permit_ids[_text(row.get('EXTERNAL_PERMIT_NMBR'))] for row in permit_rows if _text(row.get('PERM_FEATURE_ID')) and _text(row.get('EXTERNAL_PERMIT_NMBR')) in permit_ids}
    world.relation('applicable_limit_candidate', [('measurement', 'REFERENT'), ('limit_value', 'REFERENT'), ('monitoring_period', 'REFERENT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('dmr_value_qualifier_code', 'TEXT'), ('limit_type_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT')], mode='PURPOSE', description='Candidate measurement/limit pairs for discharge limit applicability (Purpose A)')
    applicable_rows = [{'measurement': r['measurement'], 'limit_value': r['limit_value'], 'monitoring_period': r['monitoring_period'], 'limit_value_nmbr': r['limit_value_nmbr'], 'limit_value_qualifier_code': r['limit_value_qualifier_code'], 'dmr_value_nmbr': r['dmr_value_nmbr'], 'dmr_value_qualifier_code': r['dmr_value_qualifier_code'], 'limit_type_code': r['limit_type_code'], 'optional_monitoring_flag': r['optional_monitoring_flag']} for r in measurement_permit_match_rows]
    world.map('applicable_limit_candidate', applicable_rows)
    numeric_comparison_rows = [r for r in applicable_rows if _text(r['limit_value_nmbr']) and _text(r['dmr_value_nmbr'])]
    world.relation('numeric_limit_comparison_candidate', [('measurement', 'REFERENT'), ('limit_value', 'REFERENT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('dmr_value_qualifier_code', 'TEXT')], mode='PURPOSE', description='Measurement/limit pairs with both source numeric fields present (Purpose A)')
    world.map('numeric_limit_comparison_candidate', numeric_comparison_rows)
    world.relation('monitoring_obligation_candidate', [('limit_value', 'REFERENT'), ('limit', 'REFERENT'), ('parameter', 'REFERENT'), ('discharge_point', 'REFERENT'), ('permit', 'REFERENT'), ('optional_monitoring_flag', 'TEXT'), ('dmr_comment_text', 'TEXT'), ('limit_freq_of_analysis_code', 'TEXT'), ('limit_set_designator', 'TEXT'), ('limit_set_schedule_id', 'TEXT'), ('nmbr_of_submission', 'TEXT')], mode='PURPOSE', description='Permit limit rows as monitoring obligation candidates (Purpose B)')
    obligation_rows = []
    seen_obligation: set[tuple[str, str]] = set()
    discharge_point_keys = {v: k for k, v in discharge_point_ids.items()}
    for row in limit_value_spec_rows:
        lvid = row['limit_value']
        schedule = row['limit_set_schedule_id']
        key = (lvid, schedule)
        if key in seen_obligation:
            continue
        seen_obligation.add(key)
        feature_key = discharge_point_keys.get(row['discharge_point'], '')
        obligation_rows.append({'limit_value': lvid, 'limit': row['limit'], 'parameter': row['parameter'], 'discharge_point': row['discharge_point'], 'permit': feature_to_permit.get(feature_key, ''), 'optional_monitoring_flag': row['optional_monitoring_flag'], 'dmr_comment_text': row['dmr_comment_text'], 'limit_freq_of_analysis_code': row['limit_freq_of_analysis_code'], 'limit_set_designator': row['limit_set_designator'], 'limit_set_schedule_id': schedule, 'nmbr_of_submission': row['nmbr_of_submission']})
    world.map('monitoring_obligation_candidate', obligation_rows)
    world.relation('missing_result_case', [('measurement', 'REFERENT'), ('monitoring_period', 'REFERENT'), ('parameter', 'REFERENT'), ('nodi_code', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('optional_monitoring_flag', 'TEXT')], mode='PURPOSE', description='FY2025 cases without an ordinary numeric reported result (Purpose C)')
    missing_result_rows = [{'measurement': r['measurement'], 'monitoring_period': r['monitoring_period'], 'parameter': r['parameter'], 'nodi_code': r['nodi_code'], 'dmr_value_nmbr': r['dmr_value_nmbr'], 'limit_value_nmbr': r['limit_value_nmbr'], 'optional_monitoring_flag': r['optional_monitoring_flag']} for r in fy_measurement_rows if not _text(r['dmr_value_nmbr']) or _text(r['nodi_code'])]
    world.map('missing_result_case', missing_result_rows)
    purpose.require_materializable('applicable_limit_candidates_materializable', relation='applicable_limit_candidate', purpose='A')
    purpose.require_interpreted('limit_value_qualifier_for_comparison', relation='numeric_limit_comparison_candidate', field='limit_value_qualifier_code', known=[''], purpose='A', per='measurement')
    purpose.require_interpreted('dmr_value_qualifier_for_comparison', relation='numeric_limit_comparison_candidate', field='dmr_value_qualifier_code', known=[''], purpose='A', per='measurement')
    purpose.require_numeric('limit_value_numeric_for_comparison', relation='numeric_limit_comparison_candidate', field='limit_value_nmbr', purpose='A', per='measurement')
    purpose.require_numeric('dmr_value_numeric_for_comparison', relation='numeric_limit_comparison_candidate', field='dmr_value_nmbr', purpose='A', per='measurement')
    observed_limit_nmbrs = sorted({_text(r['limit_value_nmbr']) for r in applicable_rows if _text(r['limit_value_nmbr'])})
    purpose.require_interpreted('limit_value_nmbr_comparability', relation='applicable_limit_candidate', field='limit_value_nmbr', known=observed_limit_nmbrs, purpose='A', per='measurement')
    purpose.require_interpreted('limit_type_code_comparability', relation='applicable_limit_candidate', field='limit_type_code', known=[''], purpose='A', per='measurement')
    for row in applicable_rows:
        if not _text(row['limit_value_nmbr']):
            purpose.unresolved('limit_applicability_without_numeric_limit', subject={'measurement': row['measurement'], 'limit_value': row['limit_value']}, relation='applicable_limit_candidate', reason='no numeric limit value in source; enforceable vs report-only applicability not established', purpose='A')
    unmatched = [m for m in fy_measurement_rows if not any((c['measurement'] == m['measurement'] for c in measurement_permit_match_rows))]
    for row in unmatched:
        purpose.unresolved('measurement_permit_spec_unmatched', subject={'measurement': row['measurement'], 'limit_value': row['limit_value']}, relation='measurement_permit_match', reason='no permit limit specification row matches measurement submission number', purpose='A')
    purpose.require_materializable('monitoring_obligation_candidates_materializable', relation='monitoring_obligation_candidate', purpose='B')
    purpose.require_interpreted('optional_monitoring_flag_obligation', relation='monitoring_obligation_candidate', field='optional_monitoring_flag', known=[''], purpose='B', per='limit_value')
    purpose.require_interpreted('dmr_comment_obligation', relation='monitoring_obligation_candidate', field='dmr_comment_text', known=[''], purpose='B', per='limit_value')
    purpose.require_interpreted('limit_freq_obligation', relation='monitoring_obligation_candidate', field='limit_freq_of_analysis_code', known=[''], purpose='B', per='limit_value')
    for row in obligation_rows:
        comment = _text(row['dmr_comment_text'])
        if comment:
            purpose.unresolved('conditional_monitoring_applicability', subject={'limit_value': row['limit_value'], 'dmr_comment_text': comment}, relation='monitoring_obligation_candidate', reason='permit comment text present; conditional/event/seasonal applicability not established from structured sources alone', purpose='B')
    purpose.require_materializable('missing_result_cases_materializable', relation='missing_result_case', purpose='C')
    purpose.require_interpreted('nodi_code_semantics', relation='missing_result_case', field='nodi_code', known=[''], purpose='C', per='measurement')
    for row in missing_result_rows:
        nodi = _text(row['nodi_code'])
        has_dmr = bool(_text(row['dmr_value_nmbr']))
        has_limit = bool(_text(row['limit_value_nmbr']))
        if not nodi and (not has_dmr):
            purpose.unresolved('missing_result_without_nodi', subject={'measurement': row['measurement']}, relation='missing_result_case', reason='no numeric result and no NODI code; missing-evidence state not established', purpose='C')
        if nodi and has_limit and (not has_dmr):
            purpose.unresolved('nodi_with_limit_but_no_measurement', subject={'measurement': row['measurement'], 'nodi_code': nodi}, relation='missing_result_case', reason='NODI present with limit value but no measurement value; no-data semantics not fully established', purpose='C')
if __name__ == '__main__':
    src = Source('sources')
    world = World()
    purpose = Purpose(world)
    construct(src, world, purpose)
    snap = world.snapshot()
    print(f"referents={snap['n_referents']} relations={len(snap['relations'])} holes={snap['n_hole_instances']}")
