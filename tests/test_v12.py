"""Okunuş, ayrıştırıcı ve v1.2 üreticisi için hızlı testler. Çalıştırma: python -m unittest discover tests"""

import json
import random
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import denetle_v11  # noqa: E402
import uret_v12  # noqa: E402
from okunus import ek, kesir_soz, soz, tam_sayili_soz  # noqa: E402
from okunus_coz import coz  # noqa: E402


class OkunusTesti(unittest.TestCase):
    def test_sayi_gidis_donus(self):
        for n in list(range(0, 1200)) + [1999, 2459, 10000, 123456]:
            self.assertEqual(coz(soz(n)), n)
            self.assertEqual(coz(soz(-n)), -n)

    def test_kesir_gidis_donus(self):
        rng = random.Random(0)
        for _ in range(2000):
            payda = rng.randint(2, 120)
            pay = rng.randint(-300, 300)
            for kip in ("bolu", "de"):
                if kip == "de" and not 0 < abs(pay) < payda:
                    continue
                self.assertEqual(coz(kesir_soz(pay, payda, kip)), Fraction(pay, payda))

    def test_tam_sayili(self):
        self.assertEqual(coz(tam_sayili_soz(-3, 2, 7, "de")), Fraction(-23, 7))
        self.assertEqual(coz(tam_sayili_soz(2, 1, 2, "bucuk")), Fraction(5, 2))
        self.assertEqual(coz("üç tam dörtte bir"), Fraction(13, 4))
        self.assertEqual(coz("yarım"), Fraction(1, 2))
        self.assertEqual(coz("ceyrek"), Fraction(1, 4))

    def test_hal_ekleri(self):
        self.assertEqual(ek("dört", "a"), "dörde")
        self.assertEqual(ek("dört", "i"), "dördü")
        self.assertEqual(ek("on dokuz", "a"), "on dokuza")
        self.assertEqual(ek("altı", "i"), "altıyı")
        self.assertEqual(ek("üç", "dan"), "üçten")
        self.assertEqual(ek("kırk", "de"), "kırkta")
        self.assertEqual(ek("iki", "in"), "ikinin")
        self.assertEqual(ek("beş", "le"), "beşle")


class UreticiTesti(unittest.TestCase):
    def test_ornekler_denetimden_gecer(self):
        with tempfile.TemporaryDirectory() as klasor:
            klasor = Path(klasor)
            rng = random.Random(3)
            gorulen, sorular = set(), set()
            for ad, n in (("test", 120), ("val", 60), ("train", 600)):
                veriler = uret_v12.bolum(ad, n, rng, gorulen, sorular)
                with open(klasor / f"{ad}.jsonl", "w", encoding="utf-8") as f:
                    for v in veriler:
                        f.write(json.dumps(v, ensure_ascii=False) + "\n")
            denetle_v11.denetle(klasor, [])

    def test_ayni_tohum_ayni_cikti(self):
        a = uret_v12.ornek("mixed", random.Random(7))
        b = uret_v12.ornek("mixed", random.Random(7))
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
