"""Megazeka-Kesir v1.3 verisi: sade ifadeler, çeşitli yazımlar ve
çok basamaklı çarpmaları, EBOB'u, ortak paydayı ara satırlarda gösteren çözümler üretir."""

import argparse
import json
import math
import random
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path

from matematik import canonical_key, oku
from okunus import kesir_soz, rakam_eki, soz, tam_sayili_soz
from sorular_v11 import BASIC_PROMPTS, BOSLUK, TAM_EK
from sorular_v12 import CUMLE, SOZEL, ZINCIR
import okunus

ROOT = Path(__file__).resolve().parents[1]
ORANLAR = {
    "simplify": 6, "compare": 8, "add": 9, "sub": 9, "mul": 9, "div": 9,
    "mixed": 22, "invalid": 4, "word_add": 6, "word_sub": 6, "word_of": 6, "word_div": 6,
}
ASCII_ISARET = {"+": "+", "-": "-", "×": "*", "÷": "/"}
ISARET_TUR = {"+": "add", "-": "sub", "×": "mul", "÷": "div"}
ISARET = {"add": "+", "sub": "-", "mul": "×", "div": "÷"}
ASCII = {"+": "+", "-": "-", "×": "*", "÷": "/"}
KELIME_ISLEMI = {"word_add": "add", "word_sub": "sub", "word_of": "mul", "word_div": "div"}
KELIME_ADIMI = {
    "word_add": "Toplam miktarı bulmak için iki kesri topla.",
    "word_sub": "Kalan miktarı bulmak için kullanılan kesri başlangıç miktarından çıkar.",
    "word_of": "Bir miktarın belli bir kesrini bulmak için miktarı verilen kesirle çarp.",
    "word_div": "Porsiyon sayısını bulmak için toplam miktarı bir porsiyonun miktarına böl.",
}
SEMBOLIK_ORAN = 0.4
SEMBOLIK_SABLONLAR = ("{islem}", "{islem} = ?", "{islem}=?", "{islem} =", "{islem}?", "{islem} kaç?")
SEMBOLIK_KIYAS = ("{a} ? {b}", "{a} __ {b}")
SADE_HARF = str.maketrans("çğıöşüÇĞİÖŞÜâÂ", "cgiosuCGIOSUaA")

# --- İşlenenler ---------------------------------------------------------------
# ("k", pay, payda): kesir (payda > 0, sadeleştirme sorusunda payda negatif olabilir)
# ("t", tam, pay, payda): tam sayılı kesir; tam işaretlidir, 0 < pay < payda


def deger(op):
    if op[0] == "k":
        return Fraction(op[1], op[2])
    _, tam, pay, payda = op
    return (1 if tam > 0 else -1) * (abs(tam) + Fraction(pay, payda))


def yaz(kesir):
    pay, payda = kesir
    if payda < 0:
        return f"{pay}/({payda})"
    return f"{pay}/{payda}" if payda != 1 else str(pay)


def parantez(kesir):
    return f"({yaz(kesir)})"


def ikili(sol, isaret, sag):
    return f"{parantez(sol)} {isaret} {parantez(sag)}"


def cift(deger_):
    return deger_.numerator, deger_.denominator


def tam_ascii(op):
    _, tam, pay, payda = op
    return f"{'-' if tam < 0 else ''}({abs(tam)}+{pay}/{payda})"


def op_ascii(op):
    return f"({tam_ascii(op)})" if op[0] == "t" else parantez(op[1:])


def baslik_ikili(sol, isaret, sag):
    if isaret == "÷":
        return f"({op_ascii_goster(sol)}) ÷ ({op_ascii_goster(sag)})"
    return f"{op_baslik(sol)} {isaret} {op_baslik(sag)}"


def op_ascii_goster(op):
    return f"{op[1]} tam {op[2]}/{op[3]}" if op[0] == "t" else yaz(op[1:])


def op_baslik(op):
    """Başlıkta işlenenin kanonik gösterimi."""
    if op[0] == "t":
        return f"({op[1]} tam {op[2]}/{op[3]})"
    pay, payda = op[1:]
    return parantez((pay, payda)) if pay < 0 else yaz((pay, payda))


# --- Ara hesap yardımcıları ------------------------------------------------------


def basamaklar(n):
    parcalar, carpan = [], 1
    while n:
        n, r = divmod(n, 10)
        if r:
            parcalar.append(r * carpan)
        carpan *= 10
    return parcalar[::-1]


def carpim(a, b):
    """İki sayının çarpımı çok basamaklıysa basamak basamak açılmış satırlar döndürür."""
    x, y = abs(a), abs(b)
    if x <= 1 or y <= 1 or x * y <= 100:
        return []
    if min(x, y) < 10 and max(x, y) < 100 or len(basamaklar(x)) == 1 or len(basamaklar(y)) == 1:
        return [f"{x} × {y} = {x * y}"]
    bol_y = y <= x if min(x, y) >= 10 else y >= x
    parcalar = basamaklar(y if bol_y else x)
    if len(parcalar) == 1:
        return [f"{x} × {y} = {x * y}"]
    terimler = [f"{x} × {p}" if bol_y else f"{p} × {y}" for p in parcalar]
    sonuclar = [x * p if bol_y else p * y for p in parcalar]
    return [f"{x} × {y} = {' + '.join(terimler)} = {' + '.join(map(str, sonuclar))} = {x * y}"]


def oklid(x, y):
    satirlar = []
    while y:
        q, r = divmod(x, y)
        satirlar.append(f"{x} = {q} × {y} + {r}")
        x, y = y, r
    return x, satirlar


