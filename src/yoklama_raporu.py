"""Kayıtlı tahminlerde yanıt dilini ve nihai değeri CPU üzerinde ölçer."""

import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import re
import sys
import unicodedata

from matematik import GECERSIZ, beklenen, oku
from puanla import ara_hesaplar, cevap_bul, temizle

DIL_ETIKETLERI = ("turkce", "yabanci", "karisik", "belirsiz", "sozel_yanit_yok")
MATEMATIK_ETIKETLERI = ("dogru", "yanlis", "okunamadi")
SOZLUKLER = {
    "tr": re.compile(
        r"\b(?:sonu[çc](?:tur|ta)?|cevap[ıi]?|yan[ıi]t[ıi]?|i[şs]lem\w*|"
        r"kes[iı]r\w*|kesr\w*|payda\w*|pay[ıi]?|b[öo]l\w*|[çc]arp\w*|"
        r"sadele[şs]\w*|eşit\w*|eşittir|tan[ıi]ms[ıi]z\w*|"
        r"dolay[ıi]s[ıi]yla|say[ıi]\w*|topla\w*|[çc][ıi]kar\w*|"
        r"ortak|için|ile|eder|olur|önce|sonra|kalan|kaldı|litre|küçük\w*|büyük\w*)\b"
    ),
    "en": re.compile(
        r"\b(?:the|of|we|let's|therefore|thus|result|answer|equals?|undefined|"
        r"fraction\w*|numerator\w*|denominator\w*|simplif\w*|multiply\w*|"
        r"divide\w*|dividing|common|first|then|which|greater|less|than|remaining)\b"
    ),
    "de": re.compile(r"\b(?:der|den|und|ist|bruch\w*|nenner|zähler|ergebnis|antwort)\b"),
    "es": re.compile(r"\b(?:para|los|las|fracci[oó]n\w*|denominador\w*|numerador\w*|resultado|respuesta)\b"),
    "fr": re.compile(r"\b(?:les|des|est|donc|dénominateur\w*|numérateur\w*|résultat|réponse)\b"),
}
LATEX_KODU = re.compile(r"\\(?!text\s*\{)[a-zA-Z]+|\b(?:GCD|LCD|LCM|EBOB|EKOK)\b")
TURKCE_KISA = {"sonuç", "sonuc", "cevap", "yanıt", "tanımsız", "eşittir", "kaldı"}
INGILIZCE_KISA = {"answer", "result", "undefined"}
SAYI = r"[+-]?\d+(?:[.,]\d+)?"
KESIR = rf"{SAYI}(?:\s*/\s*{SAYI})?"
SON_BILDIRIM = re.compile(
    r"(?:\b(?:answer|result)\s*:?\s*(?:is\b)?|(?:结果|結果|答案)(?:是|为|為)?|"
    r"就是|等于|等於|Ответ|Результат|정답(?:은|는)?|결과(?:는)?|respuesta|resultado|"
    r"réponse|résultat|antwort|ergebnis)\s*[:：=]?\s*"
    rf"(?P<deger>{KESIR})\s*[.。！!]*\s*$",
    re.I,
)


def dili_olc(tahmin):
    metin = LATEX_KODU.sub("", tahmin)
    metin = re.sub(r"\\text\s*\{([^{}]*)\}", r"\1", metin)
    metin = unicodedata.normalize("NFC", metin)
    turkce_metin = metin.replace("İ", "i").replace("I", "ı").casefold()
    kanit = {}
    for dil, desen in SOZLUKLER.items():
        izler = set(desen.findall(turkce_metin if dil == "tr" else metin.casefold()))
        kisa = TURKCE_KISA if dil == "tr" else INGILIZCE_KISA if dil == "en" else set()
        if len(izler) >= 2 or izler & kisa:
            kanit[dil] = sorted(izler)

    yazi = Counter(
        unicodedata.name(harf, "").split(" ", 1)[0] for harf in metin if harf.isalpha()
    )
    for alfabe in ("CYRILLIC", "GREEK", "ARABIC", "HEBREW", "DEVANAGARI", "THAI"):
        if yazi[alfabe] >= 3:
            kanit[alfabe.lower()] = yazi[alfabe]
    kana = yazi["HIRAGANA"] + yazi["KATAKANA"]
    if yazi["HANGUL"] >= 3:
        kanit["hangul"] = yazi["HANGUL"]
    if kana >= 3:
        kanit["kana"] = kana
    # Han karakterleri Japonca ve Korece metinlerde de kullanılır.
    if yazi["CJK"] >= 3 and not (kana >= 3 or yazi["HANGUL"] >= 3):
        kanit["han"] = yazi["CJK"]

    if len(kanit) > 1:
        return "karisik", kanit
    if "tr" in kanit:
        return "turkce", kanit
    if kanit:
        return "yabanci", kanit
    return ("belirsiz" if sum(yazi.values()) else "sozel_yanit_yok"), kanit


