"""Offline tests of CV2 duplicate decisions (no site or database required)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cellphones_c360.cv2_utils import decide_match, normalize_email, normalize_phone, normalized_name, validate_identity


class IntakeDecisionTests(unittest.TestCase):
    def test_vietnamese_phone(self):
        self.assertEqual(normalize_phone("+84 (90) 123 4567"), "0901234567")
        self.assertEqual(normalize_phone("84901234567"), "0901234567")

    def test_name_accents_and_email(self):
        self.assertEqual(normalized_name("  Nguyễn   Văn  An "), "nguyen van an")
        self.assertEqual(normalize_email("  A@EXAMPLE.TEST "), "a@example.test")

    def test_no_email_or_phone(self):
        with self.assertRaises(ValueError):
            validate_identity("Nguyễn Văn An", "", "")

    def test_invalid_phone_and_email(self):
        for phone, email in (("0121234567", ""), ("0901234567", "abc")):
            with self.subTest(phone=phone, email=email), self.assertRaises(ValueError):
                validate_identity("Nguyễn Văn An", phone, email)

    def test_new_record(self):
        incoming = validate_identity("Nguyễn Văn An", "0901234567", "a@example.test")
        self.assertEqual(decide_match(incoming, [])[0], "new")

    def test_exact_phone_and_name_links(self):
        incoming = validate_identity("Nguyễn Văn An", "+84901234567", "a@example.test")
        rows = [{"name": "CUST-00001", "customer_name": "Nguyễn Văn An", "phone_number": "0901234567", "email": "a@example.test"}]
        self.assertEqual(decide_match(incoming, rows)[:2], ("linked", "CUST-00001"))

    def test_different_name_goes_to_review(self):
        incoming = validate_identity("Nguyễn Văn Anh", "0901234567", "")
        rows = [{"name": "CUST-00001", "customer_name": "Nguyễn Văn An", "phone_number": "0901234567", "email": "a@example.test"}]
        self.assertEqual(decide_match(incoming, rows)[0], "review")

    def test_conflicting_email_goes_to_review(self):
        incoming = validate_identity("Nguyễn Văn An", "0901234567", "other@example.test")
        rows = [{"name": "CUST-00001", "customer_name": "Nguyễn Văn An", "phone_number": "0901234567", "email": "a@example.test"}]
        self.assertEqual(decide_match(incoming, rows)[0], "review")

    def test_multiple_identity_candidates_go_to_review(self):
        incoming = validate_identity("Nguyễn Văn An", "0901234567", "a@example.test")
        rows = [
            {"name": "CUST-00001", "customer_name": "Nguyễn Văn An", "phone_number": "0901234567", "email": ""},
            {"name": "CUST-00002", "customer_name": "Nguyễn Văn An", "phone_number": "", "email": "a@example.test"},
        ]
        self.assertEqual(decide_match(incoming, rows)[0], "review")

    def test_same_email_plus_name_no_conflicting_phone(self):
        incoming = validate_identity("Nguyễn Thị Thảo", "0977777777", "thao@example.test")
        rows = [{"name": "CUST-00002", "customer_name": "Nguyễn Thị Thảo", "phone_number": "", "email": "thao@example.test"}]
        self.assertEqual(decide_match(incoming, rows)[0], "linked")


if __name__ == "__main__":
    unittest.main()
