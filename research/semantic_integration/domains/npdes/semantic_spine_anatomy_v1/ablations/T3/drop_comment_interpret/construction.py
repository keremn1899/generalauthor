"""Build a purpose-sufficient semantic spine over NPDES structured sources."""
from __future__ import annotations
from source import Source, interval_contains, parse_date
from world_api import Purpose, World
FY2025_BEGIN = '2024-10-01'
FY2025_END = '2025-09-30'

def _text(value: object) -> str:
    return '' if value is None else str(value)

def _in_fy2025(date_value: object) -> bool:
    return interval_contains(date_value, FY2025_BEGIN, FY2025_END)

def construct(source: Source, world: World, purpose: Purpose) -> None:
    dmr_rows = source.rows('dmr_measurements.csv')
    permit_rows = source.rows('permit_limits.csv')
    documents = source.document_inventory()
    permit_index: dict[tuple[str, str, str], dict] = {}
    for row in permit_rows:
        key = (_text(row.get('LIMIT_VALUE_ID')), _text(row.get('NMBR_OF_SUBMISSION')), _text(row.get('NMBR_OF_REPORT')))
        permit_index[key] = row
    for row in dmr_rows:
        world.referent('measurement', {'dmr_form_value_id': _text(row.get('DMR_FORM_VALUE_ID'))})
        world.referent('limit', {'limit_id': _text(row.get('LIMIT_ID'))})
        world.referent('limit_value', {'limit_value_id': _text(row.get('LIMIT_VALUE_ID'))})
        world.referent('permit', {'external_permit_nmbr': _text(row.get('EXTERNAL_PERMIT_NMBR'))})
        world.referent('discharge_point', {'perm_feature_id': _text(row.get('PERM_FEATURE_ID'))})
        world.referent('parameter', {'parameter_code': _text(row.get('PARAMETER_CODE'))})
        world.referent('monitoring_period', {'period_end_date': parse_date(row.get('MONITORING_PERIOD_END_DATE')) or ''})
        world.referent('monitoring_event', {'dmr_event_id': _text(row.get('DMR_EVENT_ID'))})
        world.referent('limit_set', {'limit_set_id': _text(row.get('LIMIT_SET_ID'))})
        world.referent('limit_schedule', {'limit_set_schedule_id': _text(row.get('LIMIT_SET_SCHEDULE_ID'))})
    for row in permit_rows:
        world.referent('limit', {'limit_id': _text(row.get('LIMIT_ID'))})
        world.referent('limit_value', {'limit_value_id': _text(row.get('LIMIT_VALUE_ID'))})
        world.referent('permit', {'external_permit_nmbr': _text(row.get('EXTERNAL_PERMIT_NMBR'))})
        world.referent('discharge_point', {'perm_feature_id': _text(row.get('PERM_FEATURE_ID'))})
        world.referent('parameter', {'parameter_code': _text(row.get('PARAMETER_CODE'))})
        world.referent('limit_set', {'limit_set_id': _text(row.get('LIMIT_SET_ID'))})
        world.referent('limit_schedule', {'limit_set_schedule_id': _text(row.get('LIMIT_SET_SCHEDULE_ID'))})
    for doc in documents:
        world.referent('source_document', {'sha256': _text(doc.get('sha256'))}, grounding={'path': _text(doc.get('path'))})
    world.relation('document_catalog', [('document', 'REFERENT'), ('permit', 'REFERENT'), ('document_kind', 'TEXT'), ('filename', 'TEXT'), ('origin', 'TEXT')], description='Document inventory entries keyed by permit')
    document_catalog_rows = []
    for doc in documents:
        document_catalog_rows.append({'document': world.referent('source_document', {'sha256': _text(doc.get('sha256'))}), 'permit': world.referent('permit', {'external_permit_nmbr': _text(doc.get('permit'))}), 'document_kind': _text(doc.get('document_kind')), 'filename': _text(doc.get('filename')), 'origin': _text(doc.get('origin'))})
    world.map('document_catalog', document_catalog_rows)
    world.relation('measurement_record', [('measurement', 'REFERENT'), ('permit', 'REFERENT'), ('discharge_point', 'REFERENT'), ('parameter', 'REFERENT'), ('monitoring_period', 'REFERENT'), ('monitoring_event', 'REFERENT'), ('limit', 'REFERENT'), ('limit_value', 'REFERENT'), ('limit_set', 'REFERENT'), ('limit_schedule', 'REFERENT'), ('period_end_date', 'TEXT'), ('limit_begin_date', 'TEXT'), ('limit_end_date', 'TEXT'), ('value_type_code', 'TEXT'), ('limit_value_type_code', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('limit_unit_code', 'TEXT'), ('limit_type_code', 'TEXT'), ('statistical_base_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_sample_type_code', 'TEXT'), ('limit_freq_of_analysis_code', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('dmr_value_qualifier_code', 'TEXT'), ('dmr_unit_code', 'TEXT'), ('dmr_sample_type_code', 'TEXT'), ('nodi_code', 'TEXT'), ('nmbr_of_submission', 'TEXT'), ('nmbr_of_report', 'TEXT')], description='DMR measurement rows with source-coded fields')
    measurement_record_rows = []
    fy2025_measurement_rows = []
    measurement_permit_link_rows = []
    fy25_limit_evaluation_rows = []
    fy25_no_result_rows = []
    for row in dmr_rows:
        measurement_id = world.referent('measurement', {'dmr_form_value_id': _text(row.get('DMR_FORM_VALUE_ID'))})
        permit_id = world.referent('permit', {'external_permit_nmbr': _text(row.get('EXTERNAL_PERMIT_NMBR'))})
        discharge_id = world.referent('discharge_point', {'perm_feature_id': _text(row.get('PERM_FEATURE_ID'))})
        parameter_id = world.referent('parameter', {'parameter_code': _text(row.get('PARAMETER_CODE'))})
        period_end = parse_date(row.get('MONITORING_PERIOD_END_DATE')) or ''
        period_id = world.referent('monitoring_period', {'period_end_date': period_end})
        event_id = world.referent('monitoring_event', {'dmr_event_id': _text(row.get('DMR_EVENT_ID'))})
        limit_id = world.referent('limit', {'limit_id': _text(row.get('LIMIT_ID'))})
        limit_value_id = world.referent('limit_value', {'limit_value_id': _text(row.get('LIMIT_VALUE_ID'))})
        limit_set_id = world.referent('limit_set', {'limit_set_id': _text(row.get('LIMIT_SET_ID'))})
        schedule_id = world.referent('limit_schedule', {'limit_set_schedule_id': _text(row.get('LIMIT_SET_SCHEDULE_ID'))})
        record = {'measurement': measurement_id, 'permit': permit_id, 'discharge_point': discharge_id, 'parameter': parameter_id, 'monitoring_period': period_id, 'monitoring_event': event_id, 'limit': limit_id, 'limit_value': limit_value_id, 'limit_set': limit_set_id, 'limit_schedule': schedule_id, 'period_end_date': period_end, 'limit_begin_date': parse_date(row.get('LIMIT_BEGIN_DATE')) or '', 'limit_end_date': parse_date(row.get('LIMIT_END_DATE')) or '', 'value_type_code': _text(row.get('VALUE_TYPE_CODE')), 'limit_value_type_code': _text(row.get('LIMIT_VALUE_TYPE_CODE')), 'limit_value_nmbr': _text(row.get('LIMIT_VALUE_NMBR')), 'limit_value_qualifier_code': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'limit_unit_code': _text(row.get('LIMIT_UNIT_CODE')), 'limit_type_code': _text(row.get('LIMIT_TYPE_CODE')), 'statistical_base_code': _text(row.get('STATISTICAL_BASE_CODE')), 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'limit_sample_type_code': _text(row.get('LIMIT_SAMPLE_TYPE_CODE')), 'limit_freq_of_analysis_code': _text(row.get('LIMIT_FREQ_OF_ANALYSIS_CODE')), 'dmr_value_nmbr': _text(row.get('DMR_VALUE_NMBR')), 'dmr_value_qualifier_code': _text(row.get('DMR_VALUE_QUALIFIER_CODE')), 'dmr_unit_code': _text(row.get('DMR_UNIT_CODE')), 'dmr_sample_type_code': _text(row.get('DMR_SAMPLE_TYPE_CODE')), 'nodi_code': _text(row.get('NODI_CODE')), 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION')), 'nmbr_of_report': _text(row.get('NMBR_OF_REPORT'))}
        measurement_record_rows.append(record)
        if _in_fy2025(row.get('MONITORING_PERIOD_END_DATE')):
            fy2025_measurement_rows.append({'measurement': measurement_id})
        permit_key = (_text(row.get('LIMIT_VALUE_ID')), _text(row.get('NMBR_OF_SUBMISSION')), _text(row.get('NMBR_OF_REPORT')))
        permit_row = permit_index.get(permit_key)
        permit_limit_ref = ''
        dmr_comment_text = ''
        if permit_row is not None:
            permit_limit_ref = world.referent('permit_limit_row', {'limit_value_id': _text(permit_row.get('LIMIT_VALUE_ID')), 'limit_set_schedule_id': _text(permit_row.get('LIMIT_SET_SCHEDULE_ID')), 'nmbr_of_submission': _text(permit_row.get('NMBR_OF_SUBMISSION'))})
            dmr_comment_text = _text(permit_row.get('DMR_COMMENT_TEXT'))
            measurement_permit_link_rows.append({'measurement': measurement_id, 'permit_limit_row': permit_limit_ref, 'limit_value': limit_value_id})
        has_limit_number = bool(_text(row.get('LIMIT_VALUE_NMBR')).strip())
        has_dmr_number = bool(_text(row.get('DMR_VALUE_NMBR')).strip())
        if _in_fy2025(row.get('MONITORING_PERIOD_END_DATE')):
            fy25_limit_evaluation_rows.append({'measurement': measurement_id, 'limit_value': limit_value_id, 'permit_limit_row': permit_limit_ref, 'has_limit_value_number': 'true' if has_limit_number else 'false', 'has_dmr_value_number': 'true' if has_dmr_number else 'false', 'limit_value_qualifier_code': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'dmr_value_qualifier_code': _text(row.get('DMR_VALUE_QUALIFIER_CODE')), 'limit_unit_code': _text(row.get('LIMIT_UNIT_CODE')), 'value_type_code': _text(row.get('VALUE_TYPE_CODE')), 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'nodi_code': _text(row.get('NODI_CODE')), 'dmr_comment_text': dmr_comment_text})
            if not has_dmr_number or _text(row.get('NODI_CODE')).strip():
                fy25_no_result_rows.append({'measurement': measurement_id, 'permit': permit_id, 'parameter': parameter_id, 'monitoring_period': period_id, 'nodi_code': _text(row.get('NODI_CODE')), 'has_dmr_value_number': 'true' if has_dmr_number else 'false', 'has_limit_value_number': 'true' if has_limit_number else 'false', 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'dmr_comment_text': dmr_comment_text})
    world.map('measurement_record', measurement_record_rows)
    world.relation('permit_limit_record', [('permit_limit_row', 'REFERENT'), ('permit', 'REFERENT'), ('discharge_point', 'REFERENT'), ('parameter', 'REFERENT'), ('limit', 'REFERENT'), ('limit_value', 'REFERENT'), ('limit_set', 'REFERENT'), ('limit_schedule', 'REFERENT'), ('limit_begin_date', 'TEXT'), ('limit_end_date', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('limit_unit_code', 'TEXT'), ('limit_type_code', 'TEXT'), ('statistical_base_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_sample_type_code', 'TEXT'), ('limit_freq_of_analysis_code', 'TEXT'), ('dmr_comment_text', 'TEXT'), ('limit_set_status_flag', 'TEXT'), ('nmbr_of_submission', 'TEXT'), ('nmbr_of_report', 'TEXT'), ('jan', 'TEXT'), ('feb', 'TEXT'), ('mar', 'TEXT'), ('apr', 'TEXT'), ('may', 'TEXT'), ('jun', 'TEXT'), ('jul', 'TEXT'), ('aug', 'TEXT'), ('sep', 'TEXT'), ('oct', 'TEXT'), ('nov', 'TEXT'), ('dec', 'TEXT')], description='Permit limit schedule rows with seasonal and comment fields')
    permit_limit_record_rows = []
    fy25_monitoring_obligation_rows = []
    for row in permit_rows:
        permit_limit_row_id = world.referent('permit_limit_row', {'limit_value_id': _text(row.get('LIMIT_VALUE_ID')), 'limit_set_schedule_id': _text(row.get('LIMIT_SET_SCHEDULE_ID')), 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION'))})
        permit_id = world.referent('permit', {'external_permit_nmbr': _text(row.get('EXTERNAL_PERMIT_NMBR'))})
        record = {'permit_limit_row': permit_limit_row_id, 'permit': permit_id, 'discharge_point': world.referent('discharge_point', {'perm_feature_id': _text(row.get('PERM_FEATURE_ID'))}), 'parameter': world.referent('parameter', {'parameter_code': _text(row.get('PARAMETER_CODE'))}), 'limit': world.referent('limit', {'limit_id': _text(row.get('LIMIT_ID'))}), 'limit_value': world.referent('limit_value', {'limit_value_id': _text(row.get('LIMIT_VALUE_ID'))}), 'limit_set': world.referent('limit_set', {'limit_set_id': _text(row.get('LIMIT_SET_ID'))}), 'limit_schedule': world.referent('limit_schedule', {'limit_set_schedule_id': _text(row.get('LIMIT_SET_SCHEDULE_ID'))}), 'limit_begin_date': parse_date(row.get('LIMIT_BEGIN_DATE')) or '', 'limit_end_date': parse_date(row.get('LIMIT_END_DATE')) or '', 'limit_value_nmbr': _text(row.get('LIMIT_VALUE_NMBR')), 'limit_value_qualifier_code': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'limit_unit_code': _text(row.get('LIMIT_UNIT_CODE')), 'limit_type_code': _text(row.get('LIMIT_TYPE_CODE')), 'statistical_base_code': _text(row.get('STATISTICAL_BASE_CODE')), 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG')), 'limit_sample_type_code': _text(row.get('LIMIT_SAMPLE_TYPE_CODE')), 'limit_freq_of_analysis_code': _text(row.get('LIMIT_FREQ_OF_ANALYSIS_CODE')), 'dmr_comment_text': _text(row.get('DMR_COMMENT_TEXT')), 'limit_set_status_flag': _text(row.get('LIMIT_SET_STATUS_FLAG')), 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION')), 'nmbr_of_report': _text(row.get('NMBR_OF_REPORT')), 'jan': _text(row.get('JAN')), 'feb': _text(row.get('FEB')), 'mar': _text(row.get('MAR')), 'apr': _text(row.get('APR')), 'may': _text(row.get('MAY')), 'jun': _text(row.get('JUN')), 'jul': _text(row.get('JUL')), 'aug': _text(row.get('AUG')), 'sep': _text(row.get('SEP')), 'oct': _text(row.get('OCT')), 'nov': _text(row.get('NOV')), 'dec': _text(row.get('DEC'))}
        permit_limit_record_rows.append(record)
        active_during_fy = interval_contains(FY2025_BEGIN, row.get('LIMIT_BEGIN_DATE'), row.get('LIMIT_END_DATE')) or interval_contains(FY2025_END, row.get('LIMIT_BEGIN_DATE'), row.get('LIMIT_END_DATE'))
        if active_during_fy:
            fy25_monitoring_obligation_rows.append({'permit_limit_row': permit_limit_row_id, 'permit': permit_id, 'parameter': record['parameter'], 'discharge_point': record['discharge_point'], 'optional_monitoring_flag': record['optional_monitoring_flag'], 'limit_freq_of_analysis_code': record['limit_freq_of_analysis_code'], 'dmr_comment_text': record['dmr_comment_text'], 'limit_sample_type_code': record['limit_sample_type_code'], 'jan': record['jan'], 'feb': record['feb'], 'mar': record['mar'], 'apr': record['apr'], 'may': record['may'], 'jun': record['jun'], 'jul': record['jul'], 'aug': record['aug'], 'sep': record['sep'], 'oct': record['oct'], 'nov': record['nov'], 'dec': record['dec']})
    world.map('permit_limit_record', permit_limit_record_rows)
    world.relation('fy2025_measurement', [('measurement', 'REFERENT')], derived=True, description='Measurements whose monitoring period end falls in Federal FY2025')
    world.derive('fy2025_measurement', fy2025_measurement_rows, inputs=['measurement_record'], grounding={'fy_begin': FY2025_BEGIN, 'fy_end': FY2025_END})
    world.relation('measurement_permit_link', [('measurement', 'REFERENT'), ('permit_limit_row', 'REFERENT'), ('limit_value', 'REFERENT')], derived=True, description='Join DMR rows to permit limit rows on limit value and submission keys')
    world.derive('measurement_permit_link', measurement_permit_link_rows, inputs=['measurement_record', 'permit_limit_record'])
    world.relation('fy25_limit_evaluation', [('measurement', 'REFERENT'), ('limit_value', 'REFERENT'), ('permit_limit_row', 'REFERENT'), ('has_limit_value_number', 'TEXT'), ('has_dmr_value_number', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('dmr_value_qualifier_code', 'TEXT'), ('limit_unit_code', 'TEXT'), ('value_type_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('nodi_code', 'TEXT'), ('dmr_comment_text', 'TEXT')], mode='PURPOSE', description='FY2025 measurement/limit pairs for discharge limit applicability')
    world.map('fy25_limit_evaluation', fy25_limit_evaluation_rows)
    world.relation('fy25_monitoring_obligation', [('permit_limit_row', 'REFERENT'), ('permit', 'REFERENT'), ('parameter', 'REFERENT'), ('discharge_point', 'REFERENT'), ('optional_monitoring_flag', 'TEXT'), ('limit_freq_of_analysis_code', 'TEXT'), ('dmr_comment_text', 'TEXT'), ('limit_sample_type_code', 'TEXT'), ('jan', 'TEXT'), ('feb', 'TEXT'), ('mar', 'TEXT'), ('apr', 'TEXT'), ('may', 'TEXT'), ('jun', 'TEXT'), ('jul', 'TEXT'), ('aug', 'TEXT'), ('sep', 'TEXT'), ('oct', 'TEXT'), ('nov', 'TEXT'), ('dec', 'TEXT')], mode='PURPOSE', description='FY2025 permit monitoring requirements including conditional fields')
    world.map('fy25_monitoring_obligation', fy25_monitoring_obligation_rows)
    world.relation('fy25_no_result_case', [('measurement', 'REFERENT'), ('permit', 'REFERENT'), ('parameter', 'REFERENT'), ('monitoring_period', 'REFERENT'), ('nodi_code', 'TEXT'), ('has_dmr_value_number', 'TEXT'), ('has_limit_value_number', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('dmr_comment_text', 'TEXT')], mode='PURPOSE', description='FY2025 cases without an ordinary numeric reported result')
    world.map('fy25_no_result_case', fy25_no_result_rows)
    world.relation('numeric_comparison_candidate', [('measurement', 'REFERENT'), ('limit_value', 'REFERENT'), ('limit_value_nmbr', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('dmr_value_qualifier_code', 'TEXT'), ('limit_unit_code', 'TEXT'), ('value_type_code', 'TEXT')], mode='PURPOSE', derived=True, description='Measurements with structurally present numeric limit and reported values')
    numeric_comparison_rows = [{'measurement': row['measurement'], 'limit_value': row['limit_value'], 'limit_value_nmbr': rec['limit_value_nmbr'], 'dmr_value_nmbr': rec['dmr_value_nmbr'], 'limit_value_qualifier_code': rec['limit_value_qualifier_code'], 'dmr_value_qualifier_code': rec['dmr_value_qualifier_code'], 'limit_unit_code': rec['limit_unit_code'], 'value_type_code': rec['value_type_code']} for rec, row in zip(measurement_record_rows, fy25_limit_evaluation_rows) if row['has_limit_value_number'] == 'true' and row['has_dmr_value_number'] == 'true']
    world.derive('numeric_comparison_candidate', numeric_comparison_rows, inputs=['measurement_record', 'fy25_limit_evaluation'])
    purpose.require_materializable('fy25_measurements_materializable', relation='fy2025_measurement', purpose='A')
    purpose.require_materializable('fy25_limit_evaluations_materializable', relation='fy25_limit_evaluation', purpose='A')
    purpose.require_unique('unique_permit_limit_per_measurement', per='measurement', candidates='measurement_permit_link', purpose='A', cardinality='ONE')
    purpose.require_unique('unique_source_limit_value_per_measurement', per='measurement', candidates='measurement_record', purpose='A', cardinality='ONE')
    purpose.require_interpreted('limit_qualifier_for_comparison', relation='numeric_comparison_candidate', field='limit_value_qualifier_code', known=[''], purpose='A', per='measurement')
    purpose.require_interpreted('dmr_qualifier_for_comparison', relation='numeric_comparison_candidate', field='dmr_value_qualifier_code', known=[''], purpose='A', per='measurement')
    purpose.require_interpreted('limit_unit_for_comparison', relation='numeric_comparison_candidate', field='limit_unit_code', known=[''], purpose='A', per='measurement')
    purpose.require_interpreted('value_type_for_limit_selection', relation='fy25_limit_evaluation', field='value_type_code', known=[''], purpose='A', per='measurement')
    purpose.require_interpreted('optional_flag_for_limit_applicability', relation='fy25_limit_evaluation', field='optional_monitoring_flag', known=[''], purpose='A', per='measurement')
    purpose.require_interpreted('nodi_affects_limit_applicability', relation='fy25_limit_evaluation', field='nodi_code', known=[''], purpose='A', per='measurement')
    purpose.require_numeric('limit_value_numeric_for_comparison', relation='numeric_comparison_candidate', field='limit_value_nmbr', purpose='A', per='measurement')
    purpose.require_numeric('dmr_value_numeric_for_comparison', relation='numeric_comparison_candidate', field='dmr_value_nmbr', purpose='A', per='measurement')
    for row in fy25_limit_evaluation_rows:
        if row['dmr_comment_text'].strip():
            purpose.unresolved('permit_comment_affects_limit_applicability', subject={'measurement': row['measurement'], 'dmr_comment_text': row['dmr_comment_text']}, relation='fy25_limit_evaluation', reason='permit DMR comment may condition limit applicability', purpose='A')
        if row['has_limit_value_number'] == 'false' and row['has_dmr_value_number'] == 'true':
            purpose.unresolved('report_only_limit_with_numeric_measurement', subject={'measurement': row['measurement']}, relation='fy25_limit_evaluation', reason='reported numeric value without accompanying numeric limit in source', purpose='A')
        if row['limit_unit_code'] == '9A':
            purpose.unresolved('pass_fail_limit_comparison_semantics', subject={'measurement': row['measurement'], 'limit_unit_code': row['limit_unit_code']}, relation='fy25_limit_evaluation', reason='limit unit encoding is non-numeric pass/fail', purpose='A')
    purpose.require_materializable('document_catalog_materializable', relation='document_catalog', purpose='B')
    purpose.unresolved('permit_document_text_not_materialized', relation='document_catalog', reason='document inventory lists permit PDFs but document text is not in structured sources', purpose=['B', 'C'])
    purpose.require_materializable('fy25_monitoring_obligations_materializable', relation='fy25_monitoring_obligation', purpose='B')
    purpose.require_interpreted('optional_flag_for_monitoring_applicability', relation='fy25_monitoring_obligation', field='optional_monitoring_flag', known=[''], purpose='B', per='permit_limit_row')
    purpose.require_interpreted('frequency_code_for_monitoring_applicability', relation='fy25_monitoring_obligation', field='limit_freq_of_analysis_code', known=[''], purpose='B', per='permit_limit_row')
    purpose.require_interpreted('sample_type_for_monitoring_applicability', relation='fy25_monitoring_obligation', field='limit_sample_type_code', known=[''], purpose='B', per='permit_limit_row')
    for month in ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'):
        purpose.require_interpreted(f'seasonal_{month}_for_monitoring_applicability', relation='fy25_monitoring_obligation', field=month, known=[''], purpose='B', per='permit_limit_row')
    for row in fy25_monitoring_obligation_rows:
        if row['dmr_comment_text'].strip():
            purpose.unresolved('conditional_monitoring_requirement', subject={'permit_limit_row': row['permit_limit_row'], 'dmr_comment_text': row['dmr_comment_text']}, relation='fy25_monitoring_obligation', reason='permit comment indicates conditional or event-dependent monitoring', purpose='B')
    purpose.require_materializable('fy25_no_result_cases_materializable', relation='fy25_no_result_case', purpose='C')
    purpose.require_interpreted('nodi_code_semantics', relation='fy25_no_result_case', field='nodi_code', known=[''], purpose='C', per='measurement')
    purpose.require_interpreted('optional_flag_for_no_result_semantics', relation='fy25_no_result_case', field='optional_monitoring_flag', known=[''], purpose='C', per='measurement')
    for row in fy25_no_result_rows:
        nodi = row['nodi_code'].strip()
        if nodi:
            purpose.unresolved('nodi_establishes_no_result_state', subject={'measurement': row['measurement'], 'nodi_code': nodi}, relation='fy25_no_result_case', reason='NODI code present; documented no-data state requires interpretation', purpose='C')
        elif row['has_limit_value_number'] == 'true':
            purpose.unresolved('missing_result_with_numeric_limit', subject={'measurement': row['measurement']}, relation='fy25_no_result_case', reason='numeric limit present but no ordinary numeric reported result', purpose='C')
        if row['dmr_comment_text'].strip():
            purpose.unresolved('permit_comment_affects_no_result_semantics', subject={'measurement': row['measurement'], 'dmr_comment_text': row['dmr_comment_text']}, relation='fy25_no_result_case', reason='permit comment may explain conditional absence of monitoring result', purpose='C')
if __name__ == '__main__':
    from world_api import reset
    reset()
    world = World()
    construct(Source('sources'), world, Purpose(world))
