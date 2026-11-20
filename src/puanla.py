"""Taban ve adaptör tahminlerini aynı kurallarla karşılaştırır."""

import argparse
import json
import re
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from denetle import zincir_dogrula
from matematik import GECERSIZ, beklenen, oku, sayi

KESIR = re.compile(r"[+-]?\d+(?:\s*/\s*[+-]?\d+)?")
ONDALIK = re.compile(r"[+-]?\d+[.,]\d+")
UNICODE_KESIR = {
    "½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4",
    "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5", "⅙": "1/6",
    "⅚": "5/6", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8",
}
TAM_SAYILI = re.compile(r"([+-]?\d+)(?:\s+tam\s+|\s+)(\d+)\s*/\s*(\d+)")
SONUC = re.compile(
    r"^(?:[-•]\s*|#+\s*|\d+[.)]\s*)?(?:sonu[çc](?:\s+olarak)?|cevap|yanıt|özet|answer|result)\s*[:=]\s*(.*)$", re.I,
)
SONUC_ONSOZ = re.compile(
    r"^(?:\d+[.)]\s*)?(?:bu nedenle|dolayısıyla|sonu[çc] olarak|sonuçta|o hâlde|yani|therefore|thus|so)\s*[:,]?\s*", re.I,
)
SAYI_METNI = (
    r"[+-]?\d+\s+(?:tam\s+)?\d+\s*/\s*\d+|[+-]?\d+\s*/\s*[+-]?\d+|[+-]?\d+[.,]\d+|[+-]?\d+"
)
SAYI_ADAYI = re.compile(rf"(?<![\w/])(?:{SAYI_METNI})(?![\d/])")
KIYAS_ADAYI = re.compile(rf"({SAYI_METNI})\s*([<=>])\s*({SAYI_METNI})")
CEVAP_IFADESI = re.compile(
    r"\b(?:sonucu|cevabı|yanıtı|toplamı|farkı|çarpımı|bölümü|değeri|eşiti|h[aâ]li|katı|ifadesi)\b", re.I,
)
CEVAP_CUMLESI = re.compile(
    r"\b(?:sonuç|cevap|yanıt|toplam|kalan|kaldı|vardır|var|olur|eder|bulunur|eşittir|sadeleşir|"
    r"result|equals|answer|is|remaining|drank|used)\b|\bas a result\b|\ba total of\b", re.I,
)
YAKLASIK_CUMLESI = re.compile(r",\s*(?:which is approximately|yaklaşık(?: olarak)?)\b", re.I)
GECERSIZ_YANIT = re.compile(
    r"\btanımsız(?:dır)?\b|\btanımlı değil(?:dir)?\b|\bdeğeri yok(?:tur)?\b|"
    r"\b(?:sıfıra|0'a) bölünemez\b|\bundefined\b|\bcannot divide by zero\b", re.I,
)
BIRIM = re.compile(
    r"\s*(?:litre|metre|kilometre|kilogram|kg|km|cm|gram|bardak|kupa|porsiyon|parça|paket|ölçü|"
    r"birim|m|l)(?:dir|dır|dur|dür)?(?:\s+(?:eder|kaldı|olur))?[.!]?$", re.I,
)


def temizle(metin):
    metin = re.sub("([" + "".join(UNICODE_KESIR) + "])",
                   lambda m: (" " if m.start() and metin[m.start() - 1].isdigit() else "")
                   + UNICODE_KESIR[m[1]], metin)
    metin = metin.replace("⁄", "/")
    metin = re.sub(r"(?<=\d)\\[,;!]\s*(?=\\)", " ", metin)
    metin = re.sub(
        r"\\(?:d|t)?frac\s*\{([+-]?\d+)\}\s*\{([+-]?\d+)\}",
        lambda m: ((" " if m.start() and metin[m.start() - 1].isdigit() else "")
                   + f"{m[1]}/{m[2]}"),
        metin,
    )
    metin = re.sub(r"\\boxed\{([^{}]*)\}", r"\1", metin)
    for eski, yeni in {
        "−": "-", "×": "*", "·": "*", "÷": "/", r"\times": "*", r"\cdot": "*",
        r"\div": "/", r"\lt": "<", r"\gt": ">", r"\left": "", r"\right": "",
        r"\(": "", r"\)": "", r"\[": "", r"\]": "", r"\,": "", "$": "",
        "**": "", "__": "", chr(96): "",
    }.items():
        metin = metin.replace(eski, yeni)
    return metin.strip()


