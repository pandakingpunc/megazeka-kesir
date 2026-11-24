# Megazeka-Kesir v2.0 (Qwen3.5-4B) · kör test karşılaştırması

24 Kasım 2026. v2.0, v1.0 ile aynı veriyle (data/v13, 18.000 örnek) ve aynı ayarlarla eğitildi. v1.0'ın eğitim kayıtlarındaki adı v1.3, v2.0'ınki `v2-q35-4b`. Tek fark taban modeli: Qwen2.5-1.5B-Instruct yerine Qwen3.5-4B. Eğitim Colab L4'te yapıldı (2.250 adım, 3 saat 0 dakika 34 saniye). Son doğrulama kaybı v2'de 0,00036, v1.3'te 0,00165. İki modelin tokenizer'ı farklı olduğu için bu kayıplar birebir karşılaştırılamaz. Asıl karşılaştırma aşağıdaki kör testlerde.

## Sonuçlar

| Ölçüm | v1.3 | v2 |
|---|---:|---:|
| gercek5 (yeni kör küme, 120 soru) doğru son değer | 103/120 | **119/120** |
| gercek5, eğitimle işlem anahtarı çakışan 7 soru çıkarılınca | 97/113 | **112/113** |
| gercek5, yalnız sembolden oluşan sorular | 22/24 | **24/24** |
| gercek5, hatalı ara eşitlik içeren cevap | 14 | **1** |
| gercek4 (120 soru) doğru son değer | 103/120 | **115/120** |
| gercek4, yalnız sembolden oluşan sorular | 21/24 | **23/24** |
| gercek4, hatalı ara eşitlik içeren cevap | 20 | **2** |
| Türkçe dışında bir dile kayan cevap (iki kümede) | 0 | 0 |

gercek4, v1.3 eğitim verisi dondurulduktan sonra yazıldı. v2 aynı veriyi kullandığı için bu küme v2 için de kördür. gercek5 bu ölçüm için GPT-6.2 Sol'a yazdırıldı ve modeller çalışmadan önce donduruldu (sha256 `590df20ffb5c399bb3e26b56e9cfdeee4c6ff7be2e323a24f2c76abe4b6e4099`). Sorular yazılırken yalnız `src/matematik.py` ve önceki sınavlar çakışma denetimi için açılabildi, eğitim verisi açılamadı. Her sorunun `meta.answer` alanı `beklenen()` ile üretildi ve önceki dört sınavla işlem anahtarı ve metin çakışması denetlendi. Görev tanımı gercek4 ile aynı: 12 türde onar soru, 24'ü yalnız sembol, 36'sı tamamen sözle yazılmış. 120 sorunun ifadesi ve cevap anahtarı elle de kontrol edildi.

En büyük fark sözel problemlerde. gercek5'te `word_add` v1.3'te 4/10, v2'de 10/10. `word_sub` 6/10'dan 10/10'a çıktı. Örneğin "Ece yüzmede kilometrenin onda üçünü sırtüstü, yirmide yedisini serbest stilde yüzmüş" sorusunda v1.3 `213/20` yazdı. v2 doğru cevap olan `13/20`'yi buldu.

## v2'nin yanlışları (240 sorunun 6'sı)

- **İşlemi yanlış seçme (4):** gercek4-020 ve 026'da bölmenin yönünü ters kurdu. "Kepçeyle kaç kez" sorusunda `5/6 ÷ 5/42 = 7` yerine `5/42 ÷ 5/6 = 1/7` hesapladı. v1.3 de 020'de aynı hatayı yaptı. 074'te "alanın 7/10'u" çarpma isterken iki kesri topladı. 076'da "kaç metre azalmış" çıkarma isterken iki kesri çarptı.
- **Hesap hatası (2):** gercek4-115'te 63'ün 18'in katı olduğunu varsaydı. Ortak payda 126 olmalıydı, cevap `3/7` yerine `59/126` çıktı. gercek5-035'te Öklid adımında `1854 = 7 × 264 + 16` yazdı. Doğrusu `7 × 264 = 1848`, kalan 6. Cevap `218/33` yerine `79/12` oldu.

Otomatik puanlayıcı son değeri `Sonuç:` satırından okur. 240 cevabın hiçbirinde son değer okunamaz durumda kalmadı. Yanlış olan 6 cevap tek tek okundu.

## Yöntem

- v1.3: yerel RTX 4060'ta `src/kiyasla.py`, batch 16, en çok 1.500 yeni token. v1.3'ün gercek4 sonuçları 20 Kasım ölçümünden alındı.
- v2: Colab L4'te not defterinin 8. hücresi. Unsloth 4-bit, açgözlü üretim, en çok 1.500 yeni token, `enable_thinking=False`, batch 16. Toplu üretimin tekli üretimle aynı sonucu verdiği önce 6 soruda denetlendi. Tahmin biçimi `{"id","prediction"}`.
- Puanlama: iki model için de aynı `src/puanla.py`.
- Depodaki çıkarım kodu: `src/cikarim.py` Unsloth kullanmadan, transformers + peft ile tabanı 4 bit NF4 yükler. Aynı L4'te gercek5'i bu yolla da çözdük. 120 cevabın 119'u ölçümdeki cevapla harfi harfine aynı çıktı, puan yine 119/120. Farklı olan tek cevap zaten yanlış olan 035'tir (iki yolda da farklı bir Öklid adımında yanıldı).

Dosyalar: [Yeni sınav](../data/gercek5.jsonl) · [v2.0 gercek5 cevapları](tahminler/v2-gercek5.jsonl) · [v2.0 gercek4 cevapları](tahminler/v2-gercek4.jsonl) · [v1.0 gercek5 cevapları](tahminler/v13-gercek5.jsonl) · [v1.0 gercek4 cevapları](tahminler/v13-gercek4.jsonl) · [Depo koduyla üretilen v2.0 gercek5 cevapları](tahminler/v2-gercek5-depo-kodu.jsonl)

Puanları yeniden hesaplamak için `src` klasöründe `python -X utf8 puanla.py --test ../data/gercek5.jsonl --tahmin ../reports/tahminler/v2-gercek5.jsonl --out puan.json` çalıştırın.
