# Megazeka-Kesir · Türkçe adım adım kesir çözücü

Megazeka-Kesir’e `(7/18+11/24)*8/19=?` yazabilirsiniz. Model önce parantezi çözer, kesirleri hangi paydaya getireceğini Türkçe anlatır, ara işlemleri yazar ve cevabı `Sonuç: 61/171` satırıyla bitirir. Aynı modele “bir buçuk metrelik telin dokuzda dördü kaç metre?” gibi bir problem de sorabilirsiniz. Bu kez önce sözcükleri kesirlere, ardından soruyu bir işleme çevirmesi gerekir.

**v2.0, Qwen3.5-4B tabanına geçen sürümdür.** Eğitim verisi ve ayarları v1.0 ile aynı, değişen yalnızca taban model. İki ayrı kör sınavda doğru son değer sayısı, v1.0’ın ikisinde de aldığı 103/120’den 119/120’ye ve 115/120’ye çıktı. Yeni sınavda ara adımında yanlış eşitlik bulunan cevaplar 14’ten 1’e indi. Kaynak kod ve testler bu depoda. Eğitilmiş model ve veriler Hugging Face’te indirilebilir. Modeli kullanmak için yeniden eğitmeniz gerekmez. [Model kartı](https://huggingface.co/pandakingpunc/megazeka-kesir-tr) · [Veri kümesi](https://huggingface.co/datasets/pandakingpunc/megazeka-kesir-tr-steps) · [v1.0 (Qwen2.5-1.5B)](https://github.com/pandakingpunc/megazeka-kesir/tree/v1.0)

Model deposu v2.0 ile tabanı anmayan `megazeka-kesir-tr` adını aldı. İki sürüm aynı depoda `v1.0` ve `v2.0` etiketleriyle durur. Eski `megazeka-kesir-qwen2.5-1.5b-tr` adresi bu depoya yönlenir.

| Modele verilen soru | Modelin yazdığı son değer |
|---|---|
| `(7/18+11/24)*8/19=?` | `61/171` |
| `-54/90 = ?` | `-3/5` |
| `−19∕24 __ −25∕32 boşluğu doldur.` | `<` |
| `Eksi iki tam yirmide on biri bileşik kesir olarak nasıl yazıyoruz?` | `-51/20` |
| `47/0 = ?` | `tanımsız` |
| `Bir buçuk metrelik telin dokuzda dördü maket köprüye gidecekmiş. Makete ayrılan tel kaç metre tutar?` | `2/3` |
| `Ece yüzmede kilometrenin onda üçünü sırtüstü, yirmide yedisini serbest stilde yüzmüş. Defterine toplam kaç kilometre yazmalı?` | `13/20` |

Bunlar v2.0’ın yeni kör sınavda kaydedilmiş çıktıları. İlk örnekte modele yalnızca `(7/18+11/24)*8/19=?` verildiğinde tam yanıt şöyleydi:

```text
İşlem: (7/18 + 11/24) × 8/19
1. Önce parantezin içindeki işlemi yap.
2. Paydaların EBOB'unu bulmak için 24 ile 18 sayısına Öklid bölmesi uygula.
   24 = 1 × 18 + 6
   18 = 3 × 6 + 0
3. Son sıfır olmayan kalan 6, yani EBOB 6. Ortak payda 18 ÷ 6 × 24.
   18 ÷ 6 × 24 = 3 × 24 = 72
   72 = 4 × 18 = 3 × 24
4. İlk kesrin pay ve paydasını 4 ile, ikincininkini 3 ile çarp.
   (7/18) + (11/24) = (28/72) + (33/72)
5. Payları topla, ortak paydayı koru.
   (28/72) + (33/72) = (28 + (33))/72 = 61/72
6. Sadeleştirmek için 72 ile 61 sayısının EBOB'unu Öklid bölmesiyle bul.
   72 = 1 × 61 + 11
   61 = 5 × 11 + 6
   11 = 1 × 6 + 5
   6 = 1 × 5 + 1
   5 = 5 × 1 + 0
7. Son sıfır olmayan kalan 1, yani EBOB 1. Kesir zaten en sade hâlinde.
   61/72 = 61/72
8. Bulduğun ara sonucu yerine koy ve kalan işlemi yap.
   ((7/18) + (11/24)) × (8/19) = (61/72) × (8/19)
9. Payları kendi arasında, paydaları kendi arasında çarp.
   61 × 8 = 488
   72 × 19 = 72 × 10 + 72 × 9 = 720 + 648 = 1368
   (61/72) × (8/19) = (61 × (8))/(72 × 19) = 488/1368
10. Sadeleştirmek için 1368 ile 488 sayısının EBOB'unu Öklid bölmesiyle bul.
   1368 = 2 × 488 + 392
   488 = 1 × 392 + 96
   392 = 4 × 96 + 8
   96 = 12 × 8 + 0
11. Son sıfır olmayan kalan 8, yani EBOB 8. Payı ve paydayı 8 ile böl.
   488/1368 = (488 ÷ 8)/(1368 ÷ 8) = 61/171
Sonuç: 61/171
```

Tel sorusunda ise çözüm `Okunuş: bir buçuk = 1 tam 1/2; dokuzda dört = 4/9` ile başlar. Model “bir miktarın belli bir kesri” ifadesi için çarpmayı seçer, `1 tam 1/2`’yi `3/2`’ye çevirir ve `(3/2) × (4/9) = 12/18 = 2/3` yazar. Okunuşu ve seçilen işlemi görebilmek, yanlış bir yanıtın nerede başladığını bulmayı da kolaylaştırır. [Yeni sınavın çıktıları](reports/tahminler/v2-gercek5.jsonl) · [Önceki sınavın çıktıları](reports/tahminler/v2-gercek4.jsonl)

## v1.0’dan ne değişti?

Veri, eğitim ayarları ve puanlayıcı aynı kaldı. v1.0’ın 1,5 milyar parametreli Qwen2.5-1.5B-Instruct tabanı yerine 4 milyar parametreli **Qwen3.5-4B** kullanıldı. İki model aynı 18.000 soruyla, aynı sayıda adımla eğitildi.

Farkın en çok görüldüğü yer sözel problemler. Yukarıdaki Ece sorusunda v1.0 “yüzmede” sözcüğünü `yüz = 100` diye okudu ve sonucu `213/20` buldu. v2.0 yalnız iki kesri okudu, `3/10 + 7/20 = 13/20` hesabını yaptı. Yeni sınavda iki miktarı birleştiren sözel problemlerde v1.0 **4/10**, v2.0 **10/10** aldı. Kalan miktarı soran sözel problemlerde bu sayılar **6/10** ve **10/10**.

## Sonuçlar

**Yeni sınav (`gercek5`)** bu sürüm için yazıldı. 12 soru türünden onar örnek içerir, 24’ü yalnızca sembolden oluşur. Soruları eğitim verisini üreten kod değil, ayrı bir yapay zekâ oturumu (GPT-6.2 Sol) yazdı. Her sorunun işlemi ve cevap anahtarı elle kontrol edildi. Sınav, iki model de çalıştırılmadan önce dosya özetiyle donduruldu. **Önceki sınav (`gercek4`)** v1.0’ın eğitim verisi sabitlendikten sonra yazılmıştı. v2.0 aynı veriyle eğitildiği için bu sınav onun için de kördür.

| Aynı sorularda ölçülen davranış | v1.0 (Qwen2.5-1.5B) | v2.0 (Qwen3.5-4B) |
|---|---:|---:|
| Yeni sınavın tamamında doğru son değer | 103/120 | **119/120 (%99,2)** |
| Eğitimdeki işlem yapılarıyla çakışan 7 soru çıkarılınca | 97/113 | **112/113** |
| Yeni sınavın 24 sembolik sorusunda doğru son değer | 22/24 | **24/24** |
| Yeni sınavda en az bir yanlış ara eşitlik içeren yanıt | 14 | **1** |
| Önceki sınavın tamamında doğru son değer | 103/120 | **115/120 (%95,8)** |
| Önceki sınavın 24 sembolik sorusunda doğru son değer | 21/24 | **23/24** |
| Önceki sınavda en az bir yanlış ara eşitlik içeren yanıt | 20 | **2** |
| Türkçe dışında bir dile geçen yanıt (iki sınav) | 0 | **0** |

**Tablo nasıl okunmalı?** Yeni sınavın 7 sorusu, yazılışı farklı olsa da eğitimdeki bir işlemle aynı matematiksel yapıya sahip. Eğitim verisi iki modelde ortak olduğu için bu çakışma ikisini eşit etkiler. Yine de bu 7 soru çıkarılmış sonuç ayrı satırda verildi. **Doğru son değer** matematiksel eşdeğerliği ifade eder. Örneğin `17/136` ile `1/8` aynı puanı alır. Ara eşitlik denetimi, yanıttaki `a = b` biçimindeki satırları kesin kesir aritmetiğiyle sınar. İki modelin de 240 yanıtının 228’inde denetlenebilen en az bir ara eşitlik vardı. [Değerlendirme raporu](reports/degerlendirme-v2.md)

### Hangi sorularda yanıldı?

v2.0 iki sınavdaki 240 sorunun 6’sında yanlış son değer verdi. Bunların dördünde sayıları doğru okudu ama soruyu yanlış işleme çevirdi. İkisinde ise işlemi doğru kurup hesapta yanıldı.

| Soru | Hata nerede başladı? |
|---|---|
| Kırk ikide beş litrelik bir kepçem var. Tenceredeki altıda beş litre çorbayı bitirmek için bu kepçeyi kaç kez tam doldurmam gerekir? *(önceki sınav)* | Bölmeyi ters kurdu: `5/42 ÷ 5/6 = 1/7`. Doğrusu `5/6 ÷ 5/42 = 7`. v1.0 da bu soruda aynı hatayı yaptı. |
| Minderler için spor salonunun 15/28'ini boşalttık. Açtığımız alanın 7/10'una minder serdik. Minderler salonun tamamının ne kadarını kaplıyor? *(önceki sınav)* | “alanın 7/10’u” çarpma isterken iki kesri topladı ve `173/140` buldu. Doğrusu `3/8`. |
| Ölçümde kar kalınlığı önce 13/25 metre, erime sonunda 3/20 metre çıktı. Karın kalınlığı kaç metre azalmış? *(önceki sınav)* | Çıkarma yerine çarpma seçti ve `39/500` buldu. Doğrusu `37/100`. |
| `31/42 - (5/18 + 2/63) =` *(önceki sınav)* | 63’ü 18’in katı saydı. Ortak payda 126 olmalıydı. Sonuç `3/7` yerine `59/126` çıktı. |
| 4 tam 7/24'ü 11/18'e böl. Çıkan sonuçtan 5/12 çıkarınca kaç kalır? *(yeni sınav)* | Öklid adımında `1854 = 7 × 264 + 16` yazdı. `7 × 264 = 1848`, kalan 6’dır. Sonuç `218/33` yerine `79/12` oldu. |

Tabloda olmayan altıncı yanlış, önceki sınavdaki ikinci ters kurulmuş bölmedir: “Doksan altıda on bir metre uzunluğunda parçalar istiyor öğretmen. On ikide on bir metrelik kurdeleden bu boyda kaç parça çıkar?” sorusunda `8` yerine `1/8` buldu. Sözel bir problemin hangi işleme karşılık geldiğini seçmek bu sürümün en zayıf yanı. Özellikle bir çözümü öğrenciye örnek gösterecekseniz, modelin seçtiği işlemi ve ara satırları da kontrol edin. [Yeni sınavın soruları](data/gercek5.jsonl) · [Modelin verdiği tam cevaplar](reports/tahminler/v2-gercek5.jsonl)

## Kurulum ve kullanım

Kod deposunu indirin ve v2.0’ı seçin. Model 4 bit olarak yüklenir. Test edilen ortam Colab’daki NVIDIA L4’tür (Linux, Transformers 5.17.0, PEFT 0.21.2, bitsandbytes 0.50.2). `3/4+1/2` sorusunda ölçülen en yüksek GPU belleği 3,4 GB’dir. Bu yüzden 8 GB’lık kartlara sığması beklenir, ancak böyle bir kartta denenmedi. Önce sisteminize uygun CUDA destekli PyTorch’u, ardından depodaki çıkarım bağımlılıklarını kurun. [PyTorch kurulum seçenekleri](https://pytorch.org/get-started/locally/)

```shell
git clone https://github.com/pandakingpunc/megazeka-kesir.git
cd megazeka-kesir
git checkout v2.0
python -m pip install -r requirements.txt
python -X utf8 src/sohbet.py --ham
```

`Soru>` satırına bir kesir sorusu yazın. Çıkmak için `q` girin. İlk çalıştırmada Qwen3.5-4B tabanı (yaklaşık 9 GB) ve Megazeka-Kesir adaptörü Hugging Face’ten indirilir. Hesaplama bilgisayarınızda yapılır. `--ham` soruyu aynen modele gönderir. Bu seçeneği kaldırırsanız terminal, yalnızca işlem içeren girdilere Türkçe çözüm isteğini kendisi ekler. Ölçümlerde soru aynen verildi. v1.0’ı (Qwen2.5-1.5B) denemek için `--surum v1.0` ekleyin.

Linux’ta `flash-linear-attention` paketini kurmak Qwen3.5’in doğrusal dikkat katmanlarını hızlandırır. Paket yoksa model aynı sonucu daha yavaş veren PyTorch yolunu kullanır.

### Python içinden

Aşağıdaki örnek v2.0 adaptörünü sürüm etiketinden yükler. Qwen3.5-4B görsel-metin modeli olduğu için `AutoModelForImageTextToText` ile yüklenir. Adaptör yalnızca metin katmanlarında eğitildi. `enable_thinking=False` modelin düşünme bölümünü boş bırakır. Eğitimde de bu biçim kullanıldı. v1.0’ın tabanı ve yükleme kodu farklıdır, onun örneği [v1.0 model kartında](https://huggingface.co/pandakingpunc/megazeka-kesir-tr/blob/v1.0/README.md) durur.

```python
import torch
from peft import PeftModel
from transformers import AutoModelForImageTextToText, AutoTokenizer, BitsAndBytesConfig

base_id = "unsloth/Qwen3.5-4B"
adapter_id = "pandakingpunc/megazeka-kesir-tr"
tokenizer = AutoTokenizer.from_pretrained(base_id)
quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                           bnb_4bit_compute_dtype=torch.bfloat16)
base = AutoModelForImageTextToText.from_pretrained(base_id, dtype=torch.bfloat16, device_map="cuda",
                                                   quantization_config=quant)
model = PeftModel.from_pretrained(base, adapter_id, revision="v2.0").eval()

messages = [{"role": "user", "content": "3/4+1/2"}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                       enable_thinking=False)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
with torch.inference_mode():
    output = model.generate(**inputs, do_sample=False, max_new_tokens=1500,
                            pad_token_id=tokenizer.pad_token_id)
answer = tokenizer.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(answer)
```

## Eğitim verisi nasıl hazırlandı?

v2.0, v1.0 ile aynı veriyle eğitildi. Üretici önce işlemi ve sayıları seçer, soruyu sembollerle veya Türkçe bir cümleyle yazar, ardından aynı işlemden adım adım bir çözüm çıkarır. Örneğin “Eksi on sekiz bölü sekiz sadeleşince hangi kesir olur?” sorusunda çözüm önce `-18/8` okunuşunu gösterir, sonra pay ve paydayı 2’ye bölerek `-9/4` sonucuna ulaşır. Ayrı bir denetleyici hem son cevabı hem de yazılmış ara eşitlikleri kesin kesir aritmetiğiyle sınar. Üç sentetik bölümde toplam **158.995 ara hesap** denetlendi. 18.000 eğitim sorusunun **2.084’ü hiçbir harf içermez**. Böylece model karşısında Türkçe bir komut görmeden de Türkçe açıklamaya başlamayı öğrenir.

| Hugging Face bölümü | Örnek | İçerik ve kullanım |
|---|---:|---|
| `train` | 18.000 | Soru ve Türkçe çözüm. Model bu örneklerden öğrendi. |
| `validation` | 500 | Eğitim sırasında yeni örneklerdeki kaybı izlemek için ayrıldı. |
| `test` | 600 | Üreticiden gelen ayrı sorular ve referans çözümler. |
| `test_gercek` | 120 | v1.0 için bağımsız hazırlanmış sınav (`gercek4`). |
| `test_gercek5` | 120 | v2.0 için bağımsız hazırlanmış yeni sınav (`gercek5`). `messages` yalnızca soruyu içerir, doğru değer `meta.answer` alanındadır. |

İki sınav da gerçek kullanıcı konuşmalarından toplanmış bir kayıt değildir. Sembolik ifadeler, sözcüklerle yazılmış kesirler ve günlük hayat problemleri gibi kullanım biçimlerini sınamak için hazırlanmıştır. [Yayımlanan veri bölümleri](https://huggingface.co/datasets/pandakingpunc/megazeka-kesir-tr-steps/tree/v2.0)

Veriyi Python içinden okumak için önce `python -m pip install datasets` çalıştırın. Yeni sınavdan bir soru ve cevap anahtarını şöyle görebilirsiniz.

```python
from datasets import load_dataset

veri = load_dataset("pandakingpunc/megazeka-kesir-tr-steps", revision="v2.0")
ornek = veri["test_gercek5"][0]
print(ornek["messages"][0]["content"])
print(ornek["meta"]["answer"])
```

### Model ve eğitim ayarları

Megazeka-Kesir v2.0, Qwen3.5-4B üzerinde 4 bit QLoRA ile eğitildi. Temel modelin yanında yüklenen küçük bir adaptör, kesir çözümüne özgü öğrenilmiş ağırlıkları taşır. Eğitimde yalnızca asistanın cevabındaki tokenlar için kayıp hesaplandı. Qwen3.5’in sohbet şablonu cevabın başına boş bir düşünme bölümü ekler. Kayıp maskesi bu bölümden sonra başlar.

| Ayar | Değer |
|---|---|
| Taban | `unsloth/Qwen3.5-4B` (Apache-2.0), 4 bit yüklenerek |
| LoRA | Rütbe 16, alfa 32, dropout 0, metin katmanlarındaki dikkat ve MLP projeksiyonları |
| Eğitim | 18.000 örnek üzerinden iki geçiş, 2.250 ağırlık güncellemesi |
| Grup boyutu | 8 örnek × 2 gradyan biriktirme adımı |
| Bağlam ve öğrenme oranı | 1.792 token, başlangıç hedefi 0,0002, 50 ısınma adımı |
| Donanım ve süre | Colab NVIDIA L4 24 GB, bfloat16, 3 saat 0 dakika 34 saniye, en yüksek bellek 5,1 GB |
| Son doğrulama kaybı | 0,00036 (en iyi nokta son adım) |

T4 kartında bfloat16 desteği olmadığı için Qwen3.5 float32’ye düşer ve adım başına süre yaklaşık dört katına çıkar. Bu yüzden eğitim L4’te yapıldı. Depodaki `v2-q35-4b` dosya adları modelin eğitim sırasındaki adına karşılık gelir. [Eğitim yapılandırması](configs/v2-q35-4b.json) · [Eğitim kodu](training/train.py) · [Colab not defteri](colab/megazeka_kesir_q35_4b.ipynb)

### Veriyi ve ölçümleri yeniden üretme

Veri üretimi ve birim testleri Python 3.10 ve üzeriyle, yalnızca standart kütüphane kullanılarak çalışır. İlk komut tohum 13 ile eğitim verisinin üç sentetik bölümünü `data/v13/` altında üretir. İkinci komut doğrulama yaparken sınavları ve kısa işlem yoklamasını da dışarıda tutar.

```shell
python -X utf8 src/uret_v13.py
python -X utf8 src/denetle_v11.py --data data/v13 --dislanan data/gercek.jsonl data/gercek2.jsonl data/gercek3.jsonl data/gercek4.jsonl data/test.jsonl data/v11/test.jsonl data/yoklama.jsonl
python -X utf8 -m unittest discover -s tests
```

Kayıtlı cevapları yeniden puanlamak için model indirmeniz gerekmez. Aşağıdaki komut yeni sınavda v2.0’ın doğru son değerlerini, türlere göre dağılımını ve yanlış ara eşitlik içeren yanıtları hesaplar.

```shell
cd src
python -X utf8 puanla.py --test ../data/gercek5.jsonl --tahmin ../reports/tahminler/v2-gercek5.jsonl --out ../reports/v2-gercek5-puan.json
```

Cevapları yeniden üretmek için `python -X utf8 src/cikarim.py --adapter pandakingpunc/megazeka-kesir-tr --test data/gercek5.jsonl --out tahmin.jsonl --max-new-tokens 1500` çalıştırın. Yeniden eğitim Colab’da yapıldı. [Not defteri](colab/megazeka_kesir_q35_4b.ipynb) eğitim kodunu, ayarları ve veriyi Drive’a kurar, sonra eğitimi arka planda başlatıp ilerlemeyi yazar. Test edilen eğitim ortamı Unsloth 2026.11.11, TRL 1.15.0, Transformers 5.17.0 ve PyTorch 2.14.1+cu130 kullanıyordu. Kendi ortamınızda eğitimi başlatmak için:

```shell
python -X utf8 training/train.py --config configs/v2-q35-4b.json --ad v2-q35-4b
```

## Megazeka ailesi

[Megazeka](https://github.com/pandakingpunc/megazeka) Türkçe yazımı düzeltir. [Megazeka-Sayı](https://github.com/pandakingpunc/megazeka-sayi) yazıyla söylenen sayıları bağlama uygun rakam biçimine dönüştürür. [Megazeka-Denklem](https://github.com/pandakingpunc/megazeka-denklem) bir bilinmeyenli denklemleri çözer. Megazeka-Kesir’in odağı, bir kesir sorusunun nasıl okunduğunu ve çözüldüğünü Türkçe adımlarla göstermektir.

## English summary

Megazeka-Kesir v2.0 is a Turkish fraction-solving LoRA adapter for Qwen3.5-4B. It shows the calculation behind an answer, including how it reads fractions written in words. It was trained on the same 18,000 examples and with the same settings as v1.0 (Qwen2.5-1.5B-Instruct); only the base model changed. On a new held-out set of 120 questions it returned the correct final value in 119 cases (v1.0: 103), and on the earlier held-out set in 115 cases (v1.0: 103). Responses with at least one incorrect intermediate equality dropped from 14 to 1 and from 20 to 2. The remaining errors are mostly word problems translated into the wrong operation. The repository includes the evaluation inputs, raw predictions and scoring code.

## Lisans ve yazar

Kaynak kod [MIT](LICENSE), model adaptörü [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0), özgün veri [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/) lisansıyla yayımlanmıştır. Taban model Qwen3.5-4B Apache-2.0 lisanslıdır.

Mustafa Karatüm · [ORCID 0009-0006-7053-2872](https://orcid.org/0009-0006-7053-2872)
