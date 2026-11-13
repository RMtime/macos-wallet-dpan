"""Self-contained tests using synthetic Wallet metadata only."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wallet_dpan import WalletError, read_cards, _suffix, main


class WalletTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "passes23.sqlite"
        self.cards_dir = self.root / "Cards"
        self.cards_dir.mkdir()
        con = sqlite3.connect(self.db)
        con.executescript("""
            CREATE TABLE pass (pid INTEGER PRIMARY KEY, primary_account_suffix TEXT);
            CREATE TABLE payment_application (
                pass_pid INTEGER, fpan_suffix TEXT, dpan_suffix TEXT
            );
            INSERT INTO pass VALUES (1, '1234'), (2, '3456'), (3, '8888');
            INSERT INTO payment_application VALUES (1, NULL, '6789'), (2, NULL, NULL);
        """)
        con.commit()
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_suffix_validation(self):
        self.assertEqual(_suffix("1234"), "1234")
        self.assertIsNone(_suffix("4111111111111111"))
        self.assertIsNone(_suffix(b"1234"))

    def test_link_by_pass_pid_even_if_fpan_null(self):
        cards = read_cards(self.db, self.cards_dir)
        self.assertEqual(len(cards), 3)
        self.assertEqual(cards[0].dpan_suffix, "6789")
        self.assertIsNone(cards[1].dpan_suffix)
        self.assertIsNone(cards[2].dpan_suffix)

    def test_missing_db(self):
        with self.assertRaises(WalletError):
            read_cards(self.root / "missing.sqlite", self.cards_dir)

    def test_noninteractive_list(self):
        self.assertEqual(main(["--db", str(self.db), "--cards-dir",
                               str(self.cards_dir), "--list"]), 0)


if __name__ == "__main__":
    unittest.main()