def deger_bul(metin):
    metin = metin.strip(" \t.!:;")
    metin = re.sub(r"^\(([^()]*)\)$", r"\1", metin)
    metin = re.sub(r"\(([+-]?\d+)\)", r"\1", metin)
    if ONDALIK.fullmatch(metin):
        return str(Fraction(metin.replace(",", ".")))
    m = TAM_SAYILI.fullmatch(metin)
    if m:
        tam = Fraction(abs(int(m[1]))) + Fraction(int(m[2]), int(m[3]))
        return str(-tam if m[1].startswith("-") else tam)
    if KESIR.fullmatch(metin):
        return str(sayi(metin))
    return None


def yon_bul(metin, ifade):
    metin = metin.strip(" .!:;")
    ters = {"<": ">", ">": "<", "=": "="}
    if metin in ters:
        return metin
    isaretler = re.findall(r"[<=>]", metin)
    if len(isaretler) == 1 and re.search(
        r'''['"“‘][<=>]['"”’]\s*(?:işaret|sembol)''', metin, re.I,
    ):
        return isaretler[0]
    for iliski in ters:
        parcalar = metin.split(iliski)
        if len(parcalar) != 2:
            continue
        try:
            gosterilen = [sayi(parca) for parca in parcalar]
            esas = [sayi(parca) for parca in ifade.split("|")]
        except (ValueError, SyntaxError, ZeroDivisionError):
            continue
        if gosterilen == esas:
            return iliski
        if gosterilen == esas[::-1]:
            return ters[iliski]
    esas = [sayi(parca) for parca in ifade.split("|")]
    for m in reversed(list(KIYAS_ADAYI.finditer(metin))):
        try:
            gosterilen = [deger_bul(m[1]), deger_bul(m[3])]
        except (ValueError, SyntaxError, ZeroDivisionError):
            continue
        if gosterilen == [str(n) for n in esas]:
            return m[2]
        if gosterilen == [str(n) for n in esas[::-1]]:
            return ters[m[2]]
    sozcukler = {"<": r"küçük(?:tür)?|daha az", ">": r"büyük(?:tür)?|daha fazla", "=": r"eşit(?:tir)?"}
    bulunan = [isaret for isaret, desen in sozcukler.items() if re.search(rf"\b(?:{desen})\b", metin, re.I)]
    if len(bulunan) == 1:
        ozne = re.search(rf"({SAYI_METNI})\s+(?:daha\s+)?(?:küçük|büyük)(?:tür)?\b", metin, re.I)
        kesirler = [ozne[1]] if ozne else KESIR.findall(metin)
        if len(kesirler) == 2:
            try:
                esas = [sayi(parca) for parca in ifade.split("|")]
                gosterilen = [sayi(parca) for parca in kesirler]
            except (ValueError, SyntaxError, ZeroDivisionError):
                return None
            if gosterilen == esas[::-1] and gosterilen != esas:
                return ters[bulunan[0]]
            if gosterilen != esas:
                return None
        elif len(kesirler) == 1:
            try:
                deger = deger_bul(kesirler[0])
            except (ValueError, SyntaxError, ZeroDivisionError):
                return None
            if deger == str(esas[0]):
                return bulunan[0]
            if deger == str(esas[1]):
                return ters[bulunan[0]]
            return None
        elif not kesirler:
            taraf = re.search(r"\b(?:soldaki|sağdaki|birinci(?:si)?|ikinci(?:si)?)\b", metin, re.I)
            if taraf and taraf[0].lower() in {"sağdaki", "ikinci", "ikincisi"}:
                return ters[bulunan[0]]
        else:
            return None
        return bulunan[0]
    return None


