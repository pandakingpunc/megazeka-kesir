"""Bölümler arası eşleşmeleri, son cevapları ve yazılan tüm ara hesapları denetler."""

import argparse
import re
from collections import Counter
from pathlib import Path

from matematik import beklenen, canonical_key, oku, sayi

KOK = Path(__file__).resolve().parents[1]
ILISKI = re.compile(r"\s([<=>])\s")


def zincir_dogrula(hesap):
    parcalar = ILISKI.split(hesap)
    if len(parcalar) < 3:
        raise ValueError(f"Karşılaştırma ya da eşitlik bulunamadı: {hesap!r}")
    onceki = sayi(parcalar[0])
    for iliski, sag in zip(parcalar[1::2], parcalar[2::2]):
        sonuc = sayi(sag)
        dogru = {"=": onceki == sonuc, "<": onceki < sonuc, ">": onceki > sonuc}[iliski]
        if not dogru:
            raise ValueError(f"Yanlış ara hesap: {hesap}")
        onceki = sonuc


def denetle(klasor):
    kimlikler, sorular, yapilar = set(), set(), set()
    for bolum in ("train", "val", "test", "gercek"):
        turler, hesap_sayisi, en_uzun = Counter(), 0, 0
        for satir in oku(klasor / f"{bolum}.jsonl"):
            mesajlar, meta = satir["messages"], satir["meta"]
            kimlik, tur = meta["id"], meta["kind"]
            try:
                roller = ["user"] if bolum == "gercek" else ["user", "assistant"]
                if [m["role"] for m in mesajlar] != roller or any(not m["content"].strip() for m in mesajlar):
                    raise ValueError("Mesaj rolleri ya da içerik hatalı")
                soru = mesajlar[0]["content"]
                anahtar = canonical_key(tur, meta["expression"])
                if len({"<", "=", ">"} & {meta["answer"]}) != (tur == "compare"):
                    raise ValueError("Karşılaştırma etiketi yapıyla uyuşmuyor")
                if (meta["answer"] == "tanımsız") != (tur == "invalid"):
                    raise ValueError("Tanımsız işlem etiketi hatalı")
                if kimlik in kimlikler or soru in sorular or anahtar in yapilar:
                    raise ValueError(f"Yinelenen kimlik/soru/işlem: {anahtar}")
                kimlikler.add(kimlik)
                sorular.add(soru)
                yapilar.add(anahtar)
                dogru = beklenen(meta["expression"])
                if dogru != meta["answer"]:
                    raise ValueError(f"Meta cevap {meta['answer']!r}, hesap {dogru!r}")
                if len(mesajlar) == 2:
                    yanit = mesajlar[1]["content"]
                    satirlar = yanit.splitlines()
                    if satirlar[-1] != f"Sonuç: {dogru}":
                        raise ValueError("Sonuç satırı yanlış")
                    if tur == "compare":
                        if beklenen(satirlar[0].removeprefix("İşlem: ").replace(" ve ", "|")) != dogru:
                            raise ValueError("Başlıktaki karşılaştırma metayla uyuşmuyor")
                    elif satirlar[0].startswith(("İşlem: ", "Kesir: ")):
                        ifade = satirlar[0].split(": ", 1)[1]
                        ifade = re.sub(r"(-?)(\d+) tam (\d+/\d+)", r"\1(\2+\3)", ifade)
                        if beklenen(ifade) != dogru:
                            raise ValueError("Başlıktaki işlem metayla uyuşmuyor")
                    hesaplar = [s.strip() for s in satirlar if s.startswith("   ")]
                    if not hesaplar and tur != "invalid":
                        raise ValueError("Ara hesap eksik")
                    for hesap in hesaplar:
                        zincir_dogrula(hesap)
                    hesap_sayisi += len(hesaplar)
                    en_uzun = max(en_uzun, len(yanit))
                turler[tur] += 1
            except (ValueError, SyntaxError, ZeroDivisionError) as exc:
                raise ValueError(f"{bolum}/{kimlik}: {exc}") from exc
        print(f"{bolum}: {sum(turler.values())} soru, {hesap_sayisi} ara hesap, en uzun yanıt {en_uzun} karakter")
        print("  " + ", ".join(f"{k}={v}" for k, v in sorted(turler.items())))
    print(f"Toplam {len(yapilar)} benzersiz soru, doğrulama hatası ve bölümler arası çakışma yok.")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--data", default=KOK / "data", type=Path)
    denetle(cli.parse_args().data)

