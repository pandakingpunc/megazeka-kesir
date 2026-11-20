"""Türkçe kesir çözümü için deterministik, denetlenebilir SFT verisi üretir."""

import argparse
import json
import math
import random
from collections import Counter
from fractions import Fraction
from pathlib import Path

from matematik import canonical_key, oku
from sorular import BASIC_PROMPTS, SOZEL_PROMPTS

ROOT = Path(__file__).resolve().parents[1]
ORANLAR = {
    "simplify": 10, "compare": 10, "add": 13, "sub": 12, "mul": 12, "div": 12,
    "mixed": 16, "invalid": 3, "word_add": 3, "word_sub": 3, "word_of": 3, "word_div": 3,
}
ISARET = {"add": "+", "sub": "-", "mul": "×", "div": "÷"}
KELIME_ISLEMI = {"word_add": "add", "word_sub": "sub", "word_of": "mul", "word_div": "div"}
KELIME_ADIMI = {
    "word_add": "Toplam miktarı bulmak için iki kesri topla.",
    "word_sub": "Kalan miktarı bulmak için kullanılan kesri başlangıç miktarından çıkar.",
    "word_of": "Bir miktarın belli bir kesrini bulmak için miktarı verilen kesirle çarp.",
    "word_div": "Porsiyon sayısını bulmak için toplam miktarı bir porsiyonun miktarına böl.",
}


def yaz(kesir):
    pay, payda = kesir
    if payda < 0:
        return f"{pay}/({payda})"
    return f"{pay}/{payda}" if payda != 1 else str(pay)


def oran(kesir):
    return Fraction(*kesir)


def cift(deger):
    return deger.numerator, deger.denominator


def parantez(kesir):
    return f"({yaz(kesir)})"


def ikili(sol, isaret, sag):
    return f"{parantez(sol)} {isaret} {parantez(sag)}"


def goster(sol, isaret, sag):
    sol_metin = parantez(sol) if isaret == "÷" or sol[0] < 0 else yaz(sol)
    sag_metin = parantez(sag) if isaret == "÷" or sag[0] < 0 else yaz(sag)
    return f"{sol_metin} {isaret} {sag_metin}"


def sade_adimi(ham, adimlar):
    p, d = ham
    g = math.gcd(p, d)
    sonuc = oran(ham)
    if d < 0:
        adimlar.append(("Pay ve paydayı -1 ile çarparak paydayı pozitif yap.", f"{yaz(ham)} = {yaz((-p, -d))}"))
        p, d = -p, -d
    if g > 1:
        adimlar.append((
            f"Payı ve paydayı ortak bölenleri olan {g} ile böl.",
            f"{yaz((p, d))} = ({p} ÷ {g})/({d} ÷ {g}) = {sonuc}",
        ))
    return sonuc


def paylari_esitle(sol, sag):
    d = math.lcm(sol[1], sag[1])
    carp_sol, carp_sag = d // sol[1], d // sag[1]
    return d, carp_sol, carp_sag, sol[0] * carp_sol, sag[0] * carp_sag


def dort_islem(tur, sol, sag, adimlar):
    a, b = sol
    c, d = sag
    ars = ISARET[tur]
    ilk = ikili(sol, ars, sag)
    if tur in {"add", "sub"}:
        payda, sol_carpan, sag_carpan, sol_pay, sag_pay = paylari_esitle(sol, sag)
        ham_pay = sol_pay + sag_pay if tur == "add" else sol_pay - sag_pay
        if b != d:
            adimlar.append((
                f"Ortak payda {payda}. İlk kesrin pay ve paydasını {sol_carpan} ile, "
                f"ikincininkini {sag_carpan} ile çarp.",
                f"{ilk} = {ikili((sol_pay, payda), ars, (sag_pay, payda))}",
            ))
        eylem = "topla" if tur == "add" else "çıkar"
        adimlar.append((
            f"Payları {eylem}, ortak paydayı koru.",
            f"{ikili((sol_pay, payda), ars, (sag_pay, payda))}"
            f" = ({sol_pay} {ars} ({sag_pay}))/{payda} = {yaz((ham_pay, payda))}",
        ))
        return sade_adimi((ham_pay, payda), adimlar)
    if tur == "div":
        ters = (-d, -c) if c < 0 else (d, c)
        adimlar.append((
            "Bölen kesrin tersini al ve çarp."
            + (" Ters kesrin eksi işaretini paya yaz." if c < 0 else ""),
            f"{ilk} = {ikili(sol, '×', ters)}",
        ))
        c, d = ters
        sag = ters
    adimlar.append((
        "Payları kendi arasında, paydaları kendi arasında çarp.",
        f"{ikili(sol, '×', sag)} = ({a} × ({c}))/({b} × {d}) = {yaz((a*c, b*d))}",
    ))
    return sade_adimi((a * c, b * d), adimlar)


def kesir_sec(rng, pozitif=False, basit=False, sifir=True):
    # Küçük ve ortak bölenli paydaları sık göster, büyük paydaları da örnekle.
    d = rng.randint(2, 12 if rng.random() < 0.67 else 40)
    if basit:
        return rng.randint(1, d - 1), d
    a = rng.randint(0 if sifir else 1, 2 * d + 8)
    if not pozitif and a and rng.random() < 0.26:
        a = -a
    return a, d


