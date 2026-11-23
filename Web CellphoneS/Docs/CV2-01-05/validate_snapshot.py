"""Offline, read-only validation of the portable demo snapshot.

Usage: python validate_snapshot.py snapshots/demo-v1
Does not connect to Frappe or import/change any database rows.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation

RELATIONS = {
    'leads.csv': {'customer_snapshot_id': 'customers.csv'},
    'deals.csv': {'customer_snapshot_id': 'customers.csv', 'lead_snapshot_id': 'leads.csv'},
    'orders.csv': {'customer_snapshot_id': 'customers.csv'},
    'order_items.csv': {'order_snapshot_id': 'orders.csv'},
    'tickets.csv': {'customer_snapshot_id': 'customers.csv', 'order_snapshot_id': 'orders.csv'},
    'intakes.csv': {'customer_snapshot_id': 'customers.csv'},
}


def validate(path: Path) -> tuple[list[str], dict[str, int]]:
    issues = []
    manifest = json.loads((path / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('data_type') != 'synthetic_demo':
        issues.append('data_type must be synthetic_demo for GitHub demo dataset')
    rows_by_file = {}
    counts = {}
    for filename in manifest['import_order']:
        f = path / filename
        if not f.is_file():
            issues.append(f'Missing: {filename}')
            continue
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if digest != manifest['files'][filename]['sha256']:
            issues.append(f'Checksum mismatch: {filename}')
        with f.open(encoding='utf-8-sig', newline='') as fh:
            reader = csv.DictReader(fh)
            if 'snapshot_id' not in (reader.fieldnames or []):
                issues.append(f'Missing snapshot_id column: {filename}')
                continue
            rows = list(reader)
        if len(rows) != manifest['files'][filename]['record_count']:
            issues.append(f'Row count mismatch: {filename}')
        ids = [r['snapshot_id'] for r in rows]
        if not all(ids) or len(set(ids)) != len(ids):
            issues.append(f'Empty or duplicate snapshot_id: {filename}')
        rows_by_file[filename] = rows
        counts[filename] = len(rows)
    idx = {key: {r['snapshot_id']: r for r in value} for key,value in rows_by_file.items()}
    for filename, relations in RELATIONS.items():
        for row in rows_by_file.get(filename, []):
            for col, target in relations.items():
                if not row.get(col):
                    issues.append(f'{filename}/{row["snapshot_id"]}: missing {col}')
                elif row[col] not in idx.get(target, {}):
                    issues.append(f'{filename}/{row["snapshot_id"]}: dangling {col}={row[col]}')
    for r in rows_by_file.get('deals.csv', []):
        lead = idx['leads.csv'].get(r['lead_snapshot_id'])
        if lead and lead['customer_snapshot_id'] != r['customer_snapshot_id']:
            issues.append(f'{r["snapshot_id"]}: Deal customer differs from Lead customer')
    for r in rows_by_file.get('tickets.csv', []):
        order = idx['orders.csv'].get(r['order_snapshot_id'])
        if order and order['customer_snapshot_id'] != r['customer_snapshot_id']:
            issues.append(f'{r["snapshot_id"]}: Ticket customer differs from Order customer')
    for order in rows_by_file.get('orders.csv', []):
        items = [r for r in rows_by_file.get('order_items.csv', []) if r['order_snapshot_id'] == order['snapshot_id']]
        try:
            total = sum((Decimal(r['amount']) for r in items), Decimal(0))
            if total != Decimal(order['total_amount']):
                issues.append(f'{order["snapshot_id"]}: total_amount differs from sum(items)')
        except (InvalidOperation, ValueError):
            issues.append(f'{order["snapshot_id"]}: invalid numeric amount')
    source_keys = [(r['source_channel'],r['source_reference']) for r in rows_by_file.get('intakes.csv', [])]
    if len(set(source_keys)) != len(source_keys):
        issues.append('Duplicate intake source_channel/source_reference')
    return issues, counts


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Validate logic snapshot demo (read only)')
    p.add_argument('folder',type=Path)
    args = p.parse_args()
    problems, summary = validate(args.folder)
    print('Records:', ', '.join(f'{k}={v}' for k,v in summary.items()))
    if problems:
        print('FAILED:')
        for issue in problems:
            print(' -',issue)
        raise SystemExit(1)
    print('PASS: file integrity and basic logical relationships verified (not Frappe import test).')