def cevap_satiri(metin, tur, ifade):
    if tur == "compare":
        return yon_bul(metin, ifade)
    if tur == "invalid":
        eslesme = GECERSIZ_YANIT.search(metin)
        if eslesme and not re.match(r"\s+değil", metin[eslesme.end():], re.I):
            return GECERSIZ
        return None
    metin = re.sub(r"\\text\{([^{}]+)\}", r" \1", metin)
    metin = YAKLASIK_CUMLESI.split(metin, maxsplit=1)[0]
    metin = metin.rsplit("=", 1)[-1].strip()
    metin = re.sub(r"^(?:sonuç|cevap|yanıt)\s*[,:-]?\s*", "", metin, flags=re.I)
    try:
        deger = yalniz_deger(metin)
        if deger is not None:
            return deger
        for cumle in reversed(re.split(r"(?<=[.!?])\s+", metin)):
            for eslesme in reversed(list(CEVAP_IFADESI.finditer(cumle))):
                aday = yalniz_deger(cumle[eslesme.end():])
                if aday is not None:
                    return aday
            if "..." in cumle or "≈" in cumle:
                continue
            alternatif = re.split(r"\bveya\b", cumle, flags=re.I)
            if len(alternatif) == 2:
                a, b = (yalniz_deger(s) for s in alternatif)
                if a is not None and a == b:
                    return a
            if not CEVAP_CUMLESI.search(cumle):
                continue
            sonek = re.search(rf"({SAYI_METNI})['’]?(?:y?[ae])?\s+eşittir\b", cumle, re.I)
            if sonek:
                return deger_bul(sonek[1])
            sayilar = SAYI_ADAYI.findall(cumle)
            if len(sayilar) == 1:
                return deger_bul(sayilar[0])
    except (ValueError, SyntaxError, ZeroDivisionError):
        return None
    return None


def yalniz_deger(metin):
    metin = metin.strip(" ,.:!")
    metin = re.sub(
        r"\s+(?:olacaktır|eder|kaldı|olur|eşittir|olarak (?:yanıtlanabilir|sonuçlanır|yazılır))[.!]?$", "", metin, flags=re.I,
    )
    metin = re.sub(r"(?<=\d)['’](?:dir|dır|dur|dür|tir|tır|tur|tür)[.!]?$", "", metin, flags=re.I)
    metin = re.sub(r"(?<=\d)['’](?:a|e|ya|ye)$", "", metin, flags=re.I)
    metin = BIRIM.sub("", metin)
    if metin.rstrip(".").casefold() == "sıfır":
        return "0"
    return deger_bul(metin)


def cevap_bul(tahmin, tur, ifade):
    satirlar = [temizle(s) for s in tahmin.splitlines()]
    satirlar = [s for s in satirlar if s]
    for i in range(len(satirlar) - 1, -1, -1):
        if (m := SONUC.match(satirlar[i])) is not None:
            metin = m[1] or (satirlar[i + 1] if i + 1 < len(satirlar) else "")
            cevap = cevap_satiri(metin, tur, ifade)
            if cevap is not None or m[1] or i + 2 >= len(satirlar):
                return cevap
            return cevap_satiri(satirlar[i + 2], tur, ifade)
    if not satirlar:
        return None
    # Son cümle ya da son matematik satırı. Önceki ara işlemlere geri dönme.
    son = cevap_satiri(SONUC_ONSOZ.sub("", satirlar[-1]), tur, ifade)
    if son is not None:
        return son
    # Sonuç bildiren cümleyi izleyen bağımsız matematik satırını da oku.
    # Model aynı kapanışta iki farklı değer bildirirse otomatik karar verme.
    kapanislar = set()
    for i in range(max(0, len(satirlar) - 4), len(satirlar) - 1):
        satir = satirlar[i]
        if not SONUC_ONSOZ.match(satir):
            continue
        cevap = cevap_satiri(SONUC_ONSOZ.sub("", satir), tur, ifade)
        if cevap is not None:
            kapanislar.add(cevap)
        if satir.endswith(":"):
            cevap = cevap_satiri(satirlar[i + 1], tur, ifade)
            if cevap is not None:
                kapanislar.add(cevap)
    return next(iter(kapanislar)) if len(kapanislar) == 1 else None


