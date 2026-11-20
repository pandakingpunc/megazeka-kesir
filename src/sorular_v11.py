"""v1.1 soru şablonları. {a} gibi yuvalar işlenen, {a|a} gibi yuvalar hâl ekli işlenendir.

Hâl kısaltmaları: a = yönelme (-e), i = belirtme (-i), dan = ayrılma, in = tamlayan, le = vasıta.
"""

from sorular import BASIC_PROMPTS, SOZEL_PROMPTS

CUMLE = {
    "simplify": (
        "{a|i} sadeleştir.",
        "{a|i} en sade hâline getir.",
        "{a} kesrini sadeleştirir misin?",
        "{a} sadeleşince hangi kesir olur?",
        "{a|i} indirgenmiş biçimde yaz.",
        "{a} kesrinin en sade hâli ne?",
        "{a|i} pay ve paydasını ortak bölene bölerek sadeleştir.",
    ),
    "simplify_tarif": (
        "Payı {p}, paydası {q} olan kesri sadeleştir.",
        "Paydası {q}, payı {p} olan kesrin en sade hâli nedir?",
        "Bir kesrin payı {p}, paydası {q}. Bu kesri sade biçimde yaz.",
        "Pay {p}, payda {q}. Kesri sadeleştirip yaz.",
    ),
    "compare": (
        "{a} ile {b|i} karşılaştır. <, = veya > yaz.",
        "Hangisi büyük: {a} mı, {b} mı? Soldakini sağdakiyle <, = ya da > ile karşılaştır.",
        "Solda {a}, sağda {b} var. Araya <, = mi > mi gelir?",
        "{a}, {b|dan} büyük mü, küçük mü, eşit mi? <, = veya > ile cevapla.",
        "{a} ve {b} kesirlerini karşılaştırıp aralarına uygun işareti (<, =, >) koy.",
        "{a|i} {b|le} kıyasla: soldaki için <, = ya da > yaz.",
    ),
    "compare_bos": (
        "{a} {bos} {b}. Boşluğa <, = veya > işaretlerinden hangisi gelir?",
        "{a} {bos} {b} ifadesinde boş yere ne yazılır (<, =, >)?",
        "Boşluğu doldur: {a} {bos} {b}",
        "{a} {bos} {b} için doğru işaret <, = mi, > mi?",
    ),
    "add": (
        "{a|a} {b} ekle.",
        "{a|a} {b} eklersek kaç olur?",
        "{a} ile {b|i} topla.",
        "{a} artı {b} kaç eder?",
        "{a} ile {b|in} toplamı kaçtır?",
        "{a|le} {b|i} toplayınca ne çıkar?",
        "{a} ve {b} toplanırsa sonuç ne olur?",
    ),
    "sub": (
        "{a|dan} {b|i} çıkar.",
        "{a|dan} {b} çıkarılırsa ne kalır?",
        "{a} eksi {b} kaç eder?",
        "{a|dan} {b|i} çıkarınca sonuç ne olur?",
        "{a} ile {b} arasındaki farkı bul: {a|dan} {b|i} çıkar.",
        "{a|dan} {b} eksiltirsem kaç kalır?",
    ),
    "mul": (
        "{a} ile {b|i} çarp.",
        "{a} çarpı {b} kaç eder?",
        "{a} ile {b|in} çarpımı nedir?",
        "{a|i} {b} ile çarparsak sonuç ne olur?",
        "{a|in} {b} katı kaçtır?",
        "{a} kere {b} kaç?",
    ),
    "div": (
        "{a|i} {b|a} böl.",
        "{a|i} {b|a} bölünce ne çıkar?",
        "{a|in} {b|a} bölümü kaçtır?",
        "{a}, {b|in} kaç katıdır?",
        "{a|i} {b|a} bölersek sonuç kaç olur?",
        "{a} içinde kaç tane {b} var?",
    ),
    "invalid_kesir": (
        "{a} kesrinin değeri nedir?",
        "{a} diye bir sayı olur mu? Değeri ne?",
        "{a|i} hesapla.",
        "{a} tanımlı mı, değeri kaç?",
        "{a} kaç eder?",
    ),
    "cevir": (
        "{m|i} bileşik kesir olarak yaz.",
        "{m} tam sayılı kesrini bileşik kesre çevir.",
        "{m|i} tek bir kesir hâlinde yaz.",
        "{m} bileşik kesir olarak nasıl yazılır?",
        "{m} kaç bölü kaça eşittir? Bileşik kesir olarak yaz.",
        "{m|i} paydası aynı kalacak şekilde bileşik kesre dönüştür.",
    ),
}

