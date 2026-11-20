"""Taban model ve Megazeka-Kesir adaptörünü iki test kümesinde kıyasla."""

import argparse
import gc
import json
from pathlib import Path

from cikarim import KOK, MAKS_YENI_TOKEN, sorulari_oku, uret, yukle
from puanla import puanla


def tahminleri_yaz(tokenizer, model, kayitlar, yol, args, etiket):
    with yol.open("w", encoding="utf-8") as dosya:
        for baslangic in range(0, len(kayitlar), args.batch_size):
            grup = kayitlar[baslangic:baslangic + args.batch_size]
            tahminler = uret(
                tokenizer, model, [soru for _, soru in grup], args.max_new_tokens
            )
            for (kimlik, _), tahmin in zip(grup, tahminler, strict=True):
                kayit = {"id": kimlik, "prediction": tahmin}
                dosya.write(json.dumps(kayit, ensure_ascii=False) + "\n")
            dosya.flush()
            print(f"{etiket} {baslangic + len(grup)}/{len(kayitlar)}", flush=True)


def kosulu_calistir(kosul, kumeler, args):
    import torch

    print(f"[{kosul}] Model yükleniyor.", flush=True)
    tokenizer, model = yukle(args.adapter if kosul == "adapter" else None)
    try:
        for test_yolu, kayitlar in kumeler:
            kume = f"{test_yolu.parent.name}-{test_yolu.stem}" if test_yolu.parent.name != "data" else test_yolu.stem
            ad = f"{kosul}_{kume}"
            etiket = f"[{kosul}/{kume}]"
            tahmin_yolu = args.reports / f"{ad}_tahmin.jsonl"
            rapor_yolu = args.reports / f"{ad}_puan.json"
            print(f"{etiket} Çıkarım başladı.", flush=True)
            tahminleri_yaz(tokenizer, model, kayitlar, tahmin_yolu, args, etiket)
            rapor = puanla(test_yolu, tahmin_yolu)
            rapor_yolu.write_text(
                json.dumps(rapor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"{etiket} {rapor['dogru']}/{rapor['toplam']} doğru → {rapor_yolu}", flush=True)
    finally:
        del model, tokenizer
        gc.collect()
        torch.cuda.empty_cache()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", required=True, help="PEFT adaptör klasörü veya depo adı")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-new-tokens", type=int, default=MAKS_YENI_TOKEN)
    parser.add_argument("--reports", type=Path, default=KOK / "reports")
    parser.add_argument("--kosul", choices=("taban", "adapter", "ikisi"), default="ikisi")
    parser.add_argument("--kumeler", nargs="+", default=["data/test.jsonl", "data/gercek.jsonl"],
                        help="Proje köküne göre test dosyaları")
    args = parser.parse_args()
    if args.batch_size <= 0 or args.max_new_tokens <= 0:
        parser.error("Grup boyutu ve yeni token sayısı pozitif olmalı.")

    kumeler = []
    for dosya in args.kumeler:
        yol = KOK / dosya
        try:
            kayitlar = sorulari_oku(yol, limit=0)
        except (OSError, ValueError) as hata:
            parser.error(str(hata))
        if not kayitlar:
            parser.error(f"Test kümesi boş: {yol}")
        kumeler.append((yol, kayitlar))

    args.reports.mkdir(parents=True, exist_ok=True)
    kosullar = ("taban", "adapter") if args.kosul == "ikisi" else (args.kosul,)
    for kosul in kosullar:
        kosulu_calistir(kosul, kumeler, args)


if __name__ == "__main__":
    main()
