"""CellphoneS demo-v2 importer for native Frappe CRM.
Preflight reads only; trial exercises workflow and rolls back database writes.
Only newly inserted synthetic records receive historical timestamp mapping.
"""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import frappe
from frappe.utils import get_datetime, now_datetime
from cellphones_c360.api import intake
from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import (
    normalize_phone, normalize_email, normalize_source,
)
from cellphones_c360.cellphones_customer_360.doctype.c360_source_record.c360_source_record import source_key

FILES = ('customers.csv', 'intakes.csv', 'leads.csv', 'deals.csv', 'orders.csv',
         'order_items.csv', 'tickets.csv', 'registration_requests.csv')
STATUSES = {'new': 'Created', 'linked': 'Linked', 'review': 'Needs Review', 'rejected': 'Invalid'}


def load_data(folder):
    root = Path(folder)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8-sig'))
    if manifest['snapshot_id'] != 'cellphones-c360-demo-v2' or manifest['data_type'] != 'synthetic_demo':
        raise ValueError('Expected synthetic demo-v2')
    if tuple(manifest['import_order']) != FILES:
        raise ValueError('Unexpected manifest import order')
    data = {}
    for filename in FILES:
        raw = (root / filename).read_bytes()
        entry = manifest['files'][filename]
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('Checksum mismatch: ' + filename)
        with (root / filename).open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f, strict=True))
        keys = [r.get('snapshot_id') for r in rows]
        if len(rows) != entry['record_count'] or not all(keys) or len(keys) != len(set(keys)):
            raise ValueError('Invalid count or snapshot ID: ' + filename)
        data[filename] = rows
    for filename, entry in manifest.get('supplemental_files', {}).items():
        if hashlib.sha256((root / filename).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Supplemental checksum mismatch: ' + filename)
    return data


def preflight(folder='/tmp/c360-demo-v2'):
    if frappe.session.user != 'Administrator':
        frappe.throw('Run preflight as Administrator', frappe.PermissionError)
    data = load_data(folder)
    index = {f: {r['snapshot_id']: r for r in rows} for f, rows in data.items()}
    issues = defaultdict(list)
    def issue(kind, identifier, detail):
        issues[kind].append({'id': identifier, 'detail': detail})
    def options(dt, field):
        f = frappe.get_meta(dt).get_field(field)
        return set((f.options or '').splitlines()) if f else set()
    def select_check(filename, dt, field):
        allowed = options(dt, field)
        for value in sorted({r[field] for r in data[filename]} - allowed):
            issue('select_values', filename, field + '=' + value)

    for f in ('intakes.csv','leads.csv','deals.csv','orders.csv','tickets.csv'):
        for r in data[f]:
            cid = r.get('customer_snapshot_id')
            if (cid and cid not in index['customers.csv']) or (not cid and f != 'intakes.csv'):
                issue('relationships', r['snapshot_id'], 'Missing customer reference')
            candidate = r.get('candidate_customer_snapshot_id')
            if candidate and candidate not in index['customers.csv']:
                issue('relationships', r['snapshot_id'], 'Unknown candidate reference')
    for r in data['deals.csv']:
        lead = index['leads.csv'].get(r['lead_snapshot_id'])
        if not lead or lead['customer_snapshot_id'] != r['customer_snapshot_id']:
            issue('relationships', r['snapshot_id'], 'Deal/Lead customer mismatch')
    for r in data['tickets.csv']:
        if r['order_snapshot_id']:
            order = index['orders.csv'].get(r['order_snapshot_id'])
            if not order or order['customer_snapshot_id'] != r['customer_snapshot_id']:
                issue('relationships', r['snapshot_id'], 'Ticket/Order customer mismatch')
    # Report historical data conflicts before any insertion.
    for r in data['tickets.csv']:
        sid = r['snapshot_id']
        order = index['orders.csv'].get(r['order_snapshot_id'])
        target = r['ticket_status']
        try:
            created = get_datetime(r['created_date']) if r['created_date'] else None
            resolved = get_datetime(r['resolved_date']) if r['resolved_date'] else None
            if not created or created > now_datetime():
                issue('ticket_dates', sid, 'Missing or future created_date')
            if resolved and (not created or resolved < created or resolved > now_datetime()):
                issue('ticket_dates', sid, 'Resolved date is outside created_date to now')
            if target in ('Resolved', 'Closed'):
                if not (r['resolution'] or '').strip() or not resolved:
                    issue('ticket_resolution', sid, 'Resolved/Closed requires source resolution and resolved_date')
            elif resolved:
                issue('ticket_dates', sid, 'Non-resolved ticket has resolved_date')
            if r['ticket_type'] in ('Warranty', 'Return', 'Exchange'):
                if not order or order['order_status'] != 'Completed':
                    issue('ticket_purchase', sid, 'Requires a linked completed order')
                elif created and created < get_datetime(order['order_date']):
                    issue('ticket_purchase', sid, 'Ticket predates source order_date')
        except (ValueError, TypeError, OverflowError) as exc:
            issue('ticket_dates', sid, str(exc))
    if any(r['ticket_status'] in ('In Progress', 'Resolved', 'Closed') for r in data['tickets.csv']):
        user = frappe.db.get_value('User', 'Administrator', ('enabled', 'user_type'), as_dict=True)
        if not user or not user.enabled or user.user_type != 'System User' or not frappe.has_permission(
            'Customer Support Ticket', 'write', user='Administrator'
        ):
            issue('ticket_assignee', 'Administrator', 'Demo assignee must be an active System User with ticket write permission')
    totals = defaultdict(Decimal)
    for r in data['order_items.csv']:
        qty, price, amount = map(Decimal, (r['quantity'], r['unit_price'], r['amount']))
        if r['order_snapshot_id'] not in index['orders.csv'] or qty < 1 or qty != qty.to_integral_value() or price < 0 or qty * price != amount:
            issue('order_items', r['snapshot_id'], 'Invalid item amount, quantity or order reference')
        totals[r['order_snapshot_id']] += amount
    for r in data['orders.csv']:
        if r['snapshot_id'] not in totals or totals[r['snapshot_id']] != Decimal(r['total_amount']):
            issue('order_totals', r['snapshot_id'], 'Order total mismatch')
    for args in [('customers.csv','C360 Customer','customer_type'),('customers.csv','C360 Customer','customer_status'),('customers.csv','C360 Customer','source_channel'),('orders.csv','Customer Order','order_status'),('orders.csv','Customer Order','sales_channel'),('tickets.csv','Customer Support Ticket','ticket_type'),('tickets.csv','Customer Support Ticket','priority'),('tickets.csv','Customer Support Ticket','ticket_status'),('registration_requests.csv','C360 Registration Request','department'),('registration_requests.csv','C360 Registration Request','status')]:
        select_check(*args)
    for filename, dt in [('leads.csv','CRM Lead Status'),('deals.csv','CRM Deal Status')]:
        for value in sorted({r['status'] for r in data[filename]}):
            if not frappe.db.exists(dt, value):
                issue('missing_crm_status', filename, value)
    for filename in ('leads.csv','deals.csv'):
        for value in sorted({r['lost_reason'] for r in data[filename] if r['lost_reason']}):
            if not frappe.db.exists('CRM Lost Reason', value):
                issue('missing_lost_reason', filename, value)
    for r in data['registration_requests.csv']:
        if r['status'] not in ('Pending','Rejected'):
            issue('registration', r['snapshot_id'], 'Would require an approval workflow')
        if frappe.db.exists('User', r['email']) or frappe.db.exists('C360 Registration Request', {'email': r['email']}):
            issue('registration_collision', r['snapshot_id'], 'Existing user or registration email')

    # Approximate current intake behavior in memory, without calling process_records.
    existing = frappe.get_all('C360 Customer', fields=['name','customer_name','phone_number','email','merged_into'], limit_page_length=0)
    pool = [dict(r, origin='existing') for r in existing if not r.get('merged_into')]
    counts = Counter()
    expected_counts = Counter()
    mapped = {}
    seen = set()
    channels = options('C360 Customer','source_channel')
    for r in data['intakes.csv']:
        sid = r['snapshot_id']
        cid = r.get('customer_snapshot_id')
        expected = STATUSES.get(r['expected_action'], 'Unknown')
        expected_counts[expected] += 1
        ch = normalize_source(r['source_channel'])
        ref = r['source_reference'].strip()
        key = source_key(ch, ref)
        if key in seen or frappe.db.exists('C360 Source Record', key):
            issue('source_collision', sid, 'Source key already present in file or site')
        seen.add(key)
        matches = []
        selected = None
        try:
            if ch not in channels or not ref:
                raise ValueError('Invalid source')
            base = index['customers.csv'].get(cid, {})
            row = dict(r, customer_type=base.get('customer_type', 'Individual'), purchase_interest=0)
            norm = intake._normalize(row)
            phone, email, name = norm['phone_number'], norm['email'], norm['customer_name']
            matches = [p for p in pool if (phone and p.get('phone_number') == phone) or (email and p.get('email') == email)]
            if len(matches) == 1 and phone and email and matches[0].get('phone_number') == phone and matches[0].get('email') == email and (matches[0].get('customer_name') or '').casefold() == name.casefold():
                status = 'Linked'
                selected = matches[0]
            elif matches:
                status = 'Needs Review'
            else:
                status = 'Created'
                selected = dict(name='SIM:' + sid, customer_name=name, phone_number=phone, email=email, origin='snapshot', snapshot_customer=cid)
                pool.append(selected)
        except (frappe.ValidationError, ValueError):
            frappe.clear_last_message()
            status = 'Invalid'
        counts[status] += 1
        if status != expected:
            issue('intake_decision_diff', sid, 'Expected ' + expected + '; current prediction ' + status)
        if any(p['origin'] == 'existing' for p in matches):
            issue('existing_identity_overlap', sid, 'Matches an existing active customer')
        if cid and selected:
            if selected.get('snapshot_customer') != cid or (cid in mapped and mapped[cid]['name'] != selected['name']):
                issue('customer_mapping', sid, 'Customer reference does not match predicted identity')
            else:
                mapped[cid] = selected
        if cid and not selected:
            issue('customer_mapping', sid, 'No linked customer for reference')
        candidate = r.get('candidate_customer_snapshot_id')
        if candidate and not any(p.get('snapshot_customer') == candidate for p in matches):
            issue('review_candidate_diff', sid, 'Expected candidate not found by current identity matching')
    for cid, r in index['customers.csv'].items():
        p = mapped.get(cid)
        if not p:
            issue('customer_mapping', cid, 'Customer not mapped from source records')
            continue
        try:
            if (normalize_phone(r['phone_number']) != p['phone_number'] or normalize_email(r['email']) != p['email'] or ' '.join(r['customer_name'].split()).casefold() != p['customer_name'].casefold()):
                issue('customer_mapping', cid, 'Normalized master identity differs')
        except frappe.ValidationError:
            frappe.clear_last_message()
            issue('customer_mapping', cid, 'Master identity invalid under current rules')
    currency = frappe.db.get_single_value('FCRM Settings','currency') or '(unset)'
    if currency != 'VND':
        issue('currency', 'FCRM Settings', 'Configure VND before importing')
    missing_sources = sorted({r['source'] for r in data['leads.csv'] if r['source'] and not frappe.db.exists('CRM Lead Source', r['source'])})
    return {
        'mode': 'read_only_preflight', 'writes': 0,
        'counts': {f: len(rows) for f, rows in data.items()},
        'existing_active_customers': sum(p['origin'] == 'existing' for p in pool),
        'intake_expected': dict(expected_counts), 'intake_predicted': dict(counts),
        'mapped_customer_count': len(mapped), 'currency': currency,
        'missing_lead_sources': missing_sources,
        'order_status_counts': dict(Counter(r['order_status'] for r in data['orders.csv'])),
        'ticket_status_counts': dict(Counter(r['ticket_status'] for r in data['tickets.csv'])),
        'issue_counts': {k: len(v) for k,v in issues.items()},
        'issue_examples': {k: v[:12] for k,v in issues.items()},
        'note': 'Prediction only; no inserts, no workflow transitions, no import. Actual hooks still need testing.'
    }


# Phase 2: use existing native document validators and C360 association APIs.
# No schema changes, status-validation bypass, or new users.
# Historical timestamp mapping is restricted to newly created synthetic documents.
ACK = 'IMPORT_SYNTHETIC_DEMO_V2'


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _insert(doctype, fields):
    return frappe.get_doc({'doctype': doctype, **fields}).insert()


def _check_fields(doc, expected):
    for key, value in expected.items():
        _require((doc.get(key) or '') == (value or ''),
                 f'{doc.doctype} {doc.name}: {key} differs from snapshot')


def _perform(data):
    from cellphones_c360.api import crm_links
    from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import (
        find_identity_matches, lock_customer_identity_writes,
    )
    master = {r['snapshot_id']: r for r in data['customers.csv']}
    maps = {k: {} for k in ('customer', 'source', 'lead', 'deal', 'order', 'ticket', 'registration')}
    totals = Counter()
    states = Counter()
    lock_customer_identity_writes()
    for r in data['intakes.csv']:
        sid, cid = r['snapshot_id'], r['customer_snapshot_id']
        channel = normalize_source(r['source_channel'])
        reference = r['source_reference'].strip()
        row = {k: r[k] for k in ('customer_name', 'phone_number', 'email', 'received_at')}
        row.update(source_channel=channel, source_record_id=reference,
                   customer_type=master.get(cid, {}).get('customer_type', 'Individual'),
                   purchase_interest=0)
        # One record at a time keeps snapshot ordering and uses the public workflow.
        result = intake.process_records([row])['items'][0]
        expected = STATUSES[r['expected_action']]
        _require(not result.get('replay') and result['status'] == expected,
                 f'Intake {sid}: expected {expected}; got {result["status"]}')
        name = result.get('source_document')
        _require(name and name == source_key(channel, reference), f'Intake {sid}: no matching source document')
        maps['source'][sid] = name
        customer = result.get('customer')
        if expected == 'Created':
            _require(cid and cid not in maps['customer'] and customer, f'Intake {sid}: invalid new customer mapping')
            maps['customer'][cid] = customer
        elif expected == 'Linked':
            _require(cid and maps['customer'].get(cid) == customer, f'Intake {sid}: wrong customer association')
        else:
            _require(not customer, f'Intake {sid}: unresolved record unexpectedly linked')
        if r.get('candidate_customer_snapshot_id'):
            norm = intake._normalize(row)
            candidates = find_identity_matches(norm['phone_number'], norm['email'])
            _require(maps['customer'].get(r['candidate_customer_snapshot_id']) in {m.name for m in candidates},
                     f'Intake {sid}: expected review candidate missing')
        states[expected] += 1
    _require(set(maps['customer']) == set(master), 'Not all customer identities were created')
    _require(len(set(maps['customer'].values())) == len(master), 'Customer mapping is not one-to-one')
    for sid, r in master.items():
        doc = frappe.get_doc('C360 Customer', maps['customer'][sid])
        _require(normalize_phone(doc.phone_number) == normalize_phone(r['phone_number']) and
                 normalize_email(doc.email) == normalize_email(r['email']) and
                 ' '.join(doc.customer_name.split()).casefold() == ' '.join(r['customer_name'].split()).casefold(),
                 f'Customer {sid}: identity differs')
        doc.update({k: r[k] for k in ('customer_type', 'customer_status', 'source_channel')})
        doc.save()
    totals['customers.csv'] = len(maps['customer'])
    totals['intakes.csv'] = len(maps['source'])

    for r in data['leads.csv']:
        sid = r['snapshot_id']
        words = r['lead_name'].strip().split()
        _require(bool(words), f'Lead {sid}: missing name')
        values = {'first_name': ' '.join(words[:-1]) or words[0],
                  'last_name': words[-1] if len(words) > 1 else '',
                  'mobile_no': r['mobile_no'], 'email': r['email'],
                  'status': r['status'], 'source': r['source'] or None,
                  'converted': int(r['status'] == 'Converted'),
                  'custom_consultation_notes': r['consultation_notes'],
                  'lost_reason': r['lost_reason'] or None, 'lost_notes': r['lost_notes']}
        # Direct native insert + existing association, preserving historical demo status.
        doc = _insert('CRM Lead', values)
        _check_fields(doc, {'status': r['status'], 'source': r['source']})
        crm_links.link_record(maps['customer'][r['customer_snapshot_id']], 'CRM Lead', doc.name)
        maps['lead'][sid] = doc.name
    totals['leads.csv'] = len(maps['lead'])

    for r in data['deals.csv']:
        sid = r['snapshot_id']
        lead = frappe.get_doc('CRM Lead', maps['lead'][r['lead_snapshot_id']])
        _require(r['currency'] == 'VND', f'Deal {sid}: expected VND')
        values = {'lead': lead.name, 'first_name': lead.first_name, 'last_name': lead.last_name,
                  'email': lead.email, 'mobile_no': lead.mobile_no, 'source': lead.source,
                  'status': r['status'], 'expected_deal_value': float(Decimal(r['expected_deal_value'])),
                  'currency': r['currency'], 'expected_closure_date': r['expected_closure_date'] or None,
                  'lost_reason': r['lost_reason'] or None, 'lost_notes': r['lost_notes']}
        # Current CRM Deal has no deal_name field. Do not add one or invent a Contact.
        doc = _insert('CRM Deal', values)
        _check_fields(doc, {'status': r['status'], 'lead': lead.name, 'currency': 'VND'})
        _require(Decimal(str(doc.expected_deal_value or 0)) == Decimal(r['expected_deal_value']),
                 f'Deal {sid}: expected value changed')
        crm_links.link_record(maps['customer'][r['customer_snapshot_id']], 'CRM Deal', doc.name)
        maps['deal'][sid] = doc.name
    totals['deals.csv'] = len(maps['deal'])

    items = defaultdict(list)
    for r in data['order_items.csv']:
        items[r['order_snapshot_id']].append({'product_code': r['product_code'],
            'product_name': r['product_name'], 'quantity': int(Decimal(r['quantity'])),
            'unit_price': float(Decimal(r['unit_price']))})
    for r in data['orders.csv']:
        sid, target = r['snapshot_id'], r['order_status']
        doc = _insert('Customer Order', {'customer': maps['customer'][r['customer_snapshot_id']],
                     'order_date': r['order_date'], 'sales_channel': r['sales_channel'],
                     'order_status': 'Draft', 'items': items[sid]})
        if target == 'Cancelled':
            doc.order_status = 'Cancelled'
            doc.save()
        elif target in ('Confirmed', 'Processing', 'Completed'):
            # Explicit synthetic workflow defaults, not supplied by Khai's CSV.
            doc.payment_method = 'Direct'
            doc.fulfillment_method = 'Pickup' if r['sales_channel'] == 'Store' else 'Delivery'
            doc.order_status = 'Confirmed'
            doc.save()
            if target in ('Processing', 'Completed'):
                doc.order_status = 'Processing'
                doc.save()
            if target == 'Completed':
                doc.fulfillment_status = 'Picked Up' if doc.fulfillment_method == 'Pickup' else 'Delivered'
                # No claim that payment was actually made; retain existing payment default.
                doc.order_status = 'Completed'
                doc.save()
                # Workflow stamps completion with NOW. For this synthetic historical
                # dataset only, use order_date as an explicit proxy (midnight).
                # The source contains no actual completed_at. Do not change old rows.
                frappe.db.set_value('Customer Order', doc.name, 'completed_at',
                                    get_datetime(r['order_date']), update_modified=False)
        doc.reload()
        _require(doc.order_status == target, f'Order {sid}: wrong final status')
        _require(Decimal(str(doc.total_amount)) == Decimal(r['total_amount']), f'Order {sid}: total differs')
        maps['order'][sid] = doc.name
    totals['orders.csv'] = len(maps['order'])
    totals['order_items.csv'] = sum(len(frappe.get_doc('Customer Order', n).items) for n in maps['order'].values())

    for r in data['tickets.csv']:
        sid = r['snapshot_id']
        target = r['ticket_status']
        values = {k: r[k] or None for k in ('subject', 'ticket_type', 'priority',
                    'created_date', 'description')}
        values.update(customer=maps['customer'][r['customer_snapshot_id']],
                      related_order=maps['order'].get(r['order_snapshot_id']),
                      ticket_status='Open')
        try:
            doc = _insert('Customer Support Ticket', values)
            if target == 'Pending':
                doc.ticket_status = 'Pending'
                doc.save()
            elif target in ('In Progress', 'Resolved', 'Closed'):
                # Source lacks assigned_to. Explicit synthetic assignment to the
                # existing Administrator, not a new or real support employee.
                doc.assigned_to = 'Administrator'
                doc.ticket_status = 'In Progress'
                doc.save()
                if target in ('Resolved', 'Closed'):
                    doc.resolution = r['resolution']
                    doc.ticket_status = 'Resolved'
                    doc.save()
                    # Restore the supplied historical resolved_date only after
                    # validating the actual transition. No direct status writes.
                    historical = get_datetime(r['resolved_date'])
                    _require(get_datetime(doc.created_date) <= historical <= now_datetime(),
                             f'Ticket {sid}: invalid source resolved_date')
                    frappe.db.set_value(doc.doctype, doc.name, 'resolved_date',
                                        historical, update_modified=False)
                    doc.reload()
                    doc.validate_resolved_date()
                    if target == 'Closed':
                        doc.ticket_status = 'Closed'
                        doc.save()
            doc.reload()
            _check_fields(doc, {'ticket_status': target, 'customer': values['customer'],
                                'related_order': values['related_order']})
            if target in ('Resolved', 'Closed'):
                _require(get_datetime(doc.resolved_date) == get_datetime(r['resolved_date']),
                         f'Ticket {sid}: resolved_date differs')
            # Preserve any supplied notes even for a non-terminal ticket.
            if r['resolution'] and doc.resolution != r['resolution']:
                doc.resolution = r['resolution']
                doc.save()
            maps['ticket'][sid] = doc.name
        except Exception as exc:
            raise ValueError(f'Ticket {sid} ({target}): {exc}') from exc
    totals['tickets.csv'] = len(maps['ticket'])
    for r in data['registration_requests.csv']:
        sid = r['snapshot_id']
        _require(r['status'] in ('Pending', 'Rejected'), f'Registration {sid}: approval not allowed')
        _require(not frappe.db.exists('User', r['email']), f'Registration {sid}: user already exists')
        doc = _insert('C360 Registration Request', {k: r[k] or None for k in ('full_name', 'email', 'phone', 'department', 'status', 'reason')})
        _check_fields(doc, {'status': r['status'], 'email': r['email']})
        _require(not doc.get('provisioned_user') and not frappe.db.exists('User', r['email']), f'Registration {sid}: unexpected user creation')
        maps['registration'][sid] = doc.name
    totals['registration_requests.csv'] = len(maps['registration'])

    _require(dict(totals) == {f: len(rows) for f, rows in data.items()}, 'Imported counts differ from manifest')
    # Audit CRM relationships and statuses after all hooks have executed.
    for sid, name in maps['customer'].items():
        records = crm_links.related_records(frappe.get_doc('C360 Customer', name))
        for file, kind, dt in [('leads.csv', 'lead', 'CRM Lead'), ('deals.csv', 'deal', 'CRM Deal')]:
            expected = {maps[kind][r['snapshot_id']] for r in data[file] if r['customer_snapshot_id'] == sid}
            _require(expected == {d.name for d in records[dt]}, f'Customer {sid}: {dt} links differ')
    for file, kind, dt in [('leads.csv', 'lead', 'CRM Lead'), ('deals.csv', 'deal', 'CRM Deal')]:
        for r in data[file]:
            _require(frappe.db.get_value(dt, maps[kind][r['snapshot_id']], 'status') == r['status'],
                     f'{dt} {r["snapshot_id"]}: status changed by a hook')
    return {'counts': dict(totals), 'intake_statuses': dict(states),
            'sample_customer_ids': list(maps['customer'].items())[:3],
            'synthetic_order_defaults': {'payment_method': 'Direct', 'Store': 'Pickup', 'other_channels': 'Delivery', 'completed_at': 'order_date at midnight'},
            'synthetic_ticket_assignee': 'Administrator',
            'ticket_statuses': dict(Counter(r['ticket_status'] for r in data['tickets.csv'])),
            'limitations': ['No payment evidence supplied; payment status remains workflow default.',
                            'No explicit Deal name field in current schema; source deal_name retained in CSV.',
                            'No explicit Order-to-Deal or purchase_interest evidence supplied.',
                            'Synthetic completed_at uses order_date at midnight, not actual completion time.',
                            'Ticket assigned_to uses Administrator for In Progress/Resolved/Closed; source has no assignee.',
                            'Ticket resolved_date restored from source after workflow validation.',
                            'CRM creation and other workflow timestamps reflect import time.',
                            'No registration approval or new users requested.']}


def import_demo_v2(folder='/tmp/c360-demo-v2', dry_run=True, confirm=None, skip_incompatible_tickets=False):
    """Run in a fresh Administrator bench console on the backed-up demo site.

    Trial exercises actual validators and rolls back DB rows. It is not a read-only
    preflight, and cannot guarantee rollback of external effects or counters.
    Repeat imports are blocked by the original source/identity preflight checks.
    """
    _require(frappe.session.user == 'Administrator', 'Administrator required')
    _require(isinstance(dry_run, bool), 'dry_run must be a Python bool')
    _require(isinstance(skip_incompatible_tickets, bool), 'skip_incompatible_tickets must be a Python bool')
    _require(dry_run or confirm == (ACK + '_PARTIAL' if skip_incompatible_tickets else ACK),
             'Explicit import confirmation required (partial mode requires its own confirmation)')
    _require(hasattr(frappe.db, 'before_commit'), 'Commit guard unavailable; aborting')
    # Start with a clean transaction in a dedicated console session.
    frappe.db.rollback()
    allowed = False
    def prevent_early_commit():
        if not allowed:
            raise RuntimeError('Unexpected commit during import; aborting')
    frappe.db.before_commit.add(prevent_early_commit)
    old_mute = frappe.flags.get('mute_emails')
    frappe.flags.mute_emails = True
    try:
        from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import lock_customer_identity_writes
        lock_customer_identity_writes()
        check = preflight(folder)
        data = load_data(folder)
        original_counts = {f: len(rows) for f, rows in data.items()}
        blocking = dict(check['issue_counts'])
        skipped = []
        if skip_incompatible_tickets and blocking.get('ticket_purchase'):
            orders = {r['snapshot_id']: r for r in data['orders.csv']}
            for row in data['tickets.csv']:
                if row['ticket_type'] not in ('Warranty', 'Return', 'Exchange'):
                    continue
                order = orders.get(row['order_snapshot_id'])
                if not order or order['order_status'] != 'Completed':
                    skipped.append({
                        'id': row['snapshot_id'],
                        'ticket_type': row['ticket_type'],
                        'ticket_status': row['ticket_status'],
                        'original_order_id': row['order_snapshot_id'],
                        'original_order_status': order['order_status'] if order else None,
                        'reason': 'Requires a linked completed order',
                    })
            # Only this specific incompatibility can be excluded. Other errors,
            # including date conflicts, remain blocking even in this mode.
            if len(skipped) == blocking['ticket_purchase']:
                blocking.pop('ticket_purchase')
            else:
                _require(False, 'Additional ticket purchase issues require review')
        _require(not blocking and not check['missing_lead_sources'],
                 'Preflight not clean: ' + json.dumps(check['issue_examples'], ensure_ascii=False))
        if skipped:
            excluded_ids = {r['id'] for r in skipped}
            data['tickets.csv'] = [r for r in data['tickets.csv'] if r['snapshot_id'] not in excluded_ids]
        report = _perform(data)
        report.update(source_counts=original_counts,
                      skipped_ticket_count=len(skipped),
                      skipped_tickets=skipped,
                      complete_snapshot=(not skipped))
        if skipped:
            report['limitations'].append('Incompatible purchase-linked tickets excluded explicitly; original CSV unchanged. Ticket KPIs must be adjusted and are not identical to the full source snapshot.')
        if dry_run:
            frappe.db.rollback()
            report.update(ok=True, mode='trial_rolled_back', committed=False)
        else:
            allowed = True
            frappe.db.commit()
            report.update(ok=True, mode='import_committed', committed=True)
        return report
    except Exception:
        frappe.db.rollback()
        raise
    finally:
        frappe.flags.mute_emails = old_mute