def ifade_ve_adimlar(tur, rng):
    adimlar = []
    if tur == "simplify":
        d = rng.randint(2, 29)
        a = rng.randint(-3 * d, 3 * d)
        g = rng.choice([1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 12])
        if rng.random() < 0.06:
            d = -d
        ham = (a * g, d * g)
        sonuc = sade_adimi(ham, adimlar)
        if not adimlar:
            adimlar.append(("Pay ile paydanın en büyük ortak böleni 1, yani kesir en sade hâlinde.",
                             f"{yaz(ham)} = {sonuc}"))
        return yaz(ham), yaz(ham), str(sonuc), adimlar, None

    if tur == "invalid":
        sol = kesir_sec(rng, sifir=False)
        if rng.random() < 0.53:
            pay = rng.randint(-196, 196)
            ifade = f"{pay}/0"
            adimlar.append(("Payda 0 olduğu için bu kesir tanımsız.", None))
            return ifade, ifade, "tanımsız", adimlar, None
        sag = (0, rng.randint(2, 36))
        adimlar.append(("Bölen kesrin değeri 0. Bir sayıyı 0'a bölmek tanımsızdır.",
                         f"{yaz(sag)} = 0"))
        return ikili(sol, "/", sag), goster(sol, "÷", sag), "tanımsız", adimlar, None

    if tur == "compare":
        sol = kesir_sec(rng, sifir=False)
        secim = rng.random()
        if secim < 0.24:
            k = rng.randint(2, 8)
            sag = (sol[0] * k, sol[1] * k)
        elif secim < 0.46:
            sag = (sol[0] + rng.choice([-2, -1, 1, 2]), sol[1])
        else:
            sag = kesir_sec(rng)
        d, _, _, p, q = paylari_esitle(sol, sag)
        isaret = "<" if p < q else ">" if p > q else "="
        adimlar.append((f"Paydaları {d} olacak şekilde eşitle.", f"{yaz(sol)} = {yaz((p, d))}"))
        adimlar.append(("İkinci kesri de aynı paydada yaz.", f"{yaz(sag)} = {yaz((q, d))}"))
        adimlar.append((
            "Paydalar aynı olduğunda payları karşılaştır.",
            f"{yaz((p, d))} {isaret} {yaz((q, d))}",
        ))
        return f"{yaz(sol)}|{yaz(sag)}", f"{yaz(sol)} ve {yaz(sag)}", isaret, adimlar, None

    if tur == "mixed":
        return karmasik(rng, adimlar)

    sozel = tur in KELIME_ISLEMI
    if sozel:
        sol = kesir_sec(rng, basit=True)
        sag = kesir_sec(rng, basit=True)
        if tur == "word_sub" and oran(sol) < oran(sag):
            sol, sag = sag, sol
        adimlar.append((KELIME_ADIMI[tur], None))
    else:
        sol = kesir_sec(rng)
        sag = kesir_sec(rng, sifir=tur != "div")
        if tur in {"add", "sub"} and rng.random() < 0.2:
            sag = sag[0], sol[1]
    basit_tur = KELIME_ISLEMI.get(tur, tur)
    isaret = ISARET[basit_tur]
    sonuc = dort_islem(basit_tur, sol, sag, adimlar)
    ifade = ikili(sol, {"×": "*", "÷": "/"}.get(isaret, isaret), sag)
    return ifade, goster(sol, isaret, sag), str(sonuc), adimlar, (sol, sag) if sozel else None