def ortak_payda(b, d, adimlar):
    buyuk, kucuk = max(b, d), min(b, d)
    if kucuk == 1:
        adimlar.append((f"Tam sayıyı paydası {buyuk} olan kesir olarak yaz. Ortak payda {buyuk}.",
                        [f"{buyuk} = {buyuk} × 1"]))
        return buyuk
    if buyuk % kucuk == 0:
        adimlar.append((f"{buyuk}, {kucuk} sayısının katı olduğu için ortak payda {buyuk}.",
                        [f"{buyuk} = {buyuk // kucuk} × {kucuk}"]))
        return buyuk
    if buyuk <= 12:
        L = math.lcm(b, d)
        adimlar.append((f"{b} ile {d} sayısının en küçük ortak katı {L}.",
                        [f"{L} = {L // b} × {b} = {L // d} × {d}"]))
        return L
    g, satirlar = oklid(buyuk, kucuk)
    adimlar.append((f"Paydaların EBOB'unu bulmak için {buyuk} ile {kucuk} sayısına Öklid bölmesi uygula.", satirlar))
    L = b // g * d
    hesap = carpim(b // g, d)
    hesap.append(f"{b} ÷ {g} × {d} = {b // g} × {d} = {L}")
    hesap.append(f"{L} = {L // b} × {b} = {L // d} × {d}")
    adimlar.append((f"Son sıfır olmayan kalan {g}, yani EBOB {g}. Ortak payda {b} ÷ {g} × {d}.", hesap))
    return L


def sade_adimi(ham, adimlar):
    p, d = ham
    sonuc = Fraction(p, d)
    if d < 0:
        adimlar.append(("Pay ve paydayı -1 ile çarparak paydayı pozitif yap.", [f"{yaz(ham)} = {yaz((-p, -d))}"]))
        p, d = -p, -d
    if p == 0:
        if d != 1:
            adimlar.append(("Payı 0 olan kesrin değeri 0.", [f"{yaz((p, d))} = 0"]))
        return sonuc
    g = math.gcd(p, d)
    if max(abs(p), d) >= 50 and abs(p) != d:
        buyuk, kucuk = max(abs(p), d), min(abs(p), d)
        _, satirlar = oklid(buyuk, kucuk)
        adimlar.append((f"Sadeleştirmek için {buyuk} ile {kucuk} sayısının EBOB'unu Öklid bölmesiyle bul.", satirlar))
        if g == 1:
            adimlar.append(("Son sıfır olmayan kalan 1, yani EBOB 1. Kesir zaten en sade hâlinde.",
                            [f"{yaz((p, d))} = {sonuc}"]))
            return sonuc
        adimlar.append((
            f"Son sıfır olmayan kalan {g}, yani EBOB {g}. Payı ve paydayı {g} ile böl.",
            [f"{yaz((p, d))} = ({p} ÷ {g})/({d} ÷ {g}) = {sonuc}"],
        ))
        return sonuc
    if g > 1:
        adimlar.append((
            f"Payı ve paydayı ortak bölenleri olan {g} ile böl.",
            [f"{yaz((p, d))} = ({p} ÷ {g})/({d} ÷ {g}) = {sonuc}"],
        ))
    return sonuc


def dort_islem(tur, sol, sag, adimlar):
    a, b = sol
    c, d = sag
    ars = ISARET[tur]
    ilk = ikili(sol, ars, sag)
    if tur in {"add", "sub"}:
        if b != d:
            L = ortak_payda(b, d, adimlar)
            k1, k2 = L // b, L // d
            sol_pay, sag_pay = a * k1, c * k2
            hesap = carpim(a, k1) + carpim(c, k2)
            hesap.append(f"{ilk} = {ikili((sol_pay, L), ars, (sag_pay, L))}")
            if k1 == 1:
                aciklama = f"İlk kesir aynı kalır. İkincinin pay ve paydasını {k2} ile çarp."
            elif k2 == 1:
                aciklama = f"İlk kesrin pay ve paydasını {k1} ile çarp. İkinci kesir aynı kalır."
            else:
                aciklama = f"İlk kesrin pay ve paydasını {k1} ile, ikincininkini {k2} ile çarp."
            adimlar.append((aciklama, hesap))
        else:
            L, sol_pay, sag_pay = b, a, c
        ham = sol_pay + sag_pay if tur == "add" else sol_pay - sag_pay
        zincir = f"{ikili((sol_pay, L), ars, (sag_pay, L))} = ({sol_pay} {ars} ({sag_pay}))/{L}"
        if sag_pay < 0:
            zincir += f" = ({sol_pay} {'+' if tur == 'sub' else '-'} {-sag_pay})/{L}"
        zincir += f" = {yaz((ham, L))}"
        eylem = "topla" if tur == "add" else "çıkar"
        adimlar.append((f"Payları {eylem}, ortak paydayı koru.", [zincir]))
        return sade_adimi((ham, L), adimlar)
    if tur == "div":
        ters = (-d, -c) if c < 0 else (d, c)
        adimlar.append((
            "Bölen kesrin tersini al ve çarp." + (" Ters kesrin eksi işaretini paya yaz." if c < 0 else ""),
            [f"{ilk} = {ikili(sol, '×', ters)}"],
        ))
        c, d = ters
        sag = ters
    hesap = carpim(a, c) + carpim(b, d)
    hesap.append(f"{ikili(sol, '×', sag)} = ({a} × ({c}))/({b} × {d}) = {yaz((a * c, b * d))}")
    adimlar.append(("Payları kendi arasında, paydaları kendi arasında çarp.", hesap))
    return sade_adimi((a * c, b * d), adimlar)


def tam_cevir(op, adimlar):
    _, tam, pay, payda = op
    T = abs(tam)
    eksi = "-" if tam < 0 else ""
    bilesik = (-(T * payda + pay) if tam < 0 else T * payda + pay, payda)
    hesap = carpim(T, payda)
    hesap.append(
        f"{tam_ascii(op)} = {eksi}(({T} × {payda} + {pay})/{payda}) = {eksi}(({T * payda} + {pay})/{payda})"
        f" = {yaz(bilesik)}"
    )
    adimlar.append((
        f"{T} tam {pay}/{payda} sayısını bileşik kesre çevir: tam kısmı paydayla çarp, payı ekle"
        + (" ve eksi işaretini koru." if tam < 0 else "."),
        hesap,
    ))
    return bilesik


# --- Sayı seçimi -----------------------------------------------------------------


def kesir_sec(rng, pozitif=False, basit=False, sifir=True, tamsayi=0.0):
    d = rng.randint(2, 12 if rng.random() < 0.65 else 40)
    if basit:
        return ("k", rng.randint(1, d - 1), d)
    if rng.random() < tamsayi:
        n = rng.randint(1, 9)
        return ("k", -n if not pozitif and rng.random() < 0.25 else n, 1)
    a = rng.randint(0 if sifir else 1, 2 * d + 8)
    if not pozitif and a and rng.random() < 0.26:
        a = -a
    return ("k", a, d)


def tam_sec(rng, negatif=0.2, buyuk=9):
    payda = rng.randint(2, 12 if rng.random() < 0.7 else 30)
    pay = rng.randint(1, payda - 1)
    while math.gcd(pay, payda) > 1 and rng.random() < 0.8:
        pay = rng.randint(1, payda - 1)
    tam = rng.randint(1, buyuk)
    return ("t", -tam if rng.random() < negatif else tam, pay, payda)


# --- Soru biçimlendirme ------------------------------------------------------------


class Yazim:
    """Bir sorudaki rakamlı gösterimin üslubu."""

    def __init__(self, rng, sade=False):
        self.sembolik = False
        self.bolu = "/" if sade or rng.random() < 0.88 else rng.choice("⁄⁄∕")
        self.eksi = "-" if sade or rng.random() < 0.7 else "−"
        self.negatif = "parantez" if sade else rng.choices(
            ["parantez", "ciplak", "pay", "payda"], [45, 30, 15, 10])[0]
        self.bosluk = sade or rng.random() < 0.8
        self.carpi = "×" if sade else rng.choices(["×", "*", "·", "x"], [55, 25, 15, 5])[0]
        self.bolme = "÷" if sade else rng.choices(["÷", ":", "/"], [55, 30, 15])[0]
        self.kip = rng.choice(["bolu", "de", "de"])

    def ifade_bicimi(self, rng):
        self.sembolik = rng.random() < SEMBOLIK_ORAN
        if self.sembolik:
            self.bolu = "/"
            self.negatif = "parantez"
            self.bosluk = rng.random() < 0.45
            self.carpi = rng.choice(("×", "*", "·"))
            self.bolme = rng.choice(("÷", ":", "/"))

    def kesir(self, pay, payda, ifade_icinde=True, sadelestirme=False):
        e, s = self.eksi, self.bolu
        if payda == 1:
            metin = f"{e}{-pay}" if pay < 0 else str(pay)
            return f"({metin})" if pay < 0 and ifade_icinde and self.negatif == "parantez" else metin
        if sadelestirme:
            # Sadeleştirmede işaretlerin yeri sorunun parçasıdır, kaydırılmaz.
            p = f"{e}{-pay}" if pay < 0 else str(pay)
            q = f"{e}{-payda}" if payda < 0 else str(payda)
            if self.negatif == "pay" and pay < 0:
                p = f"({p})"
            if (self.sembolik or self.negatif in {"pay", "payda"}) and payda < 0:
                q = f"({q})"
            return f"{p}{s}{q}"
        if pay >= 0:
            return f"{pay}{s}{payda}"
        if self.negatif == "pay":
            return f"({e}{-pay}){s}{payda}"
        if self.negatif == "payda":
            return f"{-pay}{s}({e}{payda})" if self.bosluk else f"{-pay}{s}{e}{payda}"
        metin = f"{e}{-pay}{s}{payda}"
        return f"({metin})" if ifade_icinde and self.negatif == "parantez" else metin

    def op(self, op, ifade_icinde=True):
        if op[0] == "k":
            return self.kesir(op[1], op[2], ifade_icinde)
        if self.sembolik:
            return f"({tam_ascii(op)})" if ifade_icinde else tam_ascii(op)
        _, tam, pay, payda = op
        metin = f"{self.eksi if tam < 0 else ''}{abs(tam)} tam {pay}{self.bolu}{payda}"
        return f"({metin})" if ifade_icinde else metin

    def isaret(self, isaret):
        return {"+": "+", "-": self.eksi, "×": self.carpi, "÷": self.bolme}[isaret]

    def bolme_parantezi(self, isaret):
        return isaret == "÷" and (self.sembolik or self.bolme == "/")

    def ikili(self, sol, isaret, sag):
        if self.bolme_parantezi(isaret):
            sol_m, sag_m = f"({self.op(sol, False)})", f"({self.op(sag, False)})"
        else:
            sol_m, sag_m = self.op(sol), self.op(sag)
        ara = f" {self.isaret(isaret)} " if self.bosluk else self.isaret(isaret)
        return f"{sol_m}{ara}{sag_m}"


def okunus_metni(op, kip, rng):
    if op[0] == "t":
        if (op[2], op[3]) == (1, 2) and rng.random() < 0.3:
            return tam_sayili_soz(op[1], 1, 2, "bucuk")
        return tam_sayili_soz(*op[1:], kip)
    pay, payda = op[1:]
    if payda > 0 and pay > 0 and rng.random() < 0.35 and (pay, payda) in {(1, 2), (1, 4)}:
        return "yarım" if payda == 2 else "çeyrek"
    if kip == "de" and not 0 < abs(pay) < payda <= 100:
        kip = "bolu"
    return kesir_soz(pay, payda, kip)


def rakam_okunus(op):
    """Rakamlı yazıma ek getirmek için okunuş (kesirlerde son kelime payda)."""
    if op[0] == "t":
        return kesir_soz(op[2], op[3], "bolu")
    return kesir_soz(op[1], op[2], "bolu")


def op_rakam_baslik(op):
    if op[0] == "t":
        return f"{op[1]} tam {op[2]}/{op[3]}"
    return yaz(op[1:])


def buyuk_harf(h):
    return {"i": "İ", "ı": "I"}.get(h, h.upper())


def kucuk(metin):
    return metin.replace("İ", "i").replace("I", "ı").lower()


def buyut(soru):
    """Cümle başındaki sözle yazılmış sayıyı büyük harfle başlatır."""
    soru = buyuk_harf(soru[0]) + soru[1:]
    return re.sub(r"([.?!] )([a-zçğıöşü])", lambda m: m[1] + buyuk_harf(m[2]), soru)


YUVA = re.compile(r"\{(\w)(?:\|(\w+))?\}")


def doldur(sablon, oplar, rng, sozle, yazim):
    """Şablondaki yuvaları sözle ya da rakamla doldurur, okunuş listesini döndürür."""
    okunuslar = {}
    kip = yazim.kip

    def yerine(m):
        harf, hal = m[1], m[2]
        op = oplar[harf]
        if sozle:
            if harf not in okunuslar:
                okunuslar[harf] = okunus_metni(op, kip, rng)
            metin = okunuslar[harf]
            return okunus.ek(metin, hal) if hal else metin
        metin = yazim.op(op, ifade_icinde=False) if op[0] in "kt" else str(op)
        if hal:
            return rakam_eki(metin, rakam_okunus(op), hal)
        return metin

    soru = buyut(YUVA.sub(yerine, sablon))
    return soru, [(okunuslar[h], oplar[h]) for h in sorted(okunuslar)]


def bozum(soru, rng):
    """Gerçek yazımdaki küçük farklılıklar: Türkçe karaktersiz yazım, küçük harf, noktalama."""
    if rng.random() < 0.07:
        soru = soru.translate(SADE_HARF)
    if rng.random() < 0.12:
        soru = kucuk(soru[0]) + soru[1:]
    if rng.random() < 0.15 and soru[-1] in ".?":
        soru = soru[:-1].rstrip()
    return soru


def okunus_satiri(okunuslar, soru):
    parcalar = []
    for metin, op in okunuslar:
        yumusak = re.sub(r"dört$", "dörd", metin)
        if kucuk(metin) not in kucuk(soru) and kucuk(yumusak) not in kucuk(soru):
            metin = metin.translate(SADE_HARF)
        parcalar.append(f"{metin} = {op_rakam_baslik(op)}")
    return "Okunuş: " + "; ".join(parcalar)


# --- Örnek kurma ---------------------------------------------------------------------


def ifade_sorusu(tur, islem, rng, yazim):
    sablonlar = SEMBOLIK_SABLONLAR if yazim.sembolik else BASIC_PROMPTS[tur][:6]
    return rng.choice(sablonlar).format(islem=islem)


def ikili_soru(tur, sol, sag, rng, ozel=None):
    """İki işlenenli soruyu ifade ya da cümle şablonuyla yazar."""
    yazim = Yazim(rng)
    isaret = ISARET[tur]
    if rng.random() < 0.45:
        yazim.ifade_bicimi(rng)
        islem = yazim.ikili(sol, isaret, sag)
        return ifade_sorusu(tur, islem, rng, yazim), [], yazim.sembolik
    sozle = rng.random() < 0.72
    sablon = rng.choice(ozel or CUMLE[tur])
    soru, okunuslar = doldur(sablon, {"a": sol, "b": sag}, rng, sozle, yazim)
    return soru, okunuslar, False


def ornek_basit(tur, rng):
    adimlar = []
    sol = kesir_sec(rng, tamsayi=0.06)
    sag = kesir_sec(rng, sifir=tur != "div", tamsayi=0.06)
    if tur in {"add", "sub"} and rng.random() < 0.2:
        sag = ("k", sag[1], sol[2])
    sonuc = dort_islem(tur, sol[1:], sag[1:], adimlar)
    ifade = f"{op_ascii(sol)} {ASCII[ISARET[tur]]} {op_ascii(sag)}"
    baslik = f"İşlem: {baslik_ikili(sol, ISARET[tur], sag)}"
    soru, okunuslar, _ = ikili_soru(tur, sol, sag, rng)
    return soru, okunuslar, baslik, adimlar, str(sonuc), ifade


def ornek_sade(rng):
    adimlar = []
    d = rng.randint(2, 29)
    a = rng.randint(-3 * d, 3 * d)
    g = rng.choice([1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 18])
    secim = rng.random()
    if secim < 0.08:
        d = -d
    elif secim < 0.14:
        a, d = -abs(a) or -1, -d
    ham = (a * g, d * g)
    sonuc = sade_adimi(ham, adimlar)
    if not adimlar:
        adimlar.append(("Pay ile paydanın en büyük ortak böleni 1, yani kesir en sade hâlinde.",
                        [f"{yaz(ham)} = {sonuc}"]))
    yazim = Yazim(rng)
    okunuslar = []
    r = rng.random()
    if r < 0.4:
        yazim.ifade_bicimi(rng)
        islem = yazim.kesir(*ham, ifade_icinde=False, sadelestirme=True)
        soru = ifade_sorusu("simplify", islem, rng, yazim)
    elif r < 0.6 or ham[1] < 0:
        sozle = rng.random() < 0.5
        p, q = ham
        metin_p = soz(p) if sozle else (f"{yazim.eksi}{-p}" if p < 0 else str(p))
        metin_q = soz(q) if sozle else (f"{yazim.eksi}{-q}" if q < 0 else str(q))
        soru = rng.choice(CUMLE["simplify_tarif"]).format(p=metin_p, q=metin_q)
        if sozle:
            okunuslar = [(metin_p, ("k", p, 1)), (metin_q, ("k", q, 1))]
    else:
        soru, okunuslar = doldur(rng.choice(CUMLE["simplify"]), {"a": ("k", *ham)}, rng,
                                 rng.random() < 0.7, yazim)
    return soru, okunuslar, f"Kesir: {yaz(ham)}", adimlar, str(sonuc), yaz(ham)


def ornek_kiyas(rng):
    adimlar = []
    tamli = rng.random() < 0.2
    if tamli:
        sol = tam_sec(rng, negatif=0.3, buyuk=6)
        sag = tam_sec(rng, negatif=0.3, buyuk=6)
        if rng.random() < 0.6:
            sag = ("t", sol[1], *sag[2:])
        if deger(sol) == deger(sag):
            sag = ("t", sag[1] + (1 if sag[1] > 0 else -1), *sag[2:])
        sv, qv = tam_cevir(sol, adimlar), tam_cevir(sag, adimlar)
        adimlar.append(("İki bileşik kesri karşılaştır.", None))
    else:
        sol = kesir_sec(rng, sifir=False)
        if rng.random() < 0.12 and sol[1] > 0:
            sol = ("k", -sol[1], sol[2])
        secim = rng.random()
        if secim < 0.24:
            k = rng.randint(2, 8)
            sag = ("k", sol[1] * k, sol[2] * k)
        elif secim < 0.46:
            sag = ("k", sol[1] + rng.choice([-2, -1, 1, 2]), sol[2])
        else:
            sag = kesir_sec(rng)
            if sol[1] < 0 < sag[1] and rng.random() < 0.6:
                sag = ("k", -sag[1], sag[2])
        sv, qv = sol[1:], sag[1:]
    b, d = sv[1], qv[1]
    L = b if b == d else ortak_payda(b, d, adimlar)
    p, q = sv[0] * (L // b), qv[0] * (L // d)
    isaret = "<" if p < q else ">" if p > q else "="
    if b != d:
        hesap = carpim(sv[0], L // b) + carpim(qv[0], L // d)
        hesap += [f"{yaz(sv)} = {yaz((p, L))}", f"{yaz(qv)} = {yaz((q, L))}"]
        adimlar.append(("İki kesri de bu paydayla yaz.", hesap))
    adimlar.append(("Paydalar aynı olduğunda payları karşılaştır.", [f"{yaz((p, L))} {isaret} {yaz((q, L))}"]))
    yazim = Yazim(rng)
    r = rng.random()
    okunuslar = []
    if r < 0.3:
        yazim.ifade_bicimi(rng)
        a, b = yazim.op(sol, False), yazim.op(sag, False)
        if yazim.sembolik:
            soru = rng.choice(SEMBOLIK_KIYAS).format(a=a, b=b)
        else:
            soru = ifade_sorusu("compare", f"{a} ve {b}", rng, yazim)
    elif r < 0.5:
        soru = rng.choice(CUMLE["compare_bos"]).format(
            a=yazim.op(sol, False), b=yazim.op(sag, False), bos=rng.choice(BOSLUK))
    else:
        soru, okunuslar = doldur(rng.choice(CUMLE["compare"]), {"a": sol, "b": sag}, rng,
                                 rng.random() < 0.72, yazim)
    if tamli:
        ifade = f"{tam_ascii(sol)}|{tam_ascii(sag)}"
        baslik = f"İşlem: {op_baslik(sol)} ve {op_baslik(sag)}"
    else:
        ifade = f"{yaz(sol[1:])}|{yaz(sag[1:])}"
        baslik = f"İşlem: {yaz(sol[1:])} ve {yaz(sag[1:])}"
    return soru, okunuslar, baslik, adimlar, isaret, ifade


def ornek_tanimsiz(rng):
    adimlar = []
    yazim = Yazim(rng)
    if rng.random() < 0.3:
        return zincir(rng, gizli_sifir=True)
    if rng.random() < 0.5:
        pay = rng.randint(-150, 150)
        op = ("k", pay, 0)
        adimlar.append(("Payda 0 olduğu için bu kesir tanımsız.", None))
        r = rng.random()
        okunuslar = []
        if r < 0.5:
            yazim.ifade_bicimi(rng)
        e = yazim.eksi
        metin = f"{e}{-pay}{yazim.bolu}0" if pay < 0 else f"{pay}{yazim.bolu}0"
        if r < 0.5:
            soru = ifade_sorusu("invalid", metin, rng, yazim)
        else:
            sozle = rng.random() < 0.6
            if sozle:
                okuma = kesir_soz(pay, 1, "bolu") + " bölü sıfır"
                okunuslar = [(okuma, op)]
                sablon = rng.choice(CUMLE["invalid_kesir"])
                soru = re.sub(r"\{a(?:\|(\w+))?\}",
                              lambda m: okunus.ek(okuma, m[1]) if m[1] else okuma, sablon)
            else:
                sablon = rng.choice(CUMLE["invalid_kesir"])
                soru = re.sub(r"\{a(?:\|(\w+))?\}",
                              lambda m: rakam_eki(metin, "sıfır", m[1]) if m[1] else metin, sablon)
        ifade = f"{pay}/0"
        return soru, okunuslar, f"Kesir: {pay}/0", adimlar, "tanımsız", ifade
    sol = kesir_sec(rng, sifir=False)
    sag = ("k", 0, rng.randint(2, 36))
    adimlar.append(("Bölen kesrin değeri 0. Bir sayıyı 0'a bölmek tanımsızdır.", [f"{yaz(sag[1:])} = 0"]))
    soru, okunuslar, sembolik = ikili_soru("div", sol, sag, rng)
    if not sembolik and (okunuslar or rng.random() < 0.3):
        soru = soru.rstrip(".?") + rng.choice(("?", ". Tanımlıysa sonucu yaz.", ". Sonuç var mı?"))
    baslik = f"İşlem: {op_baslik(sol)} ÷ ({yaz(sag[1:])})"
    return soru, okunuslar, baslik, adimlar, "tanımsız", f"{op_ascii(sol)} / {op_ascii(sag)}"


def ornek_karma(rng):
    adimlar = []
    r = rng.random()
    yazim = Yazim(rng)
    if r < 0.12:
        # Tek tam sayılı kesri bileşik kesre çevirme
        op = tam_sec(rng, negatif=0.15)
        bilesik = tam_cevir(op, adimlar)
        sonuc = Fraction(*bilesik)
        sade_adimi(bilesik, adimlar)
        if rng.random() < 0.4:
            metin = yazim.op(op, False)
            soru = rng.choice(CUMLE["cevir"]).replace("{m|i}", rakam_eki(metin, rakam_okunus(op), "i")).replace("{m}", metin)
            okunuslar = []
        else:
            soru, okunuslar = doldur(rng.choice(CUMLE["cevir"]).replace("{m", "{a"), {"a": op}, rng, True, yazim)
        return soru, okunuslar, f"İşlem: {op_rakam_baslik(op)}", adimlar, str(sonuc), tam_ascii(op)
    if r < 0.5:
        # Tam sayılı kesirlerle tek işlem: biri ya da ikisi tam sayılı
        tur = rng.choice(tuple(ISARET))
        iki_tam = r >= 0.31
        a = tam_sec(rng)
        b = tam_sec(rng, buyuk=6) if iki_tam else kesir_sec(rng, sifir=tur != "div")
        if b[0] == "k" and b[1] == 0 and tur == "div":
            b = ("k", 1, b[2])
        sol, sag = (a, b) if iki_tam or rng.random() < 0.56 else (b, a)
        degerler = []
        for op in (sol, sag):
            degerler.append(tam_cevir(op, adimlar) if op[0] == "t" else op[1:])
        if adimlar:
            adimlar.append(("Bileşik kesirlerle işlemi yap.", None))
        sonuc = dort_islem(tur, degerler[0], degerler[1], adimlar)
        ifade = f"{op_ascii(sol)} {ASCII[ISARET[tur]]} {op_ascii(sag)}"
        baslik = f"İşlem: {baslik_ikili(sol, ISARET[tur], sag)}"
        soru, okunuslar, sembolik = ikili_soru(tur, sol, sag, rng)
        if not sembolik and rng.random() < 0.35:
            soru = soru.rstrip(".") + rng.choice(TAM_EK)
        return soru, okunuslar, baslik, adimlar, str(sonuc), ifade
    if rng.random() < 0.6:
        return zincir(rng)
    # Üç kesirli ifade (rakamla)
    yazim.ifade_bicimi(rng)
    tur = rng.choice(tuple(ISARET))
    isaret = ISARET[tur]
    a, b, c = (kesir_sec(rng, sifir=False) for _ in range(3))
    if rng.random() < 0.55:
        ilk = rng.choice(("add", "sub", "mul"))
        ilk_isaret = ISARET[ilk]
        ifade = f"({op_ascii(a)} {ASCII[ilk_isaret]} {op_ascii(b)}) {ASCII[isaret]} {op_ascii(c)}"
        baslik = f"({baslik_ikili(a, ilk_isaret, b)}) {isaret} " + (f"({op_ascii_goster(c)})" if isaret == "÷" else op_baslik(c))
        c_yazi = f"({yazim.op(c, False)})" if yazim.bolme_parantezi(isaret) else yazim.op(c)
        gorunen = f"({yazim.ikili(a, ilk_isaret, b)}){' ' if yazim.bosluk else ''}" \
                  f"{yazim.isaret(isaret)}{' ' if yazim.bosluk else ''}{c_yazi}"
        adimlar.append(("Önce parantezin içindeki işlemi yap.", None))
        ara = dort_islem(ilk, a[1:], b[1:], adimlar)
        sol, sag = cift(ara), c[1:]
    else:
        ilk = rng.choice(("mul", "div"))
        tur = rng.choice(("add", "sub"))
        isaret = ISARET[tur]
        ifade = f"{op_ascii(a)} {ASCII[isaret]} {op_ascii(b)} {ASCII[ISARET[ilk]]} {op_ascii(c)}"
        baslik = f"{op_baslik(a)} {isaret} " + (f"({baslik_ikili(b, ISARET[ilk], c)})" if ilk == "div" else baslik_ikili(b, ISARET[ilk], c))
        ara_yazi = yazim.ikili(b, ISARET[ilk], c)
        if yazim.bolme_parantezi(ISARET[ilk]):
            ara_yazi = f"({ara_yazi})"
        bos = " " if yazim.bosluk else ""
        gorunen = f"{yazim.op(a)}{bos}{yazim.isaret(isaret)}{bos}{ara_yazi}"
        adimlar.append(("İşlem önceliğine göre önce çarpma veya bölmeyi yap.", None))
        ara = dort_islem(ilk, b[1:], c[1:], adimlar)
        sol, sag = a[1:], cift(ara)
    adimlar.append(("Bulduğun ara sonucu yerine koy ve kalan işlemi yap.",
                    [f"{ifade.replace('*', '×').replace(' / ', ' ÷ ')} = {ikili(sol, isaret, sag)}"]))
    sonuc = dort_islem(tur, sol, sag, adimlar)
    soru = ifade_sorusu("mixed", gorunen, rng, yazim)
    return soru, [], f"İşlem: {baslik}", adimlar, str(sonuc), ifade


def p_goster(op):
    return f"({op_ascii_goster(op)})"


def zincir(rng, gizli_sifir=False):
    """Üç işlenenli zincir: sol = (a o1 b) o2 c, sag = a o2 (b o1 c). Cümleyle ya da ifadeyle sorulur."""
    while True:
        adimlar = []
        if gizli_sifir:
            anahtar = ("sag", "÷", "-")
            yon, o1, o2 = "sag", "-", "÷"
            a = kesir_sec(rng, sifir=False)
            b = kesir_sec(rng, sifir=False)
            k = rng.choice([2, 3, 4, 5])
            c = ("k", b[1] * k, b[2] * k) if rng.random() < 0.7 else b
            if rng.random() < 0.5:
                b, c = c, b
        else:
            anahtar = rng.choice(list(ZINCIR))
            # Anahtar: sol için (sol, iç, dış), sağ için (sag, dış, iç).
            yon = anahtar[0]
            o1, o2 = (anahtar[1], anahtar[2]) if yon == "sol" else (anahtar[2], anahtar[1])
            a, b, c = (kesir_sec(rng, sifir=False) for _ in range(3))
            if rng.random() < 0.3:
                hangi = rng.choice("abc")
                tam = tam_sec(rng, negatif=0.1, buyuk=5)
                a, b, c = (tam if h == hangi else op for h, op in zip("abc", (a, b, c)))
        ops = {"a": a, "b": b, "c": c}
        degerler = {h: (tam_cevir(op, adimlar) if op[0] == "t" else op[1:]) for h, op in ops.items()}
        ic_sol, ic_sag = ("a", "b") if yon == "sol" else ("b", "c")
        adimlar.append(("Önce parantezin içindeki işlemi yap.", None))
        ara = dort_islem(ISARET_TUR[o1], degerler[ic_sol], degerler[ic_sag], adimlar)
        A, B, C = (op_ascii(ops[h]) for h in "abc")
        if yon == "sol":
            ifade = f"({A} {ASCII_ISARET[o1]} {B}) {ASCII_ISARET[o2]} {C}"
            baslik = f"İşlem: ({p_goster(a)} {o1} {p_goster(b)}) {o2} {p_goster(c)}"
            sol_d, sag_d = cift(ara), degerler["c"]
        else:
            ifade = f"{A} {ASCII_ISARET[o2]} ({B} {ASCII_ISARET[o1]} {C})"
            baslik = f"İşlem: {p_goster(a)} {o2} ({p_goster(b)} {o1} {p_goster(c)})"
            sol_d, sag_d = degerler["a"], cift(ara)
        if (o2 == "÷" and sag_d[0] == 0) != gizli_sifir:
            continue
        guzel = ifade.replace(" * ", " × ").replace(" / ", " ÷ ")
        if gizli_sifir:
            adimlar.append(("Bölen 0 çıktı. Bir sayıyı 0'a bölmek tanımsızdır.", None))
            sonuc = "tanımsız"
        else:
            adimlar.append(("Bulduğun ara sonucu yerine koy ve kalan işlemi yap.",
                            [f"{guzel} = {ikili(sol_d, o2, sag_d)}"]))
            sonuc = str(dort_islem(ISARET_TUR[o2], sol_d, sag_d, adimlar))
        yazim = Yazim(rng)
        okunuslar = []
        if rng.random() < 0.6:
            soru, okunuslar = doldur(rng.choice(ZINCIR[anahtar]), ops, rng, rng.random() < 0.5, yazim)
        else:
            yazim.ifade_bicimi(rng)
            bos = " " if yazim.bosluk else ""
            bolu_par = yazim.bolme_parantezi(o2)
            if yon == "sol":
                c_yazi = f"({yazim.op(c, False)})" if bolu_par else yazim.op(c)
                gorunen = f"({yazim.ikili(a, o1, b)}){bos}{yazim.isaret(o2)}{bos}{c_yazi}"
            else:
                a_yazi = f"({yazim.op(a, False)})" if bolu_par else yazim.op(a)
                gorunen = f"{a_yazi}{bos}{yazim.isaret(o2)}{bos}({yazim.ikili(b, o1, c)})"
            soru = ifade_sorusu("invalid" if gizli_sifir else "mixed", gorunen, rng, yazim)
        return soru, okunuslar, baslik, adimlar, sonuc, ifade


def ornek_sozel(tur, rng):
    adimlar = []
    sol = kesir_sec(rng, basit=True)
    sag = kesir_sec(rng, basit=True)
    if rng.random() < 0.2:
        if rng.random() < 0.5:
            sol = tam_sec(rng, negatif=0, buyuk=4)
        else:
            sag = tam_sec(rng, negatif=0, buyuk=3)
    if tur == "word_sub" and deger(sol) < deger(sag):
        sol, sag = sag, sol
    if tur == "word_sub" and deger(sol) == deger(sag):
        sol = ("k", sol[1] + sol[2], sol[2]) if sol[0] == "k" else ("t", sol[1] + 1, *sol[2:])
    adimlar.append((KELIME_ADIMI[tur], None))
    degerler = [tam_cevir(op, adimlar) if op[0] == "t" else op[1:] for op in (sol, sag)]
    islem = KELIME_ISLEMI[tur]
    sonuc = dort_islem(islem, degerler[0], degerler[1], adimlar)
    yazim = Yazim(rng)
    soru, okunuslar = doldur(rng.choice(SOZEL[tur]), {"a": sol, "b": sag}, rng, rng.random() < 0.4, yazim)
    ifade = f"{op_ascii(sol)} {ASCII[ISARET[islem]]} {op_ascii(sag)}"
    return soru, okunuslar, "Soru: Kesir problemi", adimlar, str(sonuc), ifade


def ornek(tur, rng):
    if tur == "simplify":
        parca = ornek_sade(rng)
    elif tur == "compare":
        parca = ornek_kiyas(rng)
    elif tur == "invalid":
        parca = ornek_tanimsiz(rng)
    elif tur == "mixed":
        parca = ornek_karma(rng)
    elif tur in KELIME_ISLEMI:
        parca = ornek_sozel(tur, rng)
    else:
        parca = ornek_basit(tur, rng)
    soru, okunuslar, baslik, adimlar, sonuc, ifade = parca
    soru = bozum(soru, rng)
    metin = []
    okunuslar = [(m, op) for m, op in okunuslar if op is not None] if okunuslar else []
    if okunuslar:
        metin.append(okunus_satiri(okunuslar, soru))
    metin.append(baslik)
    for no, (aciklama, hesaplar) in enumerate(adimlar, 1):
        metin.append(f"{no}. {aciklama}")
        for hesap in hesaplar or []:
            metin.append(f"   {hesap}")
    metin.append(f"Sonuç: {sonuc}")
    return {
        "messages": [{"role": "user", "content": soru}, {"role": "assistant", "content": "\n".join(metin)}],
        "meta": {"kind": tur, "expression": ifade, "answer": sonuc},
    }


def kota(toplam):
    kotalar = {tur: toplam * oran // 100 for tur, oran in ORANLAR.items()}
    kalan = toplam - sum(kotalar.values())
    for tur in sorted(ORANLAR, key=lambda t: toplam * ORANLAR[t] % 100, reverse=True)[:kalan]:
        kotalar[tur] += 1
    return kotalar


def bolum(ad, toplam, rng, gorulen, sorular):
    kotalar = kota(toplam)
    mevcut = Counter()
    veriler = []
    for tur, hedef in kotalar.items():
        denemeler = 0
        while mevcut[tur] < hedef:
            denemeler += 1
            if denemeler > max(500, hedef * 100):
                raise RuntimeError(f"{ad}/{tur}: benzersiz örnek kotası dolmadı")
            veri = ornek(tur, rng)
            anahtar = canonical_key(tur, veri["meta"]["expression"])
            soru = veri["messages"][0]["content"]
            if anahtar in gorulen or soru in sorular:
                continue
            gorulen.add(anahtar)
            sorular.add(soru)
            veriler.append(veri)
            mevcut[tur] += 1
    rng.shuffle(veriler)
    for no, veri in enumerate(veriler, 1):
        veri["meta"]["id"] = f"{ad}-{no:05d}"
    return veriler


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--out", type=Path, default=ROOT / "data" / "v13")
    cli.add_argument("--dislanan", type=Path, nargs="*", default=[
        ROOT / "data" / "gercek.jsonl", ROOT / "data" / "gercek2.jsonl", ROOT / "data" / "gercek3.jsonl",
        ROOT / "data" / "gercek4.jsonl", ROOT / "data" / "test.jsonl",
        ROOT / "data" / "v11" / "test.jsonl", ROOT / "data" / "yoklama.jsonl"])
    cli.add_argument("--seed", type=int, default=13)
    cli.add_argument("--train", type=int, default=18000)
    cli.add_argument("--val", type=int, default=500)
    cli.add_argument("--test", type=int, default=600)
    opts = cli.parse_args()
    gorulen, sorular = set(), set()
    for yol in opts.dislanan:
        for r in oku(yol):
            gorulen.add(canonical_key(r["meta"]["kind"], r["meta"]["expression"]))
            sorular.add(r["messages"][0]["content"])
    rng = random.Random(opts.seed)
    opts.out.mkdir(parents=True, exist_ok=True)
    for ad, toplam in (("test", opts.test), ("val", opts.val), ("train", opts.train)):
        veriler = bolum(ad, toplam, rng, gorulen, sorular)
        yol = opts.out / f"{ad}.jsonl"
        with open(yol, "w", encoding="utf-8", newline="\n") as dosya:
            for veri in veriler:
                dosya.write(json.dumps(veri, ensure_ascii=False) + "\n")
        print(f"{ad}: {len(veriler)} soru → {yol}")


if __name__ == "__main__":
    main()