def ara_hesaplar(tahmin):
    dogru, yanlis = 0, 0
    for satir in tahmin.splitlines():
        metin = temizle(satir)
        if SONUC.match(metin) or not re.fullmatch(r"[\d+\-*/() <>=]+", metin):
            continue
        if not re.search(r"[<=>]", metin):
            continue
        metin = re.sub(r"\s*([<=>])\s*", r" \1 ", metin)
        try:
            zincir_dogrula(metin)
        except (SyntaxError, ZeroDivisionError):
            continue
        except ValueError:
            yanlis += 1
        else:
            dogru += 1
    return dogru, yanlis


def puanla(test_yolu, tahmin_yolu):
    tahminler = {}
    for satir in oku(tahmin_yolu):
        kimlik = satir["id"]
        if kimlik in tahminler:
            raise ValueError(f"Yinelenen tahmin: {kimlik}")
        tahminler[kimlik] = satir["prediction"]

    turler = defaultdict(lambda: {"toplam": 0, "dogru": 0, "cevap_okunamadi": 0})
    satirlar = []
    toplam_dogru = 0
    for satir in oku(test_yolu):
        meta = satir["meta"]
        kimlik, tur, ifade = meta["id"], meta["kind"], meta["expression"]
        tahmin = tahminler.pop(kimlik)
        cevap = cevap_bul(tahmin, tur, ifade)
        altin = beklenen(ifade)
        dogru = cevap == altin
        ara_dogru, ara_yanlis = ara_hesaplar(tahmin)
        sayac = turler[tur]
        sayac["toplam"] += 1
        sayac["dogru"] += dogru
        sayac["cevap_okunamadi"] += cevap is None
        toplam_dogru += dogru
        satirlar.append({
            "id": kimlik, "kind": tur, "gold": altin, "parsed": cevap, "correct": dogru,
            "checkable_correct_lines": ara_dogru, "checkable_wrong_lines": ara_yanlis,
        })
    if tahminler:
        raise ValueError(f"Testte olmayan tahmin kimliği: {next(iter(tahminler))}")
    if not satirlar:
        raise ValueError("Test kümesi boş")

    return {
        "test": str(test_yolu),
        "tahmin": str(tahmin_yolu),
        "toplam": len(satirlar),
        "dogru": toplam_dogru,
        "cevap_okunamadi": sum(s["parsed"] is None for s in satirlar),
        "ara_hesabi_okunabilen_yanit": sum(
            s["checkable_correct_lines"] + s["checkable_wrong_lines"] > 0 for s in satirlar
        ),
        "hatali_ara_hesap_iceren_yanit": sum(s["checkable_wrong_lines"] > 0 for s in satirlar),
        "turler": dict(sorted(turler.items())),
        "satirlar": satirlar,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--test", required=True, type=Path)
    cli.add_argument("--tahmin", required=True, type=Path)
    cli.add_argument("--out", required=True, type=Path)
    args = cli.parse_args()
    rapor = puanla(args.test, args.tahmin)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rapor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{rapor['dogru']}/{rapor['toplam']} doğru, {rapor['cevap_okunamadi']} okunamadı → {args.out}")

