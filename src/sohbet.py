"""Megazeka-Kesir'e terminalden tek tek soru sor."""

import argparse
import re

from cikarim import YAYIN_ADAPTORU, uret, yukle

KISA_ISLEM = re.compile(r"(?:[\d\s+*/×x÷:·−⁄∕.,=?!_…()\[\]<>%\-]|tam)+", re.IGNORECASE)


def sohbet_sorusu(soru):
    """Yalnız işlem yazıldığında terminalin Türkçe çözüm beklentisini modele ilet."""
    if KISA_ISLEM.fullmatch(soru) and any(harf.isdigit() for harf in soru):
        return "Türkçe olarak adım adım çöz.\n" + soru
    return soru


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", default=YAYIN_ADAPTORU, help="PEFT adaptör klasörü veya depo adı")
    parser.add_argument("--ham", action="store_true", help="Kısa işlemleri de Türkçe yönerge eklemeden gönder")
    parser.add_argument("--max-new-tokens", type=int, default=1500)
    args = parser.parse_args()
    if args.max_new_tokens <= 0:
        parser.error("Yeni token sayısı pozitif olmalı.")

    tokenizer, model = yukle(args.adapter)
    print("Kesir sorunuzu yazın. Çıkmak için q yazın.")
    while True:
        try:
            soru = input("\nSoru> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if soru.lower() in {"q", "çık", "cik", "exit"}:
            break
        if soru:
            girdi = soru if args.ham else sohbet_sorusu(soru)
            cevap, = uret(tokenizer, model, [girdi], args.max_new_tokens)
            print(cevap)


if __name__ == "__main__":
    main()
