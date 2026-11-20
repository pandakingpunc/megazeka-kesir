"""v1.1 verisini denetler: çakışmalar, son cevaplar, başlık, okunuş satırı ve tüm ara hesaplar."""

import argparse
import re
from collections import Counter
from pathlib import Path

from denetle import zincir_dogrula
from matematik import beklenen, canonical_key, oku
from okunus_coz import coz, katla, rakam_coz

KOK = Path(__file__).resolve().parents[1]


def okunus_dogrula(satir, soru):
    soru_k = katla(soru)
    for parca in satir.removeprefix("Okunuş: ").split("; "):
        soz, rakam = parca.rsplit(" = ", 1)
        if katla(soz) not in soru_k and re.sub(r"dort$", "dord", katla(soz)) not in soru_k:
            raise ValueError(f"Okunuş soruda geçmiyor: {soz!r}")
        if coz(soz) != rakam_coz(rakam):
            raise ValueError(f"Okunuş yanlış: {soz!r} → {coz(soz)}, yazılan {rakam}")


def baslik_dogrula(baslik, tur, dogru):
    if tur == "compare":
        ifade = baslik.removeprefix("İşlem: ").replace(" ve ", "|")
        ifade = re.sub(r"(-?)(\d+) tam (\d+/\d+)", r"\1(\2+\3)", ifade)
    elif baslik.startswith(("İşlem: ", "Kesir: ")):
        ifade = baslik.split(": ", 1)[1]
        ifade = re.sub(r"(-?)(\d+) tam (\d+/\d+)", r"\1(\2+\3)", ifade)
    elif baslik == "Soru: Kesir problemi":
        return
    else:
        raise ValueError(f"Başlık tanınmadı: {baslik!r}")
    if beklenen(ifade) != dogru:
        raise ValueError(f"Başlıktaki işlem metayla uyuşmuyor: {baslik!r}")


def denetle(klasor, dislanan):
    kimlikler, sorular, yapilar = set(), set(), set()
    for yol in dislanan:
        for r in oku(yol):
            yapilar.add(canonical_key(r["meta"]["kind"], r["meta"]["expression"]))
            sorular.add(r["messages"][0]["content"])
    toplam_okunus = 0
    for bolum in ("test", "val", "train"):
        turler, hesap_sayisi, en_uzun, okunuslu = Counter(), 0, 0, 0
        for satir in oku(klasor / f"{bolum}.jsonl"):
            mesajlar, meta = satir["messages"], satir["meta"]
            kimlik, tur = meta["id"], meta["kind"]
            try:
                if [m["role"] for m in mesajlar] != ["user", "assistant"]:
                    raise ValueError("Mesaj rolleri hatalı")
                soru, yanit = mesajlar[0]["content"], mesajlar[1]["content"]
                anahtar = canonical_key(tur, meta["expression"])
                if kimlik in kimlikler or soru in sorular or anahtar in yapilar:
                    raise ValueError(f"Yinelenen kimlik/soru/işlem: {anahtar}")
                kimlikler.add(kimlik)
                sorular.add(soru)
                yapilar.add(anahtar)
                dogru = beklenen(meta["expression"])
                if dogru != meta["answer"]:
                    raise ValueError(f"Meta cevap {meta['answer']!r}, hesap {dogru!r}")
                if (dogru == "tanımsız") != (tur == "invalid"):
                    raise ValueError("Tanımsız etiketi türle uyuşmuyor")
                satirlar = yanit.splitlines()
                if satirlar[-1] != f"Sonuç: {dogru}":
                    raise ValueError("Sonuç satırı yanlış")
                if satirlar[0].startswith("Okunuş: "):
                    okunus_dogrula(satirlar[0], soru)
                    okunuslu += 1
                    satirlar = satirlar[1:]
                baslik_dogrula(satirlar[0], tur, dogru)
                hesaplar = [s.strip() for s in satirlar if s.startswith("   ")]
                if not hesaplar and tur != "invalid":
                    raise ValueError("Ara hesap eksik")
                for hesap in hesaplar:
                    zincir_dogrula(hesap)
                hesap_sayisi += len(hesaplar)
                en_uzun = max(en_uzun, len(yanit))
                turler[tur] += 1
            except (ValueError, SyntaxError, ZeroDivisionError, KeyError) as exc:
                raise ValueError(f"{bolum}/{kimlik}: {exc}\n{soru}\n{yanit}") from exc
        toplam_okunus += okunuslu
        print(f"{bolum}: {sum(turler.values())} soru, {hesap_sayisi} ara hesap, "
              f"{okunuslu} okunuşlu soru, en uzun yanıt {en_uzun} karakter")
        print("  " + ", ".join(f"{k}={v}" for k, v in sorted(turler.items())))
    print(f"Toplam {len(kimlikler)} soru; doğrulama hatası ve dışlanan kümelerle çakışma yok.")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--data", default=KOK / "data" / "v11", type=Path)
    cli.add_argument("--dislanan", type=Path, nargs="*", default=[
        KOK / "data" / "gercek.jsonl", KOK / "data" / "gercek2.jsonl", KOK / "data" / "test.jsonl"])
    opts = cli.parse_args()
    denetle(opts.data, opts.dislanan)