def nihai_cevap(tahmin, tur, ifade):
    satirlar = [satir for ham in tahmin.splitlines() if (satir := temizle(ham))]
    if not satirlar:
        return None, None
    son = satirlar[-1]
    if tur not in {"compare", "invalid"}:
        eslesme = SON_BILDIRIM.search(son)
        if eslesme:
            try:
                deger = eslesme["deger"].replace(",", ".").split("/")
                pay = Fraction(deger[0].strip())
                return str(pay / Fraction(deger[1].strip()) if len(deger) == 2 else pay), "son_bildirim"
            except (ValueError, ZeroDivisionError):
                return None, None
    cevap = cevap_bul(tahmin, tur, ifade)
    if tur == "invalid" and cevap is None:
        # Sayısal bir sonuç iddiası, tanımsız bir işlemin yanlış cevabıdır.
        cevap = cevap_bul(tahmin, "add", ifade)
    if cevap is None:
        return None, None
    return cevap, "puanla"


def kimlikleri_oku(yol, anahtar):
    kayitlar = {}
    for kayit in oku(yol):
        oge = kayit if anahtar == "prediction" else kayit["meta"]
        kimlik = oge["id"]
        if kimlik in kayitlar:
            raise ValueError(f"{yol}: yinelenen kimlik {kimlik}")
        kayitlar[kimlik] = oge[anahtar] if anahtar == "prediction" else oge
    if not kayitlar:
        raise ValueError(f"{yol}: kayıt bulunamadı")
    return kayitlar


def raporla(test_yolu, tahmin_yolu, secili_kimlikler=()):
    test = kimlikleri_oku(test_yolu, "expression")
    tahminler = kimlikleri_oku(tahmin_yolu, "prediction")
    eksik = sorted(test.keys() - tahminler.keys())
    fazla = sorted(tahminler.keys() - test.keys())
    if eksik or fazla:
        raise ValueError(f"Kimlikler uyuşmuyor. Eksik {eksik}, fazla {fazla}")
    bilinmeyen = sorted(set(secili_kimlikler) - test.keys())
    if bilinmeyen:
        raise ValueError(f"Bilinmeyen kimlikler {bilinmeyen}")

    dil_sayaci = dict.fromkeys(DIL_ETIKETLERI, 0)
    matematik_sayaci = dict.fromkeys(MATEMATIK_ETIKETLERI, 0)
    capraz = {dil: dict.fromkeys(MATEMATIK_ETIKETLERI, 0) for dil in DIL_ETIKETLERI}
    sonuclar = []
    for kimlik, meta in test.items():
        if secili_kimlikler and kimlik not in secili_kimlikler:
            continue
        tahmin = tahminler[kimlik]
        if not isinstance(tahmin, str):
            raise ValueError(f"{tahmin_yolu}: {kimlik} için prediction metin olmalı")
        dil, kanit = dili_olc(tahmin)
        ifade, tur = meta["expression"], meta["kind"]
        beklenen_deger = beklenen(ifade)
        cevap, yontem = nihai_cevap(tahmin, tur, ifade)
        matematik = "okunamadi" if cevap is None else "dogru" if cevap == beklenen_deger else "yanlis"
        ara_dogru, ara_yanlis = ara_hesaplar(tahmin)
        dil_sayaci[dil] += 1
        matematik_sayaci[matematik] += 1
        capraz[dil][matematik] += 1
        sonuclar.append({
            "id": kimlik, "tur": tur, "dil": dil, "dil_kaniti": kanit,
            "nihai_deger": matematik, "okunan": cevap, "beklenen": beklenen_deger,
            "okuma_yontemi": yontem, "dogru_ara_satir": ara_dogru,
            "yanlis_ara_satir": ara_yanlis, "tahmin": tahmin,
        })
    return {
        "test": str(test_yolu.resolve()), "tahmin_dosyasi": str(tahmin_yolu.resolve()),
        "toplam": len(sonuclar), "dil": dil_sayaci, "nihai_deger": matematik_sayaci,
        "dil_ve_nihai_deger": capraz,
        "hatali_ara_hesap_iceren_yanit": sum(s["yanlis_ara_satir"] > 0 for s in sonuclar),
        "satirlar": sonuclar,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", type=Path, required=True, help="Meta verili test JSONL")
    parser.add_argument("--tahmin", type=Path, required=True, help="Kıyasla çıktısındaki tahmin JSONL")
    parser.add_argument("--id", action="append", default=[], help="Bu kimliği göster. Tekrarlanabilir.")
    parser.add_argument("--ozet", action="store_true", help="Yanıt metinlerini ve satır ayrıntılarını atla.")
    args = parser.parse_args()
    try:
        rapor = raporla(args.test, args.tahmin, args.id)
    except (KeyError, OSError, ValueError) as hata:
        parser.error(str(hata))
    if args.ozet:
        del rapor["satirlar"]
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(rapor, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
