"""Terminalden girilen kısa işlemlerin ve sözel soruların modele aktarımı."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sohbet import sohbet_sorusu


class SohbetSorusuTesti(unittest.TestCase):
    def test_kisa_islemi_degistirmeden_turkce_cozum_ister(self):
        for soru in ("3/4+1/2", "7/12 : 14/9 = ?", "5/7 ? 7/10", "−2 tam 1/3 × 3/4"):
            with self.subTest(soru=soru):
                self.assertEqual(sohbet_sorusu(soru), "Türkçe olarak adım adım çöz.\n" + soru)

    def test_sozel_soruyu_aynen_gonderir(self):
        for soru in ("3/4 + 1/2 kaç eder?", "İngilizce açıkla. 3/4 + 1/2", "?"):
            with self.subTest(soru=soru):
                self.assertEqual(sohbet_sorusu(soru), soru)