def karmasik(rng, adimlar):
    tur = rng.choice(tuple(ISARET))
    isaret = ISARET[tur]
    ascii_isaret = isaret.translate(str.maketrans("×÷", "*/"))
    a = kesir_sec(rng, sifir=False)
    b = kesir_sec(rng, sifir=False)
    if rng.random() < 0.48:
        # Tam sayılı kesirde kesir kısmı her zaman pozitif ve birden küçük.
        pay, payda = kesir_sec(rng, basit=True)
        tam = rng.choice([-1, 1, 1, 1]) * rng.randint(1, 9)
        birlesik_pay = abs(tam) * payda + pay
        bilesik = (birlesik_pay if tam > 0 else -birlesik_pay, payda)
        ters_isaret = "-" if tam < 0 else ""
        tam_ifade = f"{ters_isaret}({abs(tam)}+{pay}/{payda})"
        tam_goster = f"({tam} tam {pay}/{payda})"
        if rng.random() < 0.56:
            ifade = f"({tam_ifade}) {ascii_isaret} {parantez(a)}"
            gorunen = f"{tam_goster} {isaret} {parantez(a)}"
            sol, sag = bilesik, a
        else:
            ifade = f"{parantez(a)} {ascii_isaret} ({tam_ifade})"
            gorunen = f"{parantez(a)} {isaret} {tam_goster}"
            sol, sag = a, bilesik
        adimlar.append((
            "Tam kısmın mutlak değerini paydayla çarp, kesrin payını ekle ve sonuca eksi işareti koy."
            if tam < 0 else "Tam kısmı paydayla çarp ve kesrin payını ekle.",
            f"{tam_ifade} = {ters_isaret}(({abs(tam)} × {payda} + {pay})/{payda}) = {yaz(bilesik)}",
        ))
    else:
        c = kesir_sec(rng, sifir=False)
        if rng.random() < 0.55:
            ilk = rng.choice(("add", "sub", "mul"))
            ilk_isaret = ISARET[ilk]
            ilk_ascii = "*" if ilk == "mul" else ilk_isaret
            ifade = f"({ikili(a, ilk_ascii, b)}) {ascii_isaret} {parantez(c)}"
            gorunen = f"({goster(a, ilk_isaret, b)}) {isaret} {parantez(c)}"
            adimlar.append(("Önce parantezin içindeki işlemi yap.", None))
            ara = dort_islem(ilk, a, b, adimlar)
            sol, sag = cift(ara), c
        else:
            ilk = rng.choice(("mul", "div"))
            tur = rng.choice(("add", "sub"))
            isaret = ISARET[tur]
            ifade = f"{parantez(a)} {isaret} {ikili(b, '*' if ilk == 'mul' else '/', c)}"
            gorunen = f"{parantez(a)} {isaret} {goster(b, ISARET[ilk], c)}"
            adimlar.append(("İşlem önceliğine göre önce çarpma veya bölmeyi yap.", None))
            ara = dort_islem(ilk, b, c, adimlar)
            sol, sag = a, cift(ara)
        adimlar.append(("Bulduğun ara sonucu yerine koy ve kalan işlemi yap.",
                         f"{ifade} = {ikili(sol, isaret, sag)}"))
    sonuc = dort_islem(tur, sol, sag, adimlar)
    return ifade, gorunen, str(sonuc), adimlar, None


def bicim(gorunen, tur, rng):
    kip = rng.randrange(5)
    if kip == 1:
        return gorunen.replace("-", "−")
    if kip == 2:
        return gorunen.replace("×", "*")
    if kip == 3 and tur not in {"mixed", "compare"}:
        return gorunen.replace(" ", "")
    if kip == 4:
        return gorunen.replace("×", "·").replace("-", "−")
    return gorunen


def ornek(tur, rng):
    ifade, gorunen, sonuc, adimlar, sozel = ifade_ve_adimlar(tur, rng)
    if sozel:
        sol, sag = sozel
        soru = rng.choice(SOZEL_PROMPTS[tur]).format(a=yaz(sol), b=yaz(sag))
        baslik = "Soru: Kesir problemi"
    else:
        soru = rng.choice(BASIC_PROMPTS[tur]).format(islem=bicim(gorunen, tur, rng))
        baslik = f"{'Kesir' if tur == 'simplify' else 'İşlem'}: {gorunen}"
    metin = [baslik]
    for no, (aciklama, hesap) in enumerate(adimlar, 1):
        metin.append(f"{no}. {aciklama}")
        if hesap:
            metin.append(f"   {hesap}")
    metin.append(f"Sonuç: {sonuc}")
    return {
        "messages": [{"role": "user", "content": soru}, {"role": "assistant", "content": "\n".join(metin)}],
        "meta": {"kind": tur, "expression": ifade, "answer": sonuc},
    }


def kota(toplam):
    kotalar = {tur: toplam * oran // 100 for tur, oran in ORANLAR.items()}
    kalan = toplam - sum(kotalar.values())
    sirali = sorted(ORANLAR, key=lambda t: toplam * ORANLAR[t] % 100, reverse=True)
    for tur in sirali[:kalan]:
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
            meta = veri["meta"]
            anahtar = canonical_key(tur, meta["expression"])
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
    cli.add_argument("--out", type=Path, default=ROOT / "data")
    cli.add_argument("--gercek", type=Path, default=ROOT / "data" / "gercek.jsonl")
    cli.add_argument("--seed", type=int, default=7)
    cli.add_argument("--train", type=int, default=12000)
    cli.add_argument("--val", type=int, default=500)
    cli.add_argument("--test", type=int, default=600)
    opts = cli.parse_args()
    gercek = list(oku(opts.gercek))
    gorulen = {canonical_key(r["meta"]["kind"], r["meta"]["expression"]) for r in gercek}
    sorular = {r["messages"][0]["content"] for r in gercek}
    rng = random.Random(opts.seed)
    opts.out.mkdir(parents=True, exist_ok=True)
    # Ölçüm kümelerine öncelik ver, sonra eğitimde denk soru çıkmasını engelle.
    for ad, toplam in (("test", opts.test), ("val", opts.val), ("train", opts.train)):
        veriler = bolum(ad, toplam, rng, gorulen, sorular)
        yol = opts.out / f"{ad}.jsonl"
        with open(yol, "w", encoding="utf-8", newline="\n") as dosya:
            for veri in veriler:
                dosya.write(json.dumps(veri, ensure_ascii=False) + "\n")
        print(f"{ad}: {len(veriler)} soru → {yol}")


if __name__ == "__main__":
    main()

