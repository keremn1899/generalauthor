"""Build a purpose-sufficient semantic spine over NPDES structured sources."""
from __future__ import annotations
from source import Source, interval_contains, parse_date
from world_api import Purpose, World
FY2025_BEGIN = '2024-10-01'
FY2025_END = '2025-09-30'
MONTH_FIELDS = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC')

def _looks_numeric(value: object) -> bool:
    text = str(value or '').strip().replace(',', '')
    if not text:
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False

def _text(value: object) -> str:
    return '' if value is None else str(value)

def construct(source: Source, world: World, purpose: Purpose) -> None:
    dmr_rows = source.rows('dmr_measurements.csv')
    limit_rows = source.rows('permit_limits.csv')
    documents = source.document_inventory()
    measurement_ids: dict[str, str] = {}
    limit_value_ids: dict[str, str] = {}
    requirement_ids: dict[tuple[str, str], str] = {}
    document_ids: dict[str, str] = {}
    for row in dmr_rows:
        dmr_value_id = _text(row.get('DMR_VALUE_ID'))
        measurement_ids[dmr_value_id] = world.referent('measurement', {'dmr_value_id': dmr_value_id}, grounding={'source': 'dmr_measurements.csv', 'dmr_form_value_id': row.get('DMR_FORM_VALUE_ID')})
    for row in limit_rows:
        limit_value_id = _text(row.get('LIMIT_VALUE_ID'))
        if limit_value_id not in limit_value_ids:
            limit_value_ids[limit_value_id] = world.referent('limit_value', {'limit_value_id': limit_value_id}, grounding={'source': 'permit_limits.csv'})
        req_key = (limit_value_id, _text(row.get('LIMIT_SET_SCHEDULE_ID')))
        requirement_ids[req_key] = world.referent('monitoring_requirement', {'limit_value_id': limit_value_id, 'limit_set_schedule_id': req_key[1]}, grounding={'source': 'permit_limits.csv', 'limit_id': row.get('LIMIT_ID')})
    for doc in documents:
        sha = _text(doc.get('sha256'))
        document_ids[sha] = world.referent('document', {'sha256': sha}, grounding={'source': 'document_inventory.json', 'path': doc.get('path')})
    world.relation('measurement_context', [('measurement', 'REFERENT'), ('permit', 'TEXT'), ('discharge_point', 'TEXT'), ('parameter_code', 'TEXT'), ('monitoring_period_end', 'TEXT'), ('monitoring_location', 'TEXT'), ('dmr_event_id', 'TEXT'), ('limit_id', 'TEXT'), ('limit_value_id', 'TEXT'), ('limit_set_id', 'TEXT'), ('limit_set_schedule_id', 'TEXT'), ('limit_set_designator', 'TEXT'), ('nmbr_of_submission', 'TEXT'), ('nmbr_of_report', 'TEXT')])
    world.relation('measurement_result', [('measurement', 'REFERENT'), ('dmr_value_nmbr', 'TEXT'), ('dmr_value_qualifier', 'TEXT'), ('dmr_value_standard_units', 'TEXT'), ('dmr_unit_code', 'TEXT'), ('nodi_code', 'TEXT'), ('value_type_code', 'TEXT')])
    world.relation('measurement_limit_snapshot', [('measurement', 'REFERENT'), ('limit_value_type_code', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier', 'TEXT'), ('limit_unit_code', 'TEXT'), ('limit_value_standard_units', 'TEXT'), ('statistical_base_code', 'TEXT'), ('statistical_base_type_code', 'TEXT'), ('limit_type_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_begin_date', 'TEXT'), ('limit_end_date', 'TEXT')])
    world.relation('monitoring_requirement_spec', [('requirement', 'REFERENT'), ('limit_value', 'REFERENT'), ('permit', 'TEXT'), ('discharge_point', 'TEXT'), ('parameter_code', 'TEXT'), ('limit_id', 'TEXT'), ('limit_value_id', 'TEXT'), ('limit_set_schedule_id', 'TEXT'), ('limit_set_designator', 'TEXT'), ('limit_set_name', 'TEXT'), ('limit_set_status_flag', 'TEXT'), ('limit_begin_date', 'TEXT'), ('limit_end_date', 'TEXT'), ('nmbr_of_submission', 'TEXT'), ('nmbr_of_report', 'TEXT'), ('limit_value_type_code', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier', 'TEXT'), ('limit_unit_code', 'TEXT'), ('statistical_base_code', 'TEXT'), ('statistical_base_type_code', 'TEXT'), ('limit_type_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_sample_type_code', 'TEXT'), ('limit_freq_of_analysis_code', 'TEXT'), ('all_months_limit', 'TEXT'), ('limit_season_id', 'TEXT'), ('dmr_comment_text', 'TEXT')])
    world.relation('requirement_season_month', [('requirement', 'REFERENT'), ('month', 'TEXT'), ('active_flag', 'TEXT')])
    world.relation('document_catalog', [('document', 'REFERENT'), ('permit', 'TEXT'), ('document_kind', 'TEXT'), ('path', 'TEXT'), ('filename', 'TEXT'), ('bytes', 'TEXT')])
    world.relation('limit_catalog_variant', [('limit_value', 'REFERENT'), ('requirement', 'REFERENT'), ('limit_set_schedule_id', 'TEXT'), ('nmbr_of_submission', 'TEXT'), ('nmbr_of_report', 'TEXT')])
    context_rows = []
    result_rows = []
    snapshot_rows = []
    for row in dmr_rows:
        dmr_value_id = _text(row.get('DMR_VALUE_ID'))
        measurement = measurement_ids[dmr_value_id]
        context_rows.append({'measurement': measurement, 'permit': _text(row.get('EXTERNAL_PERMIT_NMBR')), 'discharge_point': _text(row.get('PERM_FEATURE_NMBR')), 'parameter_code': _text(row.get('PARAMETER_CODE')), 'monitoring_period_end': _text(parse_date(row.get('MONITORING_PERIOD_END_DATE'))), 'monitoring_location': _text(row.get('MONITORING_LOCATION_CODE')), 'dmr_event_id': _text(row.get('DMR_EVENT_ID')), 'limit_id': _text(row.get('LIMIT_ID')), 'limit_value_id': _text(row.get('LIMIT_VALUE_ID')), 'limit_set_id': _text(row.get('LIMIT_SET_ID')), 'limit_set_schedule_id': _text(row.get('LIMIT_SET_SCHEDULE_ID')), 'limit_set_designator': _text(row.get('LIMIT_SET_DESIGNATOR')), 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION')), 'nmbr_of_report': _text(row.get('NMBR_OF_REPORT'))})
        result_rows.append({'measurement': measurement, 'dmr_value_nmbr': _text(row.get('DMR_VALUE_NMBR')), 'dmr_value_qualifier': _text(row.get('DMR_VALUE_QUALIFIER_CODE')), 'dmr_value_standard_units': _text(row.get('DMR_VALUE_STANDARD_UNITS')), 'dmr_unit_code': _text(row.get('DMR_UNIT_CODE')), 'nodi_code': _text(row.get('NODI_CODE')), 'value_type_code': _text(row.get('VALUE_TYPE_CODE'))})
        snapshot_rows.append({'measurement': measurement, 'limit_value_type_code': _text(row.get('LIMIT_VALUE_TYPE_CODE')), 'limit_value_nmbr': _text(row.get('LIMIT_VALUE_NMBR')), 'limit_value_qualifier': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'limit_unit_code': _text(row.get('LIMIT_UNIT_CODE')), 'limit_value_standard_units': _text(row.get('LIMIT_VALUE_STANDARD_UNITS')), 'statistical_base_code': _text(row.get('STATISTICAL_BASE_CODE')), 'statistical_base_type_code': _text(row.get('STATISTICAL_BASE_TYPE_CODE')), 'limit_type_code': _text(row.get('LIMIT_TYPE_CODE')), 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'limit_begin_date': _text(parse_date(row.get('LIMIT_BEGIN_DATE'))), 'limit_end_date': _text(parse_date(row.get('LIMIT_END_DATE')))})
    world.map('measurement_context', context_rows, grounding={'source': 'dmr_measurements.csv'})
    world.map('measurement_result', result_rows, grounding={'source': 'dmr_measurements.csv'})
    world.map('measurement_limit_snapshot', snapshot_rows, grounding={'source': 'dmr_measurements.csv'})
    requirement_rows = []
    season_rows = []
    catalog_rows = []
    for row in limit_rows:
        limit_value_id = _text(row.get('LIMIT_VALUE_ID'))
        schedule_id = _text(row.get('LIMIT_SET_SCHEDULE_ID'))
        requirement = requirement_ids[limit_value_id, schedule_id]
        limit_value = limit_value_ids[limit_value_id]
        requirement_rows.append({'requirement': requirement, 'limit_value': limit_value, 'permit': _text(row.get('EXTERNAL_PERMIT_NMBR')), 'discharge_point': _text(row.get('PERM_FEATURE_NMBR')), 'parameter_code': _text(row.get('PARAMETER_CODE')), 'limit_id': _text(row.get('LIMIT_ID')), 'limit_value_id': limit_value_id, 'limit_set_schedule_id': schedule_id, 'limit_set_designator': _text(row.get('LIMIT_SET_DESIGNATOR')), 'limit_set_name': _text(row.get('LIMIT_SET_NAME')), 'limit_set_status_flag': _text(row.get('LIMIT_SET_STATUS_FLAG')), 'limit_begin_date': _text(parse_date(row.get('LIMIT_BEGIN_DATE'))), 'limit_end_date': _text(parse_date(row.get('LIMIT_END_DATE'))), 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION')), 'nmbr_of_report': _text(row.get('NMBR_OF_REPORT')), 'limit_value_type_code': _text(row.get('LIMIT_VALUE_TYPE_CODE')), 'limit_value_nmbr': _text(row.get('LIMIT_VALUE_NMBR')), 'limit_value_qualifier': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'limit_unit_code': _text(row.get('LIMIT_UNIT_CODE')), 'statistical_base_code': _text(row.get('STATISTICAL_BASE_CODE')), 'statistical_base_type_code': _text(row.get('STATISTICAL_BASE_TYPE_CODE')), 'limit_type_code': _text(row.get('LIMIT_TYPE_CODE')), 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'limit_sample_type_code': _text(row.get('LIMIT_SAMPLE_TYPE_CODE')), 'limit_freq_of_analysis_code': _text(row.get('LIMIT_FREQ_OF_ANALYSIS_CODE')), 'all_months_limit': _text(row.get('ALL_MONTHS_LIMIT')), 'limit_season_id': _text(row.get('LIMIT_SEASON_ID')), 'dmr_comment_text': _text(row.get('DMR_COMMENT_TEXT'))})
        catalog_rows.append({'limit_value': limit_value, 'requirement': requirement, 'limit_set_schedule_id': schedule_id, 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION')), 'nmbr_of_report': _text(row.get('NMBR_OF_REPORT'))})
        for month in MONTH_FIELDS:
            season_rows.append({'requirement': requirement, 'month': month, 'active_flag': _text(row.get(month))})
    world.map('monitoring_requirement_spec', requirement_rows, grounding={'source': 'permit_limits.csv'})
    world.map('requirement_season_month', season_rows, grounding={'source': 'permit_limits.csv'})
    world.map('limit_catalog_variant', catalog_rows, grounding={'source': 'permit_limits.csv'})
    doc_rows = []
    for doc in documents:
        sha = _text(doc.get('sha256'))
        doc_rows.append({'document': document_ids[sha], 'permit': _text(doc.get('permit')), 'document_kind': _text(doc.get('document_kind')), 'path': _text(doc.get('path')), 'filename': _text(doc.get('filename')), 'bytes': _text(doc.get('bytes'))})
    world.map('document_catalog', doc_rows, grounding={'source': 'document_inventory.json'})
    limit_index: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in limit_rows:
        key = (_text(row.get('LIMIT_VALUE_ID')), _text(row.get('NMBR_OF_SUBMISSION')), _text(row.get('NMBR_OF_REPORT')))
        limit_index.setdefault(key, []).append(row)
    fy_rows = []
    active_rows = []
    schedule_match_rows = []
    comparison_rows = []
    no_result_rows = []
    report_only_rows = []
    for row in dmr_rows:
        dmr_value_id = _text(row.get('DMR_VALUE_ID'))
        measurement = measurement_ids[dmr_value_id]
        period_end = parse_date(row.get('MONITORING_PERIOD_END_DATE'))
        in_fy = interval_contains(period_end, FY2025_BEGIN, FY2025_END)
        if in_fy:
            fy_rows.append({'measurement': measurement})
        limit_begin = parse_date(row.get('LIMIT_BEGIN_DATE'))
        limit_end = parse_date(row.get('LIMIT_END_DATE'))
        if period_end and limit_begin and limit_end and (limit_begin <= period_end <= limit_end):
            active_rows.append({'measurement': measurement})
        key = (_text(row.get('LIMIT_VALUE_ID')), _text(row.get('NMBR_OF_SUBMISSION')), _text(row.get('NMBR_OF_REPORT')))
        matches = limit_index.get(key, [])
        for match in matches:
            schedule_match_rows.append({'measurement': measurement, 'requirement': requirement_ids[_text(match.get('LIMIT_VALUE_ID')), _text(match.get('LIMIT_SET_SCHEDULE_ID'))], 'limit_value': limit_value_ids[_text(match.get('LIMIT_VALUE_ID'))]})
        nodi = _text(row.get('NODI_CODE'))
        dmr_value = _text(row.get('DMR_VALUE_NMBR'))
        limit_value = _text(row.get('LIMIT_VALUE_NMBR'))
        if in_fy and (not nodi) and _looks_numeric(limit_value) and _looks_numeric(dmr_value):
            comparison_rows.append({'measurement': measurement, 'limit_value_nmbr': limit_value, 'limit_value_qualifier': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'dmr_value_nmbr': dmr_value, 'dmr_value_qualifier': _text(row.get('DMR_VALUE_QUALIFIER_CODE')), 'limit_value_standard_units': _text(row.get('LIMIT_VALUE_STANDARD_UNITS')), 'dmr_value_standard_units': _text(row.get('DMR_VALUE_STANDARD_UNITS'))})
        if in_fy and (nodi or not _looks_numeric(dmr_value)):
            no_result_rows.append({'measurement': measurement, 'nodi_code': nodi, 'dmr_value_nmbr': dmr_value, 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'limit_value_nmbr': limit_value})
        if in_fy and (not _looks_numeric(limit_value)):
            report_only_rows.append({'measurement': measurement, 'limit_value_nmbr': limit_value, 'limit_value_qualifier': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'limit_type_code': _text(row.get('LIMIT_TYPE_CODE')), 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG'))})
    world.relation('measurement_in_fy2025', [('measurement', 'REFERENT')], derived=True, description='Monitoring periods ending within Federal FY2025.')
    world.relation('limit_active_on_measurement_date', [('measurement', 'REFERENT')], derived=True, description='Limit interval contains the measurement monitoring period end.')
    world.relation('measurement_schedule_match', [('measurement', 'REFERENT'), ('requirement', 'REFERENT'), ('limit_value', 'REFERENT')], derived=True, description='Mechanical match on limit value id and schedule submission/report numbers.')
    world.relation('numeric_comparison_candidate', [('measurement', 'REFERENT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('dmr_value_qualifier', 'TEXT'), ('limit_value_standard_units', 'TEXT'), ('dmr_value_standard_units', 'TEXT')], mode='PURPOSE', derived=True, description='FY2025 measurements with numeric limit and numeric reported value and no NODI code.')
    world.relation('measurement_no_result', [('measurement', 'REFERENT'), ('nodi_code', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_value_nmbr', 'TEXT')], mode='PURPOSE', derived=True, description='FY2025 rows lacking an ordinary numeric reported result.')
    world.relation('non_numeric_limit_candidate', [('measurement', 'REFERENT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier', 'TEXT'), ('limit_type_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT')], mode='PURPOSE', derived=True, description='FY2025 measurements whose paired limit snapshot lacks a numeric limit value.')
    world.derive('measurement_in_fy2025', fy_rows, inputs=['measurement_context'])
    world.derive('limit_active_on_measurement_date', active_rows, inputs=['measurement_limit_snapshot'])
    world.derive('measurement_schedule_match', schedule_match_rows, inputs=['measurement_context', 'monitoring_requirement_spec'])
    world.derive('numeric_comparison_candidate', comparison_rows, inputs=['measurement_result', 'measurement_limit_snapshot', 'measurement_in_fy2025'], mode='PURPOSE')
    world.derive('measurement_no_result', no_result_rows, inputs=['measurement_result', 'measurement_in_fy2025'], mode='PURPOSE')
    world.derive('non_numeric_limit_candidate', report_only_rows, inputs=['measurement_limit_snapshot', 'measurement_in_fy2025'], mode='PURPOSE')
    purpose.require_materializable('fy2025_measurements_materializable', relation='measurement_in_fy2025', purpose=['A', 'B', 'C'])
    purpose.require_materializable('monitoring_requirements_materializable', relation='monitoring_requirement_spec', purpose=['B'])
    purpose.require_materializable('no_result_cases_materializable', relation='measurement_no_result', purpose=['C'])
    purpose.require_materializable('comparison_candidates_materializable', relation='numeric_comparison_candidate', purpose=['A'])
    purpose.require_materializable('non_numeric_limit_candidates_materializable', relation='non_numeric_limit_candidate', purpose=['A'])
    purpose.require_unique('unique_schedule_match_per_measurement', per='measurement', candidates='measurement_schedule_match', purpose=['A', 'B'], cardinality='ONE')
    purpose.require_unique('unique_catalog_variant_per_limit_value', per='limit_value', candidates='limit_catalog_variant', purpose=['B'], cardinality='ONE')
    purpose.require_numeric('comparison_limit_value_numeric', relation='numeric_comparison_candidate', field='limit_value_nmbr', purpose=['A'], per='measurement')
    purpose.require_numeric('comparison_reported_value_numeric', relation='numeric_comparison_candidate', field='dmr_value_nmbr', purpose=['A'], per='measurement')
    purpose.require_interpreted('comparison_limit_qualifier', relation='numeric_comparison_candidate', field='limit_value_qualifier', known=[''], purpose=['A'], per='measurement')
    purpose.require_interpreted('comparison_reported_qualifier', relation='numeric_comparison_candidate', field='dmr_value_qualifier', known=[''], purpose=['A'], per='measurement')
    purpose.require_interpreted('non_numeric_limit_classification', relation='non_numeric_limit_candidate', field='limit_type_code', known=[''], purpose=['A'], per='measurement')
    purpose.require_interpreted('non_numeric_limit_optional_flag', relation='non_numeric_limit_candidate', field='optional_monitoring_flag', known=[''], purpose=['A'], per='measurement')
    purpose.require_interpreted('requirement_comment_semantics', relation='monitoring_requirement_spec', field='dmr_comment_text', known=[''], purpose=['B'], per='requirement')
    purpose.require_interpreted('optional_monitoring_flag_semantics', relation='monitoring_requirement_spec', field='optional_monitoring_flag', known=[''], purpose=['B'], per='requirement')
    purpose.require_interpreted('limit_freq_semantics', relation='monitoring_requirement_spec', field='limit_freq_of_analysis_code', known=[''], purpose=['B'], per='requirement')
    purpose.require_interpreted('season_month_flag_semantics', relation='requirement_season_month', field='active_flag', known=[''], purpose=['B'], per='requirement')
    purpose.require_interpreted('nodi_code_semantics', relation='measurement_no_result', field='nodi_code', known=[''], purpose=['C'], per='measurement')
    purpose.require_interpreted('no_result_optional_monitoring_flag', relation='measurement_no_result', field='optional_monitoring_flag', known=[''], purpose=['C'], per='measurement')
    for row in limit_rows:
        comment = _text(row.get('DMR_COMMENT_TEXT'))
        if comment == 'WHEN DISCHARGING.':
            req_key = (_text(row.get('LIMIT_VALUE_ID')), _text(row.get('LIMIT_SET_SCHEDULE_ID')))
        if 'FOOTNOTE' in comment.upper() or 'FIRST YEAR OF THE PERMIT' in comment.upper():
            req_key = (_text(row.get('LIMIT_VALUE_ID')), _text(row.get('LIMIT_SET_SCHEDULE_ID')))
            purpose.unresolved('permit_year_condition_requires_document_text', subject={'requirement': requirement_ids[req_key], 'permit': row.get('EXTERNAL_PERMIT_NMBR'), 'parameter_code': row.get('PARAMETER_CODE'), 'dmr_comment_text': comment[:120]}, relation='monitoring_requirement_spec', reason='Monitoring frequency depends on permit-year outcome described in comment; only document inventory is available.', purpose=['B'], grounding={'source': 'permit_limits.csv', 'limit_value_id': row.get('LIMIT_VALUE_ID')})
    for row in dmr_rows:
        if not interval_contains(row.get('MONITORING_PERIOD_END_DATE'), FY2025_BEGIN, FY2025_END):
            continue
        limit_value = _text(row.get('LIMIT_VALUE_NMBR'))
        dmr_value = _text(row.get('DMR_VALUE_NMBR'))
        nodi = _text(row.get('NODI_CODE'))
        if _looks_numeric(limit_value) and (not _looks_numeric(dmr_value)) and (not nodi):
            measurement = measurement_ids[_text(row.get('DMR_VALUE_ID'))]
            purpose.unresolved('numeric_limit_without_reported_value_or_nodi', subject={'measurement': measurement, 'limit_value_nmbr': limit_value}, relation='measurement_result', reason='Numeric limit present but reported value absent without NODI classification.', purpose=['A', 'C'], grounding={'source': 'dmr_measurements.csv', 'dmr_value_id': row.get('DMR_VALUE_ID')})

def main() -> None:
    source = Source('sources')
    world = World()
    purpose = Purpose(world)
    construct(source, world, purpose)
if __name__ == '__main__':
    main()
