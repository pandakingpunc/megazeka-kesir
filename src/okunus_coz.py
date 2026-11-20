"""Türkçe sözle yazılmış sayı ve kesirleri değere çevirir. Üreticiden bağımsız denetim içindir."""

import re
from fractions import Fraction

KATLAMA = str.maketrans("çğıöşüâ", "cgiosua")
BIR = {"sifir": 0, "bir": 1, "iki": 2, "uc": 3, "dort": 4, "bes": 5, "alti": 6, "yedi": 7, "sekiz": 8, "dokuz": 9}
ON = {"on": 10, "yirmi": 20, "otuz": 30, "kirk": 40, "elli": 50, "altmis": 60, "yetmis": 70, "seksen": 80, "doksan": 90}
KELIMELER = {**BIR, **ON, "yuz": 100, "bin": 1000}
BULUNMA = re.compile(r"^(.*?)(?:da|de|ta|te)$")


def katla(metin):
    return metin.replace("İ", "i").replace("I", "ı").lower().translate(KATLAMA)


def tamsayi(kelimeler):
    if not kelimeler:
        raise ValueError("boş sayı")
    toplam = grup = 0
    for k in kelimeler:
        if k not in KELIMELER:
            raise ValueError(f"bilinmeyen sayı kelimesi: {k}")
        v = KELIMELER[k]
        if v == 1000:
            toplam += (grup or 1) * 1000
            grup = 0
        elif v == 100:
            grup = (grup or 1) * 100
        else:
            grup += v
    return toplam + grup


def bulunma_sayisi(kelimeler):
    """Son kelimesi bulunma ekli ('dörtte') sayı grubunu çözer."""
    m = BULUNMA.match(kelimeler[-1])
    if not m or m[1] not in KELIMELER:
        raise ValueError(f"bulunma ekli payda değil: {kelimeler[-1]}")
    return tamsayi(kelimeler[:-1] + [m[1]])


def kesir(kelimeler):
    if kelimeler == ["yarim"]:
        return Fraction(1, 2)
    if kelimeler == ["ceyrek"]:
        return Fraction(1, 4)
    if "bolu" in kelimeler:
        i = kelimeler.index("bolu")
        pay, payda = tamsayi(kelimeler[:i]), tamsayi(kelimeler[i + 1:])
        if payda == 0:
            return ("tanımsız", pay)
        return Fraction(pay, payda)
    for i, k in enumerate(kelimeler):
        m = BULUNMA.match(k)
        if m and m[1] in KELIMELER and i + 1 < len(kelimeler):
            return Fraction(tamsayi(kelimeler[i + 1:]), bulunma_sayisi(kelimeler[:i + 1]))
    return Fraction(tamsayi(kelimeler))


def coz(metin):
    """'eksi üç tam dörtte bir' → Fraction(-13, 4). Paydası 0 olan kesirde ('tanımsız', pay)."""
    kelimeler = katla(metin).split()
    isaret = 1
    if kelimeler and kelimeler[0] == "eksi":
        isaret, kelimeler = -1, kelimeler[1:]
    if "tam" in kelimeler:
        i = kelimeler.index("tam")
        return isaret * (tamsayi(kelimeler[:i]) + kesir(kelimeler[i + 1:]))
    if kelimeler and kelimeler[-1] == "bucuk":
        return isaret * (tamsayi(kelimeler[:-1]) + Fraction(1, 2))
    deger = kesir(kelimeler)
    if isinstance(deger, tuple):
        return ("tanımsız", isaret * deger[1])
    return isaret * deger


def rakam_coz(metin):
    """'3 tam 2/15', '-3 tam 2/15', '17/19', '-96', '5/0' → değer."""
    m = re.fullmatch(r"(-?)(\d+) tam (\d+)/(\d+)", metin)
    if m:
        return (-1 if m[1] else 1) * (int(m[2]) + Fraction(int(m[3]), int(m[4])))
    m = re.fullmatch(r"(-?\d+)/0", metin)
    if m:
        return ("tanımsız", int(m[1]))
    m = re.fullmatch(r"(-?\d+)(?:/(\d+))?", metin)
    if not m:
        raise ValueError(f"rakamlı okunuş çözülemedi: {metin}")
    return Fraction(int(m[1]), int(m[2] or 1))
