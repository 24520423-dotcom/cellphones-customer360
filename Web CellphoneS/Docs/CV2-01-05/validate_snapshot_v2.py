"""Read-only validator for CellphoneS synthetic snapshot demo-v2.

Example:
python 'Web CellphoneS/Docs/CV2-01-05/validate_snapshot_v2.py' 'Web CellphoneS/Docs/CV2-01-05/snapshots/demo-v2'

Only stdlib; no MariaDB/Frappe connection. This does not import any data.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

RELATIONS = {
    'leads.csv': {'customer_snapshot_id': 'customers.csv'},
    'deals.csv': {'customer_snapshot_id': 'customers.csv', 'lead_snapshot_id': 'leads.csv'},
    'orders.csv': {'customer_snapshot_id': 'customers.csv'},
    'order_items.csv': {'order_snapshot_id': 'orders.csv'},
    'tickets.csv': {'customer_snapshot_id': 'customers.csv'},
    'intakes.csv': {},
    'registration_requests.csv': {},
}
CHANNELS = {'Website','App','Facebook','Zalo','Hotline','Store','Other'}
LEAD_STATES = {'Junk','Unqualified','Converted','Qualified','Nurture','Contacted','New'}
DEAL_STATES = {'Lost','Won','Ready to Close','Negotiation','Proposal/Quotation','Demo/Making','Qualification'}
ORDER_STATES = {'Draft','Confirmed','Processing','Completed','Cancelled'}
TICKET_STATES = {'Open','In Progress','Pending','Resolved','Closed'}
REQUIRED = {
    'customers.csv': ['customer_name','phone_number','email','customer_type','customer_status','source_channel'],
    'intakes.csv': ['customer_snapshot_id','candidate_customer_snapshot_id','expected_action','source_channel','source_reference','customer_name','phone_number','email','received_at'],
    'leads.csv': ['customer_snapshot_id','lead_name','mobile_no','email','status','consultation_notes','lost_reason'],
    'deals.csv': ['customer_snapshot_id','lead_snapshot_id','status','expected_deal_value','currency','lost_reason','expected_closure_date'],
    'orders.csv': ['customer_snapshot_id','order_date','sales_channel','order_status','total_amount'],
    'order_items.csv': ['order_snapshot_id','product_name','quantity','unit_price','amount'],
    'tickets.csv': ['customer_snapshot_id','order_snapshot_id','subject','ticket_type','priority','ticket_status','created_date','description','resolution','resolved_date'],
    'registration_requests.csv': ['full_name','email','phone','department','status','reason'],
}


def load_snapshot(folder):
    folder = Path(folder)
    problems = []
    mf = folder / 'manifest.json'
    if not mf.is_file():
        raise ValueError('Missing manifest.json')
    manifest = json.loads(mf.read_text(encoding='utf-8-sig'))
    if manifest.get('snapshot_id') != 'cellphones-c360-demo-v2' or manifest.get('data_type') != 'synthetic_demo':
        problems.append('Not a supported synthetic demo-v2 manifest')
    if set(manifest.get('import_order', [])) != set(REQUIRED):
        problems.append('Manifest import_order does not match required files')
    data={}
    for filename in REQUIRED:
        path = folder / filename
        if not path.is_file():
            problems.append(f'Missing {filename}')
            data[filename]=[]
            continue
        meta = manifest.get('files', {}).get(filename, {})
        if hashlib.sha256(path.read_bytes()).hexdigest() != meta.get('sha256'):
            problems.append(f'Checksum mismatch: {filename}')
        with path.open('r',encoding='utf-8-sig',newline='') as handle:
            reader=csv.DictReader(handle)
            cols = set(reader.fieldnames or [])
            missing = set(REQUIRED[filename] + ['snapshot_id']) - cols
            if missing:
                problems.append(f'Missing columns {filename}: {sorted(missing)}')
            rows=list(reader)
        if len(rows)!=meta.get('record_count'):
            problems.append(f'Row count mismatch: {filename}')
        keys=[r.get('snapshot_id','') for r in rows]
        if any(not key for key in keys) or len(set(keys))!=len(keys):
            problems.append(f'Duplicate or missing snapshot_id: {filename}')
        data[filename]=rows
    return manifest,data,problems


def validate(folder):
    manifest,data,problems=load_snapshot(folder)
    idx={file:{r['snapshot_id']:r for r in rows} for file,rows in data.items()}
    for fname, rels in RELATIONS.items():
        for r in data[fname]:
            for column, other in rels.items():
                if r.get(column) not in idx[other]:
                    problems.append(f'{fname}/{r["snapshot_id"]}: missing {column} {r.get(column)}')
    for r in data['customers.csv']:
        if not re.fullmatch(r'0[35789][0-9]{8}',r.get('phone_number','')):
            problems.append(f'Invalid customer phone: {r["snapshot_id"]}')
        if not r.get('email','').endswith('@example.test'):
            problems.append(f'Unsafe/non-demo email: {r["snapshot_id"]}')
        if r.get('customer_type') not in ('Individual','Business') or r.get('customer_status') not in ('Active','Inactive'):
            problems.append(f'Invalid Customer enum: {r["snapshot_id"]}')
        if r.get('source_channel') not in CHANNELS:
            problems.append(f'Invalid Customer channel: {r["snapshot_id"]}')
    phones=[r['phone_number'] for r in data['customers.csv']]
    emails=[r['email'] for r in data['customers.csv']]
    if len(set(phones))!=len(phones) or len(set(emails))!=len(emails):
        problems.append('Duplicate identity among base customers')
    for r in data['leads.csv']:
        if r['status'] not in LEAD_STATES:
            problems.append(f'Invalid Lead status {r["snapshot_id"]}')
        if r['status'] in ('Junk','Unqualified') and not r.get('lost_reason'):
            problems.append(f'Missing Lead lost_reason {r["snapshot_id"]}')
    for r in data['deals.csv']:
        lead=idx['leads.csv'].get(r['lead_snapshot_id'])
        if lead and lead['customer_snapshot_id'] != r['customer_snapshot_id']:
            problems.append(f'Cross-customer Deal {r["snapshot_id"]}')
        if r['status'] not in DEAL_STATES or r['currency']!='VND':
            problems.append(f'Invalid Deal status/currency: {r["snapshot_id"]}')
        if r['status']=='Lost' and not r.get('lost_reason'):
            problems.append(f'Missing Deal lost_reason: {r["snapshot_id"]}')
        if not r.get('expected_closure_date'):
            problems.append(f'Missing Deal expected closure date: {r["snapshot_id"]}')
        try:
            if Decimal(r['expected_deal_value']) < 0: raise ValueError()
        except (InvalidOperation, ValueError):
            problems.append(f'Invalid Deal amount {r["snapshot_id"]}')
    order_items_by_order={}
    for r in data['order_items.csv']:
        try:
            qty=int(r['quantity']); price=Decimal(r['unit_price']); amt=Decimal(r['amount'])
            if qty < 1 or price < 0 or qty*price != amt: raise ValueError()
            order_items_by_order.setdefault(r['order_snapshot_id'],[]).append(amt)
        except (InvalidOperation, ValueError):
            problems.append(f'Invalid order item {r["snapshot_id"]}')
    for r in data['orders.csv']:
        if r['order_status'] not in ORDER_STATES or r['sales_channel'] not in CHANNELS:
            problems.append(f'Invalid Order status/channel: {r["snapshot_id"]}')
        try:
            if not order_items_by_order.get(r['snapshot_id']):
                raise ValueError('No order items')
            if Decimal(r['total_amount']) != sum(order_items_by_order[r['snapshot_id']]):
                raise ValueError('Order total != sum items')
        except (ValueError,InvalidOperation) as ex:
            problems.append(f'Invalid Order {r["snapshot_id"]}: {ex}')
    for r in data['tickets.csv']:
        oid=r.get('order_snapshot_id','')
        if oid:
            order=idx['orders.csv'].get(oid)
            if not order or order['customer_snapshot_id']!=r['customer_snapshot_id']:
                problems.append(f'Cross-customer Ticket {r["snapshot_id"]}')
        if r['ticket_status'] not in TICKET_STATES or r['ticket_type'] not in {'Warranty','Return','Exchange','Complaint','Technical Support','Other'} or r['priority'] not in {'Low','Medium','High','Urgent'}:
            problems.append(f'Invalid Ticket enum: {r["snapshot_id"]}')
        if r['ticket_status'] in {'Resolved','Closed'} and not r['resolution']:
            problems.append(f'Missing Ticket resolution: {r["snapshot_id"]}')
        if r['resolved_date'] and r['resolved_date'] < r['created_date']:
            problems.append(f'Resolved before created: {r["snapshot_id"]}')
    # First touchpoint must create a Customer, all followups link, uncertain rows do not auto-merge.
    first_cust=set()
    seen_sources=set()
    for r in data['intakes.csv']:
        cid=r['customer_snapshot_id']; cand=r['candidate_customer_snapshot_id']
        action=r['expected_action']
        sk=(r['source_channel'],r['source_reference'])
        if sk in seen_sources: problems.append(f'Duplicate source key {sk}')
        seen_sources.add(sk)
        if r['source_channel'] not in CHANNELS: problems.append(f'Invalid Intake channel {r["snapshot_id"]}')
        if action=='new':
            if cid not in idx['customers.csv'] or cid in first_cust: problems.append(f'Invalid initial Intake {r["snapshot_id"]}')
            first_cust.add(cid)
        elif action=='linked':
            if cid not in first_cust: problems.append(f'Linked before first Intake {r["snapshot_id"]}')
        elif action=='review':
            if cid or cand not in first_cust: problems.append(f'Invalid review Intake {r["snapshot_id"]}')
        elif action=='rejected':
            if cid or cand: problems.append(f'Rejected Intake with Customer link {r["snapshot_id"]}')
        else: problems.append(f'Unknown Intake action {r["snapshot_id"]}')
    if first_cust != set(idx['customers.csv']):
        problems.append('Some Customer missing a creation Intake')
    # Simulate the exact pure CV2 matching logic (no database access).
    # Keep this check tied to the checked-in backend's cv2_utils.py.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend' / 'cellphones_c360'))
    from cellphones_c360.cv2_utils import validate_identity, decide_match
    virtual = []
    for r in data['intakes.csv']:
        try:
            identity = validate_identity(r['customer_name'], r['phone_number'], r['email'])
            actual, candidate, _ = decide_match(identity, virtual)
        except ValueError:
            actual, candidate = 'rejected', None
        if actual != r['expected_action']:
            problems.append(f'Intake decision mismatch {r["snapshot_id"]}: expected {r["expected_action"]}, actual {actual}')
        if actual == 'new':
            virtual.append({'name': r['customer_snapshot_id'], **identity})
        elif actual == 'linked' and candidate != r['customer_snapshot_id']:
            problems.append(f'Wrong Intake linked Customer {r["snapshot_id"]}')
        elif actual == 'review' and candidate != r['candidate_customer_snapshot_id']:
            problems.append(f'Wrong Intake candidate Customer {r["snapshot_id"]}')
    for r in data['registration_requests.csv']:
        if not r['email'].endswith('@example.test') or r['status'] not in {'Pending','Rejected'} or r['department'] not in {'Sales','Customer Service','Operations','Other'}:
            problems.append(f'Unsafe/invalid registration {r["snapshot_id"]}')
    cases = {
        'intake': dict(Counter(r['expected_action'] for r in data['intakes.csv'])),
        'deal': dict(Counter(r['status'] for r in data['deals.csv'])),
        'order': dict(Counter(r['order_status'] for r in data['orders.csv'])),
        'ticket': dict(Counter(r['ticket_status'] for r in data['tickets.csv'])),
    }
    return problems, {filename:len(rows) for filename,rows in data.items()},cases

if __name__=='__main__':
    if len(sys.argv)!=2:
        print('Usage: python validate_snapshot_v2.py <folder>')
        sys.exit(2)
    try:
        errors,counts,cases=validate(Path(sys.argv[1]))
    except Exception as e:
        print('FAIL:',repr(e))
        sys.exit(1)
    print('Records:', ', '.join(f'{k}={v}' for k,v in counts.items()))
    print('Scenario coverage:',json.dumps(cases,ensure_ascii=False,sort_keys=True))
    if errors:
        print('FAIL:')
        for e in errors:print(' -',e)
        sys.exit(1)
    print('PASS: checksums, IDs, links, values, required statuses and demo privacy. Offline only; Frappe import NOT tested.')
