"""Kesir soruları için Türkçe metin şablonları."""

BASIC_PROMPTS = {
    "simplify": (
        "{islem} kesrini en sade hâline getir.",
        "{islem} kesri sadeleşince ne olur?",
        "{islem} kesrinin sadeleştirilmiş hâlini bul.",
        "Pay ve paydanın ortak çarpanlarını gider: {islem}.",
        "{islem} kesrini eşit değerli, indirgenmiş biçimde yaz.",
        "{islem} kesrini sadeleştirip sonucu yaz.",
    ),
    "compare": (
        "{islem} kesirlerinden ilki ikinciden küçük mü, büyük mü, yoksa eşit mi? <, = ya da > yaz.",
        "{islem} karşılaştırmasında soldaki sayı sağdakinden küçük mü, eşit mi, büyük mü?",
        "{islem} çiftini soldan sağa karşılaştırıp <, = veya > yaz.",
        "{islem} için uygun karşılaştırma işaretini (<, =, >) seç.",
        "Soldaki kesirle sağdaki kesri karşılaştır: {islem}. Sonucu <, = veya > ile göster.",
        "{islem} gösterimindeki iki kesir arasına hangi işaret yazılır: <, = veya >?",
    ),
    "add": (
        "{islem} toplamını bul.",
        "{islem} işleminin sonucu kaç?",
        "Şu kesirleri topla: {islem}.",
        "{islem} toplamının en sade sonucu ne?",
        "{islem} işlemini yap ve sonucu sadeleştir.",
        "{islem} toplamını tek sayı olarak yaz.",
    ),
    "sub": (
        "{islem} farkını hesapla.",
        "{islem} işleminin sonucu ne olur?",
        "Şu çıkarma işlemini yap: {islem}.",
        "{islem} farkını en sade biçimde yaz.",
        "{islem} işlemini tamamla, sonucu sadeleştir.",
        "{islem} kaç eder?",
    ),
    "mul": (
        "{islem} çarpımını bul.",
        "{islem} işleminin sonucunu hesapla.",
        "Verilen kesirleri çarp: {islem}.",
        "{islem} çarpımı en sade biçimde nasıl yazılır?",
        "{islem} işlemini çöz.",
        "{islem} çarpımını tek sayı olarak yaz.",
    ),
    "div": (
        "{islem} bölümünü hesapla.",
        "{islem} işlemi kaç eder?",
        "Şu bölme işlemini yap: {islem}.",
        "{islem} bölümünün sade sonucu nedir?",
        "{islem} ifadesinin değerini bul.",
        "{islem} işlemini çöz ve sonucu sadeleştir.",
    ),
    "mixed": (
        "{islem} ifadesinin sonucunu tek kesir veya tam sayı olarak yaz.",
        "İşlem sırasına dikkat ederek {islem} ifadesini çöz.",
        "{islem} ifadesini hesapla ve sadeleştir.",
        "{islem} kaç eder? Sonucu tam sayı ya da sade kesir olarak ver.",
        "Şu ifadenin değerini bul: {islem}.",
        "{islem} işleminin sadeleştirilmiş sonucunu yaz.",
    ),
    "invalid": (
        "{islem} ifadesinin bir değeri var mı?",
        "{islem} işleminin sonucu nedir?",
        "{islem} tanımlıysa değerini, değilse tanımsız olduğunu yaz.",
        "{islem} ifadesini değerlendir. Sayısal bir sonuç elde edilebilir mi?",
        "{islem} işlemi tanımlı mı?",
        "{islem} için sonuç varsa sonucunu yaz.",
    ),
}

SOZEL_PROMPTS = {
    "word_add": (
        "Ayça önce {a} litre, sonra {b} litre su içti. Toplam kaç litre su içti?",
        "Bir kaba {a} kilogram un koydum, üzerine {b} kilogram daha ekledim. Kapta kaç kilogram un var?",
        "Ece sabah {a} kilometre, akşam {b} kilometre yürüdü. O gün toplam kaç kilometre yürüdü?",
        "İki kurdeleden biri {a} metre, diğeri {b} metre. Uzunlukları toplam kaç metre?",
        "Bir sürahiye {a} litre elma suyu ile {b} litre armut suyu doldurdum. Sürahide kaç litre meyve suyu var?",
    ),
    "word_sub": (
        "Şişedeki {a} litre sütün {b} litresini kullandım. Şişede kaç litre kaldı?",
        "{a} metre ipten {b} metre kestim. Geriye kaç metre ip kaldı?",
        "{a} kilogram pirincin {b} kilogramını pişirdim. Kaç kilogram pirinç kaldı?",
        "{a} kilometrelik yolun {b} kilometresini yürüdüm. Kaç kilometre yolum kaldı?",
        "Depoda {a} litre su vardı. {b} litre boşalttım. Depoda şimdi kaç litre su var?",
    ),
    "word_of": (
        "Bir kapta {a} litre zeytinyağı var. Bunun {b} kadarını kullanırsam kaç litre kullanmış olurum?",
        "{a} metrelik kurdelenin {b} kesri kadar bir parça kestim. Parça kaç metre?",
        "Elimde {a} kilogram un var. Bu miktarın {b} kadarını hamura koydum. Kaç kilogram un kullandım?",
        "{a} kilometrelik yolun {b} kadarını yürüdüm. Kaç kilometre yürüdüm?",
        "{a} litre sütün {b} kadarı bir bardağa döküldü. Bardağa kaç litre süt döküldü?",
    ),
    "word_div": (
        "{a} litre çorba var. Bir porsiyon {b} litre ise bu miktar kaç porsiyona karşılık gelir? Kesirli porsiyonu da say.",
        "{a} metrelik ipin uzunluğu, {b} metrelik bir standart parçanın kaç katıdır? Sonucu gerekirse kesirli yaz.",
        "{a} kilogram pirinç var. Bir paket {b} kilogram alıyorsa bu miktar kaç paket eder? Tam dolmayan paketi de kesirli olarak hesaba kat.",
        "{a} litre suyum var ve bir bardak {b} litre alıyor. Bu su, tam ya da kesirli olarak kaç bardak eder?",
        "Bir tarifte {b} kilogram un bir ölçü sayılıyor. {a} kilogram un kaç ölçüdür? Sonucu gerekiyorsa kesir olarak yaz.",
    ),
}
