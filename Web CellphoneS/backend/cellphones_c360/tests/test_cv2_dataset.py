"""Validate the CSV scenario from CV2-02 without requiring a Frappe site."""
import csv
import sys
import unittest
from pathlib import Path

backend = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend))
from cellphones_c360.cv2_utils import decide_match, validate_identity


class DemoCsvTests(unittest.TestCase):
    def test_expected_sequential_decisions_on_empty_site(self):
        csv_file = backend.parents[1] / 'Docs' / 'CV2-01-05' / 'demo_customers_multichannel.csv'
        self.assertTrue(csv_file.is_file(), csv_file)
        expected = ['new', 'linked', 'new', 'linked', 'new', 'new', 'linked',
                    'review', 'review', 'rejected', 'new', 'linked']
        customers = []
        actions = []
        with csv_file.open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                try:
                    identity = validate_identity(row['customer_name'], row['phone_number'], row['email'])
                except ValueError:
                    actions.append('rejected')
                    continue
                action, _, _ = decide_match(identity, customers)
                actions.append(action)
                if action == 'new':
                    customers.append({'name': f'CUST-{len(customers)+1:05d}', **identity})
        self.assertEqual(actions, expected)
        self.assertEqual(len(customers), 5)


if __name__ == '__main__':
    unittest.main()