# Tam sayılı kesirle yapılan işlemlerde sonuç bileşik kesir olarak istenir.
TAM_EK = (
    "",
    " Sonucu bileşik kesir olarak ver.",
    " Sonucu sade kesir olarak yaz.",
    "",
)

BOSLUK = ("__", "___", "[?]", "…", "( )", "□", "?", "...")

SOZEL_EK = {
    "word_add": (
        "Bir tencereye önce {a} litre su, sonra {b} litre su koydum. Tencerede kaç litre su oldu?",
        "Manavdan {a} kilo elma ve {b} kilo armut aldım. Toplam kaç kilo meyve aldım?",
        "Bir boyacı sabah {a} kutu, öğleden sonra {b} kutu boya kullandı. Gün boyunca kaç kutu boya kullandı?",
        "Bir şişede {a} litre süt, diğerinde {b} litre süt var. İki şişede toplam kaç litre süt var?",
        "Terzi bir elbise için {a} metre, bir etek için {b} metre kumaş kesti. Toplam kaç metre kumaş kesti?",
    ),
    "word_sub": (
        "Kavanozda {a} kilo bal vardı, {b} kilosunu yedik. Kavanozda kaç kilo bal kaldı?",
        "{a} metrelik kumaştan {b} metre kestim. Geriye kaç metre kumaş kaldı?",
        "Bidonda {a} litre zeytinyağı vardı. {b} litre kullanıldı. Bidonda ne kadar kaldı?",
        "Bir koşucu {a} kilometrelik parkurun {b} kilometresini koştu. Bitirmesine kaç kilometre kaldı?",
        "Bir haznede {a} litre su vardı, {b} litresi buharlaştı. Haznede ne kadar su kaldı?",
    ),
    "word_of": (
        "{a} kilo peynirin {b|i} kahvaltıda yedik. Kaç kilo peynir yedik?",
        "Bir depoda {a} ton kum var. Kumun {b} kadarı satıldı. Kaç ton kum satıldı?",
        "{a} litre ayranın {b|i} misafirlere ikram ettik. Kaç litre ayran ikram ettik?",
        "Bir duvarın {a} kısmı boyandı. Boyanan kısmın {b|i} Ali boyadı. Ali duvarın ne kadarını boyadı?",
        "{a} metre telin {b} kadarıyla çit örüldü. Çitte kaç metre tel kullanıldı?",
    ),
    "word_div": (
        "{a} kilo un, {b} kiloluk poşetlere bölünecek. Kaç poşet dolar? Yarım kalan poşeti kesirle say.",
        "{a} litre limonata {b} litrelik bardaklara dağıtılıyor. Kaç bardak eder?",
        "{a} metre kurdele, her biri {b} metre olan parçalara ayrılacak. Kaç parça çıkar? Gerekirse kesirli yaz.",
        "Bir arabanın deposu {b} litre alıyor. {a} litre benzin bu deponun kaç katıdır?",
        "Her gün {b} kilo yem veriliyor. {a} kilo yem kaç gün yeter? Kesirli gün de olabilir.",
    ),
}

SOZEL = {tur: SOZEL_PROMPTS[tur] + SOZEL_EK[tur] for tur in SOZEL_EK}

__all__ = ["BASIC_PROMPTS", "BOSLUK", "CUMLE", "SOZEL", "TAM_EK"]
