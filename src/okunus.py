"""Sayıları ve kesirleri Türkçe sözle yazar, hâl eklerini ses uyumuna göre ekler."""

BIRLER = ["sıfır", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
KALIN = set("aıou")
INCE = set("eiöü")
UNLU = KALIN | INCE
SERT = set("fstkçşhp")
DORTLU = {"a": "ı", "ı": "ı", "o": "u", "u": "u", "e": "i", "i": "i", "ö": "ü", "ü": "ü"}
# Sayı adlarında yalnız "dört" ünlüyle başlayan ek alınca yumuşar.
YUMUSAMA = {"dört": "dörd"}


def soz(n):
    """0-999999 arası tam sayıyı Türkçe sözle yazar."""
    if n < 0:
        return "eksi " + soz(-n)
    if n < 10:
        return BIRLER[n]
    parcalar = []
    binler, n = divmod(n, 1000)
    if binler:
        parcalar.append("bin" if binler == 1 else f"{soz(binler)} bin")
    yuzler, n = divmod(n, 100)
    if yuzler:
        parcalar.append("yüz" if yuzler == 1 else f"{BIRLER[yuzler]} yüz")
    onlar, birler = divmod(n, 10)
    if onlar:
        parcalar.append(ONLAR[onlar])
    if birler:
        parcalar.append(BIRLER[birler])
    return " ".join(parcalar)


def son_unlu(kelime):
    for harf in reversed(kelime):
        if harf in UNLU:
            return harf
    return "e"


def ek(metin, hal):
    """Metnin son kelimesine hâl eki ekler: a (yönelme), i (belirtme), dan, de, in, le."""
    govde, _, son = metin.rpartition(" ")
    on = govde + " " if govde else ""
    unlu = son_unlu(son)
    kalin = unlu in KALIN
    unluyle_biter = son[-1] in UNLU
    sert = son[-1] in SERT
    if hal in {"a", "i", "in"} and not unluyle_biter:
        son = YUMUSAMA.get(son, son)
    if hal == "a":
        eki = ("y" if unluyle_biter else "") + ("a" if kalin else "e")
    elif hal == "i":
        eki = ("y" if unluyle_biter else "") + DORTLU[unlu]
    elif hal == "in":
        eki = ("n" if unluyle_biter else "") + DORTLU[unlu] + "n"
    elif hal in {"dan", "de"}:
        eki = ("t" if sert else "d") + ("a" if kalin else "e") + ("n" if hal == "dan" else "")
    elif hal == "le":
        eki = ("y" if unluyle_biter else "") + ("la" if kalin else "le")
    else:
        raise ValueError(hal)
    return on + son + eki


def kesir_soz(pay, payda, kip):
    """kip: 'bolu' → 'üç bölü dört', 'de' → 'dörtte üç'."""
    eksi = "eksi " if (pay < 0) != (payda < 0) and pay != 0 else ""
    pay, payda = abs(pay), abs(payda)
    if payda == 1:
        return eksi + soz(pay)
    if kip == "bolu":
        return f"{eksi}{soz(pay)} bölü {soz(payda)}"
    return f"{eksi}{ek(soz(payda), 'de')} {soz(pay)}"


def tam_sayili_soz(tam, pay, payda, kip):
    eksi = "eksi " if tam < 0 else ""
    if kip == "bucuk" and (pay, payda) == (1, 2):
        return f"{eksi}{soz(abs(tam))} buçuk"
    return f"{eksi}{soz(abs(tam))} tam {kesir_soz(pay, payda, 'de' if kip == 'bucuk' else kip)}"


def rakam_eki(yazi, okunus, hal):
    """'5/12' gibi rakamla yazılmış sayıya okunuşuna göre kesme işaretiyle ek getirir."""
    tam = ek(okunus, hal)
    return f"{yazi}'{tam[len(okunus):]}"
