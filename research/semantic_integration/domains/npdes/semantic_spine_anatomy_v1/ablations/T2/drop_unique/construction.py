"""Build a purpose-sufficient semantic spine over NPDES structured sources."""
from __future__ import annotations
from source import Source, interval_contains, parse_date
from world_api import Purpose, World
FY_BEGIN = '2024-10-01'
FY_END = '2025-09-30'
MONTH_COLUMNS = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC')

def _text(value: object) -> str:
    return '' if value is None else str(value).strip()

def _in_fy2025(period_end: object) -> bool:
    return interval_contains(period_end, FY_BEGIN, FY_END)

def _limit_active_for_period(row: dict, period_end: object) -> bool:
    return interval_contains(period_end, row.get('LIMIT_BEGIN_DATE'), row.get('LIMIT_END_DATE'))

def construct(source: Source, world: World, purpose: Purpose) -> None:
    dmr_rows = source.rows('dmr_measurements.csv')
    permit_rows = source.rows('permit_limits.csv')
    documents = source.document_inventory()
    facility_ids: set[str] = set()
    permit_ids: set[str] = set()
    feature_ids: set[str] = set()
    parameter_ids: set[str] = set()
    limit_ids: set[str] = set()
    limit_value_ids: set[str] = set()
    schedule_ids: set[str] = set()
    dmr_report_ids: set[str] = set()
    event_ids: set[str] = set()
    document_ids: set[str] = set()
    for row in dmr_rows + permit_rows:
        if _text(row.get('ACTIVITY_ID')):
            facility_ids.add(_text(row['ACTIVITY_ID']))
        if _text(row.get('EXTERNAL_PERMIT_NMBR')):
            permit_ids.add(_text(row['EXTERNAL_PERMIT_NMBR']))
        if _text(row.get('PERM_FEATURE_ID')):
            feature_ids.add(_text(row['PERM_FEATURE_ID']))
        if _text(row.get('PARAMETER_CODE')):
            parameter_ids.add(_text(row['PARAMETER_CODE']))
        if _text(row.get('LIMIT_ID')):
            limit_ids.add(_text(row['LIMIT_ID']))
        if _text(row.get('LIMIT_VALUE_ID')):
            limit_value_ids.add(_text(row['LIMIT_VALUE_ID']))
        if _text(row.get('LIMIT_SET_SCHEDULE_ID')):
            schedule_ids.add(_text(row['LIMIT_SET_SCHEDULE_ID']))
    for row in dmr_rows:
        if _text(row.get('DMR_FORM_VALUE_ID')):
            dmr_report_ids.add(_text(row['DMR_FORM_VALUE_ID']))
        if _text(row.get('DMR_EVENT_ID')):
            event_ids.add(_text(row['DMR_EVENT_ID']))
    for doc in documents:
        doc_key = _text(doc.get('sha256')) or _text(doc.get('path'))
        if doc_key:
            document_ids.add(doc_key)
    ref_facility = {fid: world.referent('facility', {'activity_id': fid}) for fid in sorted(facility_ids)}
    ref_permit = {pid: world.referent('permit', {'permit_number': pid}) for pid in sorted(permit_ids)}
    ref_feature = {fid: world.referent('discharge_point', {'perm_feature_id': fid}) for fid in sorted(feature_ids)}
    ref_parameter = {pcode: world.referent('parameter', {'parameter_code': pcode}) for pcode in sorted(parameter_ids)}
    ref_limit = {lid: world.referent('limit', {'limit_id': lid}) for lid in sorted(limit_ids)}
    ref_limit_value = {lvid: world.referent('limit_value', {'limit_value_id': lvid}) for lvid in sorted(limit_value_ids)}
    ref_schedule = {sid: world.referent('limit_set_schedule', {'limit_set_schedule_id': sid}) for sid in sorted(schedule_ids)}
    ref_dmr_report = {rid: world.referent('dmr_report', {'dmr_form_value_id': rid}) for rid in sorted(dmr_report_ids)}
    ref_event = {eid: world.referent('monitoring_event', {'dmr_event_id': eid}) for eid in sorted(event_ids)}
    ref_document = {did: world.referent('document', {'sha256': did}, grounding={'path': next((d.get('path') for d in documents if _text(d.get('sha256')) == did), '')}) for did in sorted(document_ids)}
    world.relation('facility_permit', [('facility', 'REFERENT'), ('permit', 'REFERENT'), ('activity_id', 'TEXT'), ('permit_number', 'TEXT')], description='Facility activity linked to external permit number.')
    world.relation('discharge_point_identity', [('discharge_point', 'REFERENT'), ('permit', 'REFERENT'), ('feature_number', 'TEXT'), ('feature_type_code', 'TEXT')], description='Permit discharge point identifiers.')
    world.relation('parameter_identity', [('parameter', 'REFERENT'), ('parameter_code', 'TEXT'), ('parameter_desc', 'TEXT')], description='Parameter code and description.')
    world.relation('limit_identity', [('limit', 'REFERENT'), ('permit', 'REFERENT'), ('discharge_point', 'REFERENT'), ('parameter', 'REFERENT'), ('limit_set_id', 'TEXT'), ('limit_set_designator', 'TEXT')], description='Limit identity within permit and discharge point.')
    world.relation('limit_value_identity', [('limit_value', 'REFERENT'), ('limit', 'REFERENT'), ('limit_value_type_code', 'TEXT'), ('statistical_base_code', 'TEXT'), ('statistical_base_type_code', 'TEXT')], description='Limit value row identity and statistical basis codes.')
    world.relation('limit_effective_interval', [('limit', 'REFERENT'), ('limit_begin_date', 'TEXT'), ('limit_end_date', 'TEXT')], description='Limit effective dates as parseable text.')
    world.relation('limit_value_magnitude', [('limit_value', 'REFERENT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_standard_units', 'TEXT'), ('limit_unit_code', 'TEXT'), ('limit_unit_desc', 'TEXT')], description='Limit numeric magnitude and units as reported.')
    world.relation('limit_value_qualifier_code', [('limit_value', 'REFERENT'), ('qualifier_code', 'TEXT')], description='Uninterpreted limit comparison qualifier code.')
    world.relation('limit_type_code', [('limit', 'REFERENT'), ('limit_type_code', 'TEXT')], description='Uninterpreted limit type code.')
    world.relation('optional_monitoring_flag', [('limit', 'REFERENT'), ('optional_monitoring_flag', 'TEXT')], description='Uninterpreted optional monitoring flag.')
    world.relation('monitoring_schedule', [('limit_set_schedule', 'REFERENT'), ('limit', 'REFERENT'), ('limit_freq_of_analysis_code', 'TEXT'), ('limit_sample_type_code', 'TEXT'), ('nmbr_of_submission', 'TEXT'), ('nmbr_of_report', 'TEXT'), ('all_months_limit', 'TEXT')], description='Permit monitoring schedule metadata.')
    world.relation('seasonal_month_flag', [('limit_set_schedule', 'REFERENT'), ('month', 'TEXT'), ('active_flag', 'TEXT')], description='Per-month monitoring activity flags from permit.')
    world.relation('permit_limit_comment', [('limit_set_schedule', 'REFERENT'), ('dmr_comment_text', 'TEXT')], description='Uninterpreted permit DMR comment text.')
    world.relation('dmr_measurement', [('dmr_report', 'REFERENT'), ('monitoring_event', 'REFERENT'), ('limit', 'REFERENT'), ('limit_value', 'REFERENT'), ('limit_set_schedule', 'REFERENT'), ('permit', 'REFERENT'), ('discharge_point', 'REFERENT'), ('parameter', 'REFERENT'), ('monitoring_period_end_date', 'TEXT'), ('value_received_date', 'TEXT'), ('limit_set_designator', 'TEXT')], description='DMR measurement row keyed by form value id.')
    world.relation('measurement_value', [('dmr_report', 'REFERENT'), ('dmr_value_nmbr', 'TEXT'), ('dmr_value_standard_units', 'TEXT'), ('dmr_unit_code', 'TEXT'), ('value_type_code', 'TEXT')], description='Reported measurement value fields.')
    world.relation('measurement_qualifier_code', [('dmr_report', 'REFERENT'), ('dmr_value_qualifier_code', 'TEXT')], description='Uninterpreted measurement qualifier code.')
    world.relation('measurement_nodi_code', [('dmr_report', 'REFERENT'), ('nodi_code', 'TEXT')], description='Uninterpreted no-data indicator code.')
    world.relation('document_inventory', [('document', 'REFERENT'), ('permit', 'REFERENT'), ('document_kind', 'TEXT'), ('filename', 'TEXT'), ('bytes', 'TEXT'), ('origin', 'TEXT')], description='Available permit-related documents (metadata only).')
    facility_permit_rows: list[dict] = []
    discharge_point_rows: list[dict] = []
    parameter_rows: list[dict] = []
    limit_identity_rows: list[dict] = []
    limit_value_identity_rows: list[dict] = []
    limit_interval_rows: list[dict] = []
    limit_magnitude_rows: list[dict] = []
    limit_qualifier_rows: list[dict] = []
    limit_type_rows: list[dict] = []
    optional_flag_rows: list[dict] = []
    schedule_rows: list[dict] = []
    seasonal_rows: list[dict] = []
    comment_rows: list[dict] = []
    dmr_measurement_rows: list[dict] = []
    measurement_value_rows: list[dict] = []
    measurement_qualifier_rows: list[dict] = []
    measurement_nodi_rows: list[dict] = []
    document_rows: list[dict] = []
    seen: set[tuple] = set()

    def _once(key: tuple, bucket: list[dict], row: dict) -> None:
        if key in seen:
            return
        seen.add(key)
        bucket.append(row)
    for row in permit_rows:
        permit_id = _text(row.get('EXTERNAL_PERMIT_NMBR'))
        facility_id = _text(row.get('ACTIVITY_ID'))
        feature_id = _text(row.get('PERM_FEATURE_ID'))
        parameter_code = _text(row.get('PARAMETER_CODE'))
        limit_id = _text(row.get('LIMIT_ID'))
        limit_value_id = _text(row.get('LIMIT_VALUE_ID'))
        schedule_id = _text(row.get('LIMIT_SET_SCHEDULE_ID'))
        _once(('facility_permit', facility_id, permit_id), facility_permit_rows, {'facility': ref_facility[facility_id], 'permit': ref_permit[permit_id], 'activity_id': facility_id, 'permit_number': permit_id})
        _once(('discharge_point', feature_id), discharge_point_rows, {'discharge_point': ref_feature[feature_id], 'permit': ref_permit[permit_id], 'feature_number': _text(row.get('PERM_FEATURE_NMBR')), 'feature_type_code': _text(row.get('PERM_FEATURE_TYPE_CODE'))})
        _once(('parameter', parameter_code), parameter_rows, {'parameter': ref_parameter[parameter_code], 'parameter_code': parameter_code, 'parameter_desc': _text(row.get('PARAMETER_DESC'))})
        _once(('limit', limit_id), limit_identity_rows, {'limit': ref_limit[limit_id], 'permit': ref_permit[permit_id], 'discharge_point': ref_feature[feature_id], 'parameter': ref_parameter[parameter_code], 'limit_set_id': _text(row.get('LIMIT_SET_ID')), 'limit_set_designator': _text(row.get('LIMIT_SET_DESIGNATOR'))})
        _once(('limit_interval', limit_id), limit_interval_rows, {'limit': ref_limit[limit_id], 'limit_begin_date': parse_date(row.get('LIMIT_BEGIN_DATE')) or _text(row.get('LIMIT_BEGIN_DATE')), 'limit_end_date': parse_date(row.get('LIMIT_END_DATE')) or _text(row.get('LIMIT_END_DATE'))})
        _once(('limit_type', limit_id), limit_type_rows, {'limit': ref_limit[limit_id], 'limit_type_code': _text(row.get('LIMIT_TYPE_CODE'))})
        _once(('optional_flag', limit_id), optional_flag_rows, {'limit': ref_limit[limit_id], 'optional_monitoring_flag': _text(row.get('OPTIONAL_MONITORING_FLAG'))})
        _once(('limit_value_identity', limit_value_id), limit_value_identity_rows, {'limit_value': ref_limit_value[limit_value_id], 'limit': ref_limit[limit_id], 'limit_value_type_code': _text(row.get('LIMIT_VALUE_TYPE_CODE')), 'statistical_base_code': _text(row.get('STATISTICAL_BASE_CODE')), 'statistical_base_type_code': _text(row.get('STATISTICAL_BASE_TYPE_CODE'))})
        _once(('limit_magnitude', limit_value_id), limit_magnitude_rows, {'limit_value': ref_limit_value[limit_value_id], 'limit_value_nmbr': _text(row.get('LIMIT_VALUE_NMBR')), 'limit_value_standard_units': _text(row.get('LIMIT_VALUE_STANDARD_UNITS')), 'limit_unit_code': _text(row.get('LIMIT_UNIT_CODE')), 'limit_unit_desc': _text(row.get('LIMIT_UNIT_DESC'))})
        _once(('limit_qualifier', limit_value_id), limit_qualifier_rows, {'limit_value': ref_limit_value[limit_value_id], 'qualifier_code': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE'))})
        _once(('schedule', schedule_id, limit_id), schedule_rows, {'limit_set_schedule': ref_schedule[schedule_id], 'limit': ref_limit[limit_id], 'limit_freq_of_analysis_code': _text(row.get('LIMIT_FREQ_OF_ANALYSIS_CODE')), 'limit_sample_type_code': _text(row.get('LIMIT_SAMPLE_TYPE_CODE')), 'nmbr_of_submission': _text(row.get('NMBR_OF_SUBMISSION')), 'nmbr_of_report': _text(row.get('NMBR_OF_REPORT')), 'all_months_limit': _text(row.get('ALL_MONTHS_LIMIT'))})
        comment_text = _text(row.get('DMR_COMMENT_TEXT'))
        if comment_text:
            _once(('comment', schedule_id), comment_rows, {'limit_set_schedule': ref_schedule[schedule_id], 'dmr_comment_text': comment_text})
        for month in MONTH_COLUMNS:
            _once(('season', schedule_id, month), seasonal_rows, {'limit_set_schedule': ref_schedule[schedule_id], 'month': month, 'active_flag': _text(row.get(month))})
    for row in dmr_rows:
        report_id = _text(row.get('DMR_FORM_VALUE_ID'))
        event_id = _text(row.get('DMR_EVENT_ID'))
        limit_id = _text(row.get('LIMIT_ID'))
        limit_value_id = _text(row.get('LIMIT_VALUE_ID'))
        schedule_id = _text(row.get('LIMIT_SET_SCHEDULE_ID'))
        permit_id = _text(row.get('EXTERNAL_PERMIT_NMBR'))
        feature_id = _text(row.get('PERM_FEATURE_ID'))
        parameter_code = _text(row.get('PARAMETER_CODE'))
        dmr_measurement_rows.append({'dmr_report': ref_dmr_report[report_id], 'monitoring_event': ref_event[event_id], 'limit': ref_limit[limit_id], 'limit_value': ref_limit_value[limit_value_id], 'limit_set_schedule': ref_schedule[schedule_id], 'permit': ref_permit[permit_id], 'discharge_point': ref_feature[feature_id], 'parameter': ref_parameter[parameter_code], 'monitoring_period_end_date': parse_date(row.get('MONITORING_PERIOD_END_DATE')) or _text(row.get('MONITORING_PERIOD_END_DATE')), 'value_received_date': parse_date(row.get('VALUE_RECEIVED_DATE')) or _text(row.get('VALUE_RECEIVED_DATE')), 'limit_set_designator': _text(row.get('LIMIT_SET_DESIGNATOR'))})
        measurement_value_rows.append({'dmr_report': ref_dmr_report[report_id], 'dmr_value_nmbr': _text(row.get('DMR_VALUE_NMBR')), 'dmr_value_standard_units': _text(row.get('DMR_VALUE_STANDARD_UNITS')), 'dmr_unit_code': _text(row.get('DMR_UNIT_CODE')), 'value_type_code': _text(row.get('VALUE_TYPE_CODE'))})
        measurement_qualifier_rows.append({'dmr_report': ref_dmr_report[report_id], 'dmr_value_qualifier_code': _text(row.get('DMR_VALUE_QUALIFIER_CODE'))})
        measurement_nodi_rows.append({'dmr_report': ref_dmr_report[report_id], 'nodi_code': _text(row.get('NODI_CODE'))})
    for doc in documents:
        doc_key = _text(doc.get('sha256')) or _text(doc.get('path'))
        permit_id = _text(doc.get('permit'))
        if not doc_key or permit_id not in ref_permit:
            continue
        document_rows.append({'document': ref_document[doc_key], 'permit': ref_permit[permit_id], 'document_kind': _text(doc.get('document_kind')), 'filename': _text(doc.get('filename')), 'bytes': _text(doc.get('bytes')), 'origin': _text(doc.get('origin'))})
    world.map('facility_permit', facility_permit_rows)
    world.map('discharge_point_identity', discharge_point_rows)
    world.map('parameter_identity', parameter_rows)
    world.map('limit_identity', limit_identity_rows)
    world.map('limit_value_identity', limit_value_identity_rows)
    world.map('limit_effective_interval', limit_interval_rows)
    world.map('limit_value_magnitude', limit_magnitude_rows)
    world.map('limit_value_qualifier_code', limit_qualifier_rows)
    world.map('limit_type_code', limit_type_rows)
    world.map('optional_monitoring_flag', optional_flag_rows)
    world.map('monitoring_schedule', schedule_rows)
    world.map('seasonal_month_flag', seasonal_rows)
    world.map('permit_limit_comment', comment_rows)
    world.map('dmr_measurement', dmr_measurement_rows)
    world.map('measurement_value', measurement_value_rows)
    world.map('measurement_qualifier_code', measurement_qualifier_rows)
    world.map('measurement_nodi_code', measurement_nodi_rows)
    world.map('document_inventory', document_rows)
    fy_dmr_rows = [row for row in dmr_rows if _in_fy2025(row.get('MONITORING_PERIOD_END_DATE'))]
    fy_report_ids = {_text(row.get('DMR_FORM_VALUE_ID')) for row in fy_dmr_rows}
    world.derive('fy2025_dmr_measurement', [{'dmr_report': ref_dmr_report[_text(row.get('DMR_FORM_VALUE_ID'))], 'monitoring_period_end_date': parse_date(row.get('MONITORING_PERIOD_END_DATE')) or _text(row.get('MONITORING_PERIOD_END_DATE'))} for row in fy_dmr_rows], roles=[('dmr_report', 'REFERENT'), ('monitoring_period_end_date', 'TEXT')], inputs=['dmr_measurement'])
    permit_by_schedule: dict[str, dict] = {}
    for row in permit_rows:
        key = (_text(row.get('LIMIT_ID')), _text(row.get('LIMIT_VALUE_ID')), _text(row.get('LIMIT_SET_SCHEDULE_ID')))
        permit_by_schedule[key] = row
    dmr_permit_link_rows: list[dict] = []
    for row in fy_dmr_rows:
        key = (_text(row.get('LIMIT_ID')), _text(row.get('LIMIT_VALUE_ID')), _text(row.get('LIMIT_SET_SCHEDULE_ID')))
        permit_row = permit_by_schedule.get(key)
        dmr_permit_link_rows.append({'dmr_report': ref_dmr_report[_text(row.get('DMR_FORM_VALUE_ID'))], 'limit': ref_limit[_text(row.get('LIMIT_ID'))], 'limit_value': ref_limit_value[_text(row.get('LIMIT_VALUE_ID'))], 'limit_set_schedule': ref_schedule[_text(row.get('LIMIT_SET_SCHEDULE_ID'))], 'permit_row_found': 'yes' if permit_row else 'no', 'limit_active_for_period': 'yes' if permit_row and _limit_active_for_period(permit_row, row.get('MONITORING_PERIOD_END_DATE')) else 'no'})
    world.derive('dmr_permit_link', dmr_permit_link_rows, roles=[('dmr_report', 'REFERENT'), ('limit', 'REFERENT'), ('limit_value', 'REFERENT'), ('limit_set_schedule', 'REFERENT'), ('permit_row_found', 'TEXT'), ('limit_active_for_period', 'TEXT')], inputs=['dmr_measurement', 'limit_value_identity', 'monitoring_schedule'])
    permit_requirement_keys: set[tuple[str, str]] = set()
    permit_requirement_rows: list[dict] = []
    for row in permit_rows:
        schedule_id = _text(row.get('LIMIT_SET_SCHEDULE_ID'))
        limit_id = _text(row.get('LIMIT_ID'))
        key = (limit_id, schedule_id)
        if key in permit_requirement_keys:
            continue
        permit_requirement_keys.add(key)
        permit_requirement_rows.append({'monitoring_requirement': world.referent('monitoring_requirement', {'limit_id': limit_id, 'limit_set_schedule_id': schedule_id}), 'limit': ref_limit[limit_id], 'limit_set_schedule': ref_schedule[schedule_id], 'permit': ref_permit[_text(row.get('EXTERNAL_PERMIT_NMBR'))], 'discharge_point': ref_feature[_text(row.get('PERM_FEATURE_ID'))], 'parameter': ref_parameter[_text(row.get('PARAMETER_CODE'))], 'limit_freq_of_analysis_code': _text(row.get('LIMIT_FREQ_OF_ANALYSIS_CODE')), 'has_dmr_comment': 'yes' if _text(row.get('DMR_COMMENT_TEXT')) else 'no'})
    world.derive('permit_monitoring_requirement', permit_requirement_rows, roles=[('monitoring_requirement', 'REFERENT'), ('limit', 'REFERENT'), ('limit_set_schedule', 'REFERENT'), ('permit', 'REFERENT'), ('discharge_point', 'REFERENT'), ('parameter', 'REFERENT'), ('limit_freq_of_analysis_code', 'TEXT'), ('has_dmr_comment', 'TEXT')], inputs=['monitoring_schedule', 'limit_identity'])
    reported_schedule_keys = {(_text(row.get('LIMIT_ID')), _text(row.get('LIMIT_SET_SCHEDULE_ID'))) for row in fy_dmr_rows}
    requirement_evidence_rows: list[dict] = []
    for req in permit_requirement_rows:
        limit_id = req['limit']
        schedule_id = req['limit_set_schedule']
        source_key = None
        for row in permit_rows:
            if ref_limit[_text(row.get('LIMIT_ID'))] == limit_id and ref_schedule[_text(row.get('LIMIT_SET_SCHEDULE_ID'))] == schedule_id:
                source_key = (_text(row.get('LIMIT_ID')), _text(row.get('LIMIT_SET_SCHEDULE_ID')))
                break
        has_fy_dmr = 'yes' if source_key in reported_schedule_keys else 'no'
        requirement_evidence_rows.append({'monitoring_requirement': req['monitoring_requirement'], 'fy2025_dmr_present': has_fy_dmr})
    world.derive('requirement_fy2025_dmr_evidence', requirement_evidence_rows, roles=[('monitoring_requirement', 'REFERENT'), ('fy2025_dmr_present', 'TEXT')], inputs=['permit_monitoring_requirement', 'fy2025_dmr_measurement'])
    world.relation('numeric_comparison_pair', [('dmr_report', 'REFERENT'), ('limit_value', 'REFERENT'), ('dmr_value_nmbr', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('limit_value_qualifier_code', 'TEXT'), ('dmr_value_qualifier_code', 'TEXT'), ('limit_set_designator', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('nodi_code', 'TEXT')], mode='PURPOSE', description='FY2025 measurement/limit pairs where both sides expose numeric text.')
    world.relation('no_numeric_result_case', [('dmr_report', 'REFERENT'), ('limit', 'REFERENT'), ('parameter', 'REFERENT'), ('monitoring_period_end_date', 'TEXT'), ('dmr_value_nmbr', 'TEXT'), ('limit_value_nmbr', 'TEXT'), ('nodi_code', 'TEXT'), ('optional_monitoring_flag', 'TEXT'), ('limit_set_designator', 'TEXT')], mode='PURPOSE', description='FY2025 rows lacking an ordinary numeric reported result.')
    world.relation('monitoring_obligation_subject', [('monitoring_requirement', 'REFERENT'), ('limit', 'REFERENT'), ('limit_set_schedule', 'REFERENT'), ('parameter', 'REFERENT'), ('fy2025_dmr_present', 'TEXT'), ('has_dmr_comment', 'TEXT')], mode='PURPOSE', description='Permit monitoring obligations subject to applicability evaluation.')
    numeric_pair_rows: list[dict] = []
    no_result_rows: list[dict] = []
    obligation_rows: list[dict] = []
    dmr_by_report = {_text(row.get('DMR_FORM_VALUE_ID')): row for row in fy_dmr_rows}
    for report_id in sorted(fy_report_ids):
        row = dmr_by_report[report_id]
        dmr_num = _text(row.get('DMR_VALUE_NMBR'))
        lim_num = _text(row.get('LIMIT_VALUE_NMBR'))
        nodi = _text(row.get('NODI_CODE'))
        designator = _text(row.get('LIMIT_SET_DESIGNATOR'))
        optional_flag = _text(row.get('OPTIONAL_MONITORING_FLAG'))
        if dmr_num and lim_num:
            numeric_pair_rows.append({'dmr_report': ref_dmr_report[report_id], 'limit_value': ref_limit_value[_text(row.get('LIMIT_VALUE_ID'))], 'dmr_value_nmbr': dmr_num, 'limit_value_nmbr': lim_num, 'limit_value_qualifier_code': _text(row.get('LIMIT_VALUE_QUALIFIER_CODE')), 'dmr_value_qualifier_code': _text(row.get('DMR_VALUE_QUALIFIER_CODE')), 'limit_set_designator': designator, 'optional_monitoring_flag': optional_flag, 'nodi_code': nodi})
        if not dmr_num:
            no_result_rows.append({'dmr_report': ref_dmr_report[report_id], 'limit': ref_limit[_text(row.get('LIMIT_ID'))], 'parameter': ref_parameter[_text(row.get('PARAMETER_CODE'))], 'monitoring_period_end_date': parse_date(row.get('MONITORING_PERIOD_END_DATE')) or _text(row.get('MONITORING_PERIOD_END_DATE')), 'dmr_value_nmbr': dmr_num, 'limit_value_nmbr': lim_num, 'nodi_code': nodi, 'optional_monitoring_flag': optional_flag, 'limit_set_designator': designator})
    for req in permit_requirement_rows:
        obligation_rows.append({'monitoring_requirement': req['monitoring_requirement'], 'limit': req['limit'], 'limit_set_schedule': req['limit_set_schedule'], 'parameter': req['parameter'], 'fy2025_dmr_present': next((row['fy2025_dmr_present'] for row in requirement_evidence_rows if row['monitoring_requirement'] == req['monitoring_requirement'])), 'has_dmr_comment': req['has_dmr_comment']})
    world.map('numeric_comparison_pair', numeric_pair_rows)
    world.map('no_numeric_result_case', no_result_rows)
    world.map('monitoring_obligation_subject', obligation_rows)
    purpose.require_materializable('fy2025_reported_measurements', relation='fy2025_dmr_measurement', purpose='A')
    purpose.require_materializable('dmr_permit_links', relation='dmr_permit_link', purpose='A')
    purpose.require_materializable('numeric_comparison_pairs', relation='numeric_comparison_pair', purpose='A')
    purpose.require_interpreted('interpret_limit_type_code', relation='limit_type_code', field='limit_type_code', known=[''], purpose='A', per='limit')
    purpose.require_interpreted('interpret_limit_value_qualifier', relation='limit_value_qualifier_code', field='qualifier_code', known=[''], purpose='A', per='limit_value')
    purpose.require_interpreted('interpret_optional_monitoring_for_limits', relation='optional_monitoring_flag', field='optional_monitoring_flag', known=[''], purpose='A', per='limit')
    purpose.require_interpreted('interpret_measurement_qualifier', relation='measurement_qualifier_code', field='dmr_value_qualifier_code', known=[''], purpose='A', per='dmr_report')
    purpose.require_interpreted('interpret_nodi_for_limit_applicability', relation='measurement_nodi_code', field='nodi_code', known=[''], purpose='A', per='dmr_report')
    purpose.require_numeric('numeric_limit_for_comparison', relation='numeric_comparison_pair', field='limit_value_nmbr', purpose='A', per='dmr_report')
    purpose.require_numeric('numeric_measurement_for_comparison', relation='numeric_comparison_pair', field='dmr_value_nmbr', purpose='A', per='dmr_report')
    for row in fy_dmr_rows:
        report_id = _text(row.get('DMR_FORM_VALUE_ID'))
        lim_num = _text(row.get('LIMIT_VALUE_NMBR'))
        dmr_num = _text(row.get('DMR_VALUE_NMBR'))
        nodi = _text(row.get('NODI_CODE'))
        qualifier = _text(row.get('LIMIT_VALUE_QUALIFIER_CODE'))
        designator = _text(row.get('LIMIT_SET_DESIGNATOR'))
        if dmr_num and (not lim_num):
            purpose.unresolved('reported_value_without_numeric_limit', subject={'dmr_report': ref_dmr_report[report_id]}, relation='dmr_measurement', reason='Reported measurement has numeric value but paired limit value number is absent.', purpose='A', grounding={'limit_set_designator': designator, 'parameter_code': _text(row.get('PARAMETER_CODE'))})
        if lim_num and (not dmr_num) and (not nodi):
            purpose.unresolved('numeric_limit_without_reported_value_or_nodi', subject={'dmr_report': ref_dmr_report[report_id]}, relation='dmr_measurement', reason='Numeric limit present but measurement value and NODI are both absent.', purpose='A', grounding={'parameter_code': _text(row.get('PARAMETER_CODE'))})
        if lim_num and qualifier == '':
            purpose.unresolved('numeric_limit_without_qualifier', subject={'dmr_report': ref_dmr_report[report_id]}, relation='limit_value_qualifier_code', reason='Limit value number present without comparison qualifier code.', purpose='A')
    purpose.require_materializable('permit_monitoring_requirements', relation='permit_monitoring_requirement', purpose='B')
    purpose.require_materializable('monitoring_obligation_subjects', relation='monitoring_obligation_subject', purpose='B')
    purpose.require_interpreted('interpret_monitoring_frequency_code', relation='monitoring_schedule', field='limit_freq_of_analysis_code', known=[''], purpose='B', per='limit_set_schedule')
    purpose.require_interpreted('interpret_seasonal_month_flag', relation='seasonal_month_flag', field='active_flag', known=[''], purpose='B', per=['limit_set_schedule', 'month'])
    purpose.require_interpreted('interpret_permit_dmr_comment', relation='permit_limit_comment', field='dmr_comment_text', known=[''], purpose='B', per='limit_set_schedule')
    purpose.require_interpreted('interpret_optional_monitoring_for_obligations', relation='optional_monitoring_flag', field='optional_monitoring_flag', known=[''], purpose='B', per='limit')
    schedule_by_limit: dict[str, list[str]] = {}
    for row in permit_rows:
        limit_id = _text(row.get('LIMIT_ID'))
        schedule_id = _text(row.get('LIMIT_SET_SCHEDULE_ID'))
        schedule_by_limit.setdefault(limit_id, [])
        if schedule_id not in schedule_by_limit[limit_id]:
            schedule_by_limit[limit_id].append(schedule_id)
    for limit_id, schedules in schedule_by_limit.items():
        if len(schedules) > 1:
            dmr_schedules = {_text(row.get('LIMIT_SET_SCHEDULE_ID')) for row in fy_dmr_rows if _text(row.get('LIMIT_ID')) == limit_id}
            if len(dmr_schedules) <= 1:
                purpose.unresolved('multiple_permit_schedules_for_limit', subject={'limit': ref_limit[limit_id]}, relation='monitoring_schedule', reason='Permit exposes multiple schedule ids for the same limit; FY2025 DMR does not disambiguate.', purpose='B', grounding={'schedule_ids': schedules, 'dmr_schedule_ids': sorted(dmr_schedules)})
    for req in permit_requirement_rows:
        if req['has_dmr_comment'] == 'yes':
            purpose.unresolved('conditional_permit_comment_present', subject={'monitoring_requirement': req['monitoring_requirement']}, relation='permit_limit_comment', reason='Permit schedule carries DMR comment text that may condition monitoring applicability.', purpose='B')
    purpose.require_materializable('no_numeric_result_cases', relation='no_numeric_result_case', purpose='C')
    purpose.require_interpreted('interpret_nodi_semantics', relation='measurement_nodi_code', field='nodi_code', known=[''], purpose='C', per='dmr_report')
    purpose.require_interpreted('interpret_optional_monitoring_for_no_result', relation='optional_monitoring_flag', field='optional_monitoring_flag', known=[''], purpose='C', per='limit')
    for row in no_result_rows:
        report_ref = row['dmr_report']
        nodi = row['nodi_code']
        if nodi:
            purpose.unresolved('nodi_without_interpretation', subject={'dmr_report': report_ref}, relation='measurement_nodi_code', reason='No numeric result accompanied by NODI code pending semantic interpretation.', purpose='C', grounding={'nodi_code': nodi})
        elif row['limit_value_nmbr'] and (not row['dmr_value_nmbr']):
            purpose.unresolved('missing_measurement_for_numeric_limit', subject={'dmr_report': report_ref}, relation='no_numeric_result_case', reason='Numeric limit exists but reported measurement value is absent without NODI.', purpose='C')
    for req in permit_requirement_rows:
        evidence = next((row for row in requirement_evidence_rows if row['monitoring_requirement'] == req['monitoring_requirement']))
        if evidence['fy2025_dmr_present'] == 'no':
            purpose.unresolved('permit_requirement_without_fy2025_dmr', subject={'monitoring_requirement': req['monitoring_requirement']}, relation='requirement_fy2025_dmr_evidence', reason='Permit monitoring requirement has no FY2025 DMR evidence row.', purpose='B,C', grounding={'parameter': req['parameter'], 'limit': req['limit']})

def main() -> None:
    source = Source('sources')
    world = World()
    purpose = world.purpose()
    construct(source, world, purpose)
if __name__ == '__main__':
    main()
