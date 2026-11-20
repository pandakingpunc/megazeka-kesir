# Megazeka-Kesir v1.0 değerlendirmesi

Her iki adaptöre de soru metinleri aynen verildi. Aşağıdaki önceki deney yerelde v1.2 (`v12`), ilk açık sürüm v1.0 ise v1.3 (`v13`) olarak adlandırılır. Yeni sınav için ölçüm açgözlü çözümleme, 16'lık grup ve en çok 1.500 yeni tokenla aynı 4 bit taban üzerinde yapıldı.

| Küme ve ölçüm | Önceki deney | **v1.0** |
| --- | ---: | ---: |
| Önceki 24 kısa işlemde Türkçe yanıt | 2/24 | **24/24** |
| Önceki 24 kısa işlemde doğru nihai değer | 22/24 | **22/24** |
| Yeni sınavın 24 sembolik sorusunda Türkçe yanıt | 0/24 | **24/24** |
| Aynı 24 sembolik soruda doğru nihai değer | 11/24 | **21/24** |
| Yeni sınavda Türkçe yanıt | 96/120 | **120/120** |
| Yeni sınavda doğru nihai değer | 95/120 | **103/120** |
| İki adaptörün de eğitim ve doğrulamasından ayrı kalan yeni sorularda doğru nihai değer | 88/112 | **96/112** |
| Eski 120 soruluk sınavda standart puan | 101/120 | **101/120** |
| Eski 600 üretilmiş soruda standart puan | 579/600 | **576/600** |

Bağımsız bir yapay zekâ tarafından hazırlanan yeni sınav 12 soru türünden onar örnek içeriyor. Bunun 24'ünde soru metni harf içermiyor. Yeni sınavın sekiz işlem yapısı önceki adaptörün eğitiminde vardı (008, 012, 017, 028, 036, 044, 059, 107). Yayımlanan sürümün verisi üretilirken sınavdaki işlem anahtarları ve soru metinleri dışlandı.

Dil sınıflandırması sözcük ve alfabe ipuçlarına dayanıyor. Karışık, belirsiz ve yalnızca matematik içeren yanıtlar Türkçe sayısına dahil edilmiyor. Sayısal ölçüm kesin kesir aritmetiğiyle nihai değeri karşılaştırıyor ve eşdeğer kesirleri kabul ediyor. Yeni sınavdaki önceki yanıtlardan üçünde standart puanlayıcı Çince kapanıştaki doğru değeri okuyamadı. Çok dilli sonuç okumasıyla puan 92/120'den 95/120'ye çıktı. Geçmiş karşılaştırma kümelerinde standart puanlayıcının sonuçları kullanıldı.

Yayımlanan adaptör yeni sınavda 20 yanıtta en az bir hatalı ara eşitlik yazdı. Örneğin bir yanıtta sonuç olan `1/8` doğruydu, ara satırdaki `680 = 8 × 85 + 60` eşitliği yanlıştı. Uzun cevaplar tekrar edebilir veya yarıda kalabilir. Bu ölçümler kesir sorularıyla sınırlıdır.

## CPU üzerinde yeniden puanlama

Depo kökünde çalıştırın. [Kayıtlı model yanıtları](tahminler/) her satırda yalnız soru kimliğini ve modelin yanıtını içerir. Komutlar model indirmeden dil ve doğruluk sayılarını yeniden çıkarır. `--ozet` kaldırıldığında her çıktı dil ipuçlarını, okunan ve beklenen sonucu ve yanıt metnini gösterir.

```powershell
foreach ($surum in 'v12', 'v13') {
    foreach ($kume in 'yoklama', 'gercek4') {
        python -X utf8 src/yoklama_raporu.py --test "data/$kume.jsonl" --tahmin "reports/tahminler/$surum-$kume.jsonl" --ozet
    }
    foreach ($kume in 'gercek3', 'test') {
        python -X utf8 src/puanla.py --test "data/$kume.jsonl" --tahmin "reports/tahminler/$surum-$kume.jsonl" --out ".cache/$surum-$kume-puan.json"
    }
}
```

Yeni sınavdaki 24 sembolik soruyu ve 112 ortak ayrılmış soruyu ayrıca puanlayın.

```powershell
$ortakKumeDisi = '008', '012', '017', '028', '036', '044', '059', '107'
$sembolik = @()
$ortak = @()
Get-Content -Encoding utf8 data/gercek4.jsonl | ForEach-Object {
    $satir = $_ | ConvertFrom-Json
    if ($satir.messages[0].content -notmatch '\p{L}') {
        $sembolik += '--id', $satir.meta.id
    }
    if ($satir.meta.id.Substring($satir.meta.id.Length - 3) -notin $ortakKumeDisi) {
        $ortak += '--id', $satir.meta.id
    }
}
foreach ($surum in 'v12', 'v13') {
    $tahmin = "reports/tahminler/$surum-gercek4.jsonl"
    python -X utf8 src/yoklama_raporu.py --test data/gercek4.jsonl --tahmin $tahmin --ozet @sembolik
    python -X utf8 src/yoklama_raporu.py --test data/gercek4.jsonl --tahmin $tahmin --ozet @ortak
}
```

## Yayımlanan adaptörle yeni tahmin üretme

[CUDA kurulumundan](../README.md#kurulum-ve-kullanım) sonra depo kökünde çalıştırın. Yeni çıktılar `.cache/yeni-olcum/` altında oluşur.

```powershell
python -X utf8 src/kiyasla.py --adapter pandakingpunc/megazeka-kesir-qwen2.5-1.5b-tr --kosul adapter --batch-size 16 --max-new-tokens 1500 --kumeler data/yoklama.jsonl data/gercek4.jsonl data/gercek3.jsonl data/test.jsonl --reports .cache/yeni-olcum
python -X utf8 src/yoklama_raporu.py --test data/gercek4.jsonl --tahmin .cache/yeni-olcum/adapter_gercek4_tahmin.jsonl --ozet
```
