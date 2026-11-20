"""Veri üreticisinden bağımsız tam kesir aritmetiği ve test anahtarları."""

import ast
import json
import operator
from fractions import Fraction

ISLEMLER = {
    ast.Add: (operator.add, "+"),
    ast.Sub: (operator.sub, "-"),
    ast.Mult: (operator.mul, "*"),
    ast.Div: (operator.truediv, "/"),
}
GECERSIZ = "tanımsız"
CEVIR = str.maketrans({"−": "-", "×": "*", "·": "*", "÷": "/"})


def oku(yol):
    with open(yol, encoding="utf-8") as dosya:
        for satir in dosya:
            if satir.strip():
                yield json.loads(satir)


def agac(metin):
    return ast.parse(metin.translate(CEVIR).strip(), mode="eval").body


def deger(dugum):
    if isinstance(dugum, ast.Constant) and type(dugum.value) is int:
        return Fraction(dugum.value)
    if isinstance(dugum, ast.UnaryOp) and isinstance(dugum.op, (ast.UAdd, ast.USub)):
        isaret = -1 if isinstance(dugum.op, ast.USub) else 1
        return isaret * deger(dugum.operand)
    if isinstance(dugum, ast.BinOp) and type(dugum.op) in ISLEMLER:
        islem, _ = ISLEMLER[type(dugum.op)]
        return islem(deger(dugum.left), deger(dugum.right))
    raise ValueError(f"Desteklenmeyen ifade: {ast.dump(dugum)}")


def sayi(metin):
    return deger(agac(metin))


def karsilastir(sol, sag):
    return "<" if sol < sag else ">" if sol > sag else "="


def beklenen(ifade):
    if "|" in ifade:
        sol, sag = ifade.split("|")
        return karsilastir(sayi(sol), sayi(sag))
    try:
        return str(sayi(ifade))
    except ZeroDivisionError:
        return GECERSIZ


def tamsayi_yazimi(dugum):
    return (
        isinstance(dugum, ast.Constant) and type(dugum.value) is int
        or isinstance(dugum, ast.UnaryOp) and tamsayi_yazimi(dugum.operand)
    )


def kesir_yazimi(dugum):
    if isinstance(dugum, ast.UnaryOp):
        return kesir_yazimi(dugum.operand)
    return (
        isinstance(dugum, ast.BinOp) and isinstance(dugum.op, ast.Div)
        and tamsayi_yazimi(dugum.left) and tamsayi_yazimi(dugum.right)
    )


def tam_sayili_yazimi(dugum):
    if isinstance(dugum, ast.UnaryOp):
        return tam_sayili_yazimi(dugum.operand)
    return (
        isinstance(dugum, ast.BinOp) and isinstance(dugum.op, ast.Add)
        and tamsayi_yazimi(dugum.left) and kesir_yazimi(dugum.right)
    )


def yapi(dugum):
    # Eşdeğer kesir yazımları ve tam sayılı gösterimler aynı operandı belirtir.
    if tamsayi_yazimi(dugum) or kesir_yazimi(dugum) or tam_sayili_yazimi(dugum):
        try:
            return str(deger(dugum))
        except ZeroDivisionError:
            if isinstance(dugum, ast.BinOp):
                return f"{deger(dugum.left)}/0"
    if isinstance(dugum, ast.UnaryOp):
        return f"{type(dugum.op).__name__}({yapi(dugum.operand)})"
    _, sembol = ISLEMLER[type(dugum.op)]
    sol, sag = yapi(dugum.left), yapi(dugum.right)
    if sembol in {"+", "*"}:
        sol, sag = sorted((sol, sag))
    return f"({sol}{sembol}{sag})"


def canonical_key(tur, ifade):
    if "|" in ifade:
        sol, sag = sorted(yapi(agac(parca)) for parca in ifade.split("|"))
        return f"kıyas:{sol}|{sag}"
    dugum = agac(ifade)
    if tur == "simplify" and kesir_yazimi(dugum):
        # 2/4 ve 4/8 farklı sadeleştirme sorularıdır. Eksi işaretinin yeri yeterli fark değildir.
        isaret = 1
        while isinstance(dugum, ast.UnaryOp):
            if isinstance(dugum.op, ast.USub):
                isaret *= -1
            dugum = dugum.operand
        pay, payda = int(deger(dugum.left)) * isaret, int(deger(dugum.right))
        if payda < 0:
            pay, payda = -pay, -payda
        return f"sadeleştir:{pay}/{payda}"
    return f"işlem:{yapi(dugum)}"

