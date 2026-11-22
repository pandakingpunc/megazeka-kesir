# Megazeka-Kesir · Türkçe adım adım kesir çözücü

Megazeka-Kesir’e `3/4+1/2` yazabilirsiniz. Model iki kesri hangi paydaya getireceğini Türkçe anlatır, ara işlemleri yazar ve cevabı `Sonuç: 5/4` satırıyla bitirir. Aynı modele “beşte üç kilo yoğurdun yarısı kaç kilo?” gibi bir problem de sorabilirsiniz. Bu kez önce sözcükleri kesirlere, ardından soruyu bir işleme çevirmesi gerekir.

**v1.0 ilk açık sürümdür.** Kaynak kod ve testler bu depoda. Eğitilmiş model ve veriler Hugging Face’te indirilebilir. Modeli kullanmak için yeniden eğitmeniz gerekmez. [Model kartı](https://huggingface.co/pandakingpunc/megazeka-kesir-qwen2.5-1.5b-tr) · [Veri kümesi](https://huggingface.co/datasets/pandakingpunc/megazeka-kesir-tr-steps)

| Modele verilen soru | Modelin yazdığı son değer |
|---|---|
| `3/4+1/2` | `5/4` |
| `11/28 - (-5/42) =` | `43/84` |
| `16/36 ? 22/51` | `>` |
| `-105/-150 kesrini sadeleştir.` | `7/10` |
| `6 tam 5/18'i bileşik kesre nasıl çeviririm?` | `113/18` |
| `Yirmi dokuzda on biri, on beşte sıfıra böldüğümde sonuç ne olur?` | `tanımsız` |
| `Beşte üç kilo yoğurdum var, annem bunun yarısını çorbaya koy dedi. Çorbaya kaç kilo yoğurt koymam gerekiyor?` | `3/10` |

Bunlar v1.0’ın kaydedilmiş çıktıları. İlk örnekte terminale sadece `3/4+1/2` yazıldığında tam yanıt şöyleydi:

```text
İşlem: 3/4 + 1/2
1. 4, 2 sayısının katı olduğu için ortak payda 4.
   4 = 2 × 2
2. İlk kesir aynı kalır. İkincinin pay ve paydasını 2 ile çarp.
   (3/4) + (1/2) = (3/4) + (2/4)
3. Payları topla, ortak paydayı koru.
   (3/4) + (2/4) = (3 + (2))/4 = 5/4
Sonuç: 5/4
```

Yoğurt sorusunda ise çözüm `Okunuş: beşte üç = 3/5; yarım = 1/2` ile başlar. Model “bir miktarın belli bir kesri” ifadesi için çarpmayı seçer ve `(3/5) × (1/2) = 3/10` yazar. Okunuşu ve seçilen işlemi görebilmek, yanlış bir yanıtın nerede başladığını bulmayı da kolaylaştırır. [Kısa işlemlerin çıktıları](reports/tahminler/v13-yoklama.jsonl) · [Yeni sınavın çıktıları](reports/tahminler/v13-gercek4.jsonl)

## Sadece işlemi yazınca hangi dilde cevap veriyor?

Önceki yerel deneyde eğitim sorularına genellikle “işlemi çöz” gibi Türkçe bir yönerge eşlik ediyordu. Kullanıcı yalnızca işlemi yazınca dil seçimi modele kalıyordu. Örneğin `3/4 + 5/12 = ?` sorusunun sonucunu doğru olarak `7/6` buldu, fakat açıklamayı Çince yazdı. 24 kısa sorunun yalnızca ikisine Türkçe cevap verdi. Aynı soruların başına “Türkçe olarak adım adım çöz.” eklediğimizde 24’ünü de Türkçe açıkladı.

Yayımlanan modelin eğitiminde **18.000 sorunun 2.084’ü hiçbir harf içermiyor**. Bu soruların karşısında da Türkçe çözümler var. Böylece model `a/b+c/d`, `… = ?` ve `a/b ? c/d` gibi biçimlerde karşısında Türkçe bir komut görmeden açıklamaya başlamayı öğrenebiliyor. Aşağıdaki ölçümlerde soruları aynen verdik. Terminalde bu davranışı denemek için `--ham` seçeneği kullanılır.

## Sonuçlar

**Yeni sınav** 12 soru türünden onar örnek içerir. Bu 120 soruyu eğitim verisini üreten kod yazmadı. Ayrı bir yapay zekâ oturumu soruları hazırladı. Eğitim sorularının nasıl üretileceği sabitlendikten sonra her soru, temsil ettiği işlem ve cevap anahtarı birlikte incelendi. Sınavdaki soru metinleri ve matematiksel işlem yapıları v1.0 eğitiminden çıkarıldı. **24 sembolik soru bu 120’nin içindedir.**

| Aynı sorularda ölçülen davranış | Önceki yerel deney (v1.2) | Açık sürüm (v1.0) |
|---|---:|---:|
| Önceki 24 kısa soruda Türkçe açıklama | 2/24 | **24/24** |
| Bu 24 soruda doğru son değer | 22/24 | **22/24** |
| Yeni sınavın 24 sembolik sorusunda Türkçe açıklama | 0/24 | **24/24** |
| Bu 24 sembolik soruda doğru son değer | 11/24 | **21/24** |
| Yeni sınavın tamamında doğru son değer | 95/120 | **103/120 (%85,8)** |
| İki modelin de eğitim ve doğrulamasında görülmeyen ortak sorularda doğru son değer | 88/112 | **96/112** |
| Eski 120 soruluk sınavda standart puan | 101/120 | **101/120** |
| Eski 600 sentetik soruda standart puan | 579/600 | **576/600 (%96)** |

**Tablo nasıl okunmalı?** Eski 24 soruda iki sürüm de 22 doğru değer buldu. Değişen şey kullanıcının okuyabildiği açıklamaydı. Yeni sembolik sorularda ise hem dil hem hesap iyileşti. Eski 600 soruda yayımlanan model üç soru geride kaldı. Ortak 112 sorunun ayrıca gösterilme nedeni, yeni sınavdaki sekiz işlem yapısının önceki modelin eğitiminde bulunmasıdır.

**Doğru son değer** matematiksel eşdeğerliği ifade eder. Örneğin `17/136` ile `1/8` aynı puanı alır. Bu ölçü en sade biçimi veya bütün ara satırların doğru olduğunu garanti etmez. Önceki modelin Çince yazdığı üç doğru sonucu eski otomatik puanlayıcı okuyamadı. Tablodaki 95/120 bu cevaplar yeniden okunduktan sonraki sayıdır. Ham cevaplar, kullanılan puanlayıcılar ve ölçümü bilgisayarınızda tekrarlama komutları depodadır. [Değerlendirme raporu](reports/degerlendirme.md)

### Hangi tür sorularda zorlanıyor?

Yeni sınavda sadeleştirme, çıkarma ve tanımsız işlem gruplarında **10’ar sorunun 10’unun** son değerini doğru buldu. Kalan miktarı soran sözel problemlerde **6/10**, iki miktarı birleştiren sözel problemlerde **7/10** aldı. Her grupta on örnek bulunduğu için bunlar belirli bir soru türündeki genel başarı oranını tahmin etmekten çok, sonraki geliştirmede hangi cevaplara bakılacağını gösterir.

| Soru | Hata nerede başladı? |
|---|---|
| Tarifte hamur için yarım bardak süt, üzeri için de sekizde üç bardak süt gerekiyor. Sütü baştan tek kapta ölçsem kaç bardak ayırmalıyım? | Model iki miktarı da doğru okudu. Toplama yerine bölmeyi seçip `4/3` buldu. Doğru işlem `1/2 + 3/8 = 7/8`. |
| `15/28 × 14/45` *(yeni sınavdan değil, 24 kısa sorudan)* | Çarpımı doğru kurup `210/1260` buldu. Ortak böleni de doğru olarak 210 buldu, ama bölerken `1/10` yazdı. Doğrusu `1260 ÷ 210 = 6`, yani `1/6`. |
| 5/34 çarpı 17/20 işlemini deftere geçiriyorum, sonucu ne yazayım? | Çarpımı `85/680` olarak doğru kurdu. Ortak böleni ararken `680 = 8 × 85 + 60` yazdı, oysa 8 × 85 tam 680 eder ve kalan 0’dır. Bu yüzden 85 yerine 5 ile sadeleştirip `17/136` buldu. Değer `1/8`’e eşit olduğu için doğru sayıldı ama sade değil. |
| `31/42 - (5/18 + 2/63) =` | Ortak payda hesabında bazı satırları tekrarladı ve sonuca gelmeden yanıt kesildi. Doğru değer `3/7`. |

Yeni sınavın 120 yanıtından **20’sinde en az bir yanlış ara eşitlik** bulundu. Eski 600 soruluk sentetik testte bu sayı 73’tür. Özellikle bir çözümü öğrenciye örnek gösterecekseniz, modelin seçtiği işlemi ve ara satırları da kontrol edin. [Test soruları](data/gercek4.jsonl) · [Modelin verdiği tam cevaplar](reports/tahminler/v13-gercek4.jsonl)

## Kurulum ve kullanım

Kod deposunu indirin ve v1.0’ı seçin. Modeli çalıştırmak için test edilen ortam CUDA destekli PyTorch ve 8 GB belleği olan bir NVIDIA RTX 4060’tır. Önce sisteminize uygun PyTorch’u, ardından depodaki çıkarım bağımlılıklarını kurun. [PyTorch kurulum seçenekleri](https://pytorch.org/get-started/locally/)

```shell
git clone https://github.com/pandakingpunc/megazeka-kesir.git
cd megazeka-kesir
git checkout v1.0
python -m pip install -r requirements.txt
python -X utf8 src/sohbet.py --adapter pandakingpunc/megazeka-kesir-qwen2.5-1.5b-tr --ham --max-new-tokens 1500
```

`Soru>` satırına bir kesir sorusu yazın. Çıkmak için `q` girin. İlk çalıştırmada Qwen tabanı ve Megazeka-Kesir adaptörü Hugging Face’ten indirilir. Hesaplama bilgisayarınızda yapılır. `--ham` soruyu aynen modele gönderir. Bu seçeneği kaldırırsanız terminal, yalnızca işlem içeren girdilere Türkçe çözüm isteğini kendisi ekler. Testlerde kullanılan ayarı denemek için seçeneği açık bırakın.

### Python içinden

Aşağıdaki örnek, v1.0 adaptörünü sürüm etiketinden yükler. Model her adımda en olası devamı seçer. Girdi uzunluğu kadar token çıktının başından ayrılır, böylece ekrana yalnızca modelin cevabı gelir.

```python
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_id = "unsloth/Qwen2.5-1.5B-Instruct-unsloth-bnb-4bit"
adapter_id = "pandakingpunc/megazeka-kesir-qwen2.5-1.5b-tr"
tokenizer = AutoTokenizer.from_pretrained(base_id)
base = AutoModelForCausalLM.from_pretrained(base_id, dtype=torch.bfloat16, device_map="cuda")
model = PeftModel.from_pretrained(base, adapter_id, revision="v1.0").eval()

messages = [{"role": "user", "content": "3/4+1/2"}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
with torch.inference_mode():
    output = model.generate(**inputs, do_sample=False, max_new_tokens=1500,
                            pad_token_id=tokenizer.pad_token_id)
answer = tokenizer.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(answer)
```

## Eğitim verisi nasıl hazırlandı?

Üretici önce işlemi ve sayıları seçer, soruyu sembollerle veya Türkçe bir cümleyle yazar, ardından aynı işlemden adım adım bir çözüm çıkarır. Örneğin “Eksi on sekiz bölü sekiz sadeleşince hangi kesir olur?” sorusunda çözüm önce `-18/8` okunuşunu gösterir, sonra pay ve paydayı 2’ye bölerek `-9/4` sonucuna ulaşır. Ayrı bir denetleyici hem son cevabı hem de yazılmış ara eşitlikleri kesin kesir aritmetiğiyle sınar. Üç sentetik bölümde toplam **158.995 ara hesap** denetlendi.

| Hugging Face bölümü | Örnek | İçerik ve kullanım |
|---|---:|---|
| `train` | 18.000 | Soru ve Türkçe çözüm. Model bu örneklerden öğrendi. |
| `validation` | 500 | Eğitim sırasında yeni örneklerdeki kaybı izlemek için ayrıldı. |
| `test` | 600 | Bu sürümün üreticisinden gelen ayrı sorular ve referans çözümler. |
| `test_gercek` | 120 | Bağımsız hazırlanmış sınav. `messages` yalnızca soruyu içerir, doğru değer `meta.answer` alanındadır. |

`test_gercek` gerçek kullanıcı konuşmalarından toplanmış bir kayıt değildir. Sembolik ifadeler, sözcüklerle yazılmış kesirler ve günlük hayat problemleri gibi kullanım biçimlerini sınamak için hazırlanmıştır. Sonuç tablosundaki **eski 600 soruluk** kıyas da ayrı bir dosyadır. [Eski kıyas kümesi](data/test.jsonl) · [Yayımlanan dört veri bölümü](https://huggingface.co/datasets/pandakingpunc/megazeka-kesir-tr-steps/tree/v1.0)

Veriyi Python içinden okumak için önce `python -m pip install datasets` çalıştırın. Sınavdan bir soru ve cevap anahtarını şöyle görebilirsiniz.

```python
from datasets import load_dataset

veri = load_dataset("pandakingpunc/megazeka-kesir-tr-steps", revision="v1.0")
ornek = veri["test_gercek"][0]
print(ornek["messages"][0]["content"])
print(ornek["meta"]["answer"])
```

### Model ve eğitim ayarları

Megazeka-Kesir, Qwen2.5-1.5B-Instruct’ın 4 bit sürümü üzerinde QLoRA ile eğitildi. Temel modelin yanında yüklenen küçük bir adaptör, kesir çözümüne özgü öğrenilmiş ağırlıkları taşır. Eğitimde yalnızca asistanın cevabındaki tokenlar için kayıp hesaplandı.

| Ayar | Değer |
|---|---|
| Taban | `unsloth/Qwen2.5-1.5B-Instruct-unsloth-bnb-4bit` |
| LoRA | Rütbe 16, alfa 32, dropout 0 |
| Eğitim | 18.000 örnek üzerinden iki geçiş, 2.250 ağırlık güncellemesi |
| Grup boyutu | 8 örnek × 2 gradyan biriktirme adımı |
| Bağlam ve öğrenme oranı | 1.792 token, başlangıç hedefi 0,0002, 50 ısınma adımı |
| Donanım ve süre | RTX 4060 8 GB, yaklaşık 1 saat 45 dakika |

Depodaki `v13` dosya adları modelin eğitim sırasındaki adına karşılık gelir. Kullanıcıya sunulan ilk sürümün etiketi **v1.0**’dır. [Eğitim yapılandırması](configs/v13.json) · [Eğitim kodu](training/train.py)

### Veriyi ve ölçümleri yeniden üretme

Veri üretimi ve birim testleri Python 3.10 ve üzeriyle, yalnızca standart kütüphane kullanılarak çalışır. İlk komut tohum 13 ile v1.0’ın üç sentetik bölümünü `data/v13/` altında üretir. İkinci komut doğrulama yaparken eski sınavları ve kısa işlem yoklamasını da dışarıda tutar.

```shell
python -X utf8 src/uret_v13.py
python -X utf8 src/denetle_v11.py --data data/v13 --dislanan data/gercek.jsonl data/gercek2.jsonl data/gercek3.jsonl data/gercek4.jsonl data/test.jsonl data/v11/test.jsonl data/yoklama.jsonl
python -X utf8 -m unittest discover -s tests
```

Kayıtlı cevapları yeniden puanlamak için model indirmeniz gerekmez. Örneğin aşağıdaki komut, yeni sınavda kaç açıklamanın Türkçe olduğunu ve kaç doğru son değer bulunduğunu ayrı ayrı verir.

```shell
python -X utf8 src/yoklama_raporu.py --test data/gercek4.jsonl --tahmin reports/tahminler/v13-gercek4.jsonl --ozet
```

Yeniden eğitim için Unsloth ve TRL de gerekir. Test edilen eğitim ortamı Unsloth 2026.11.5, TRL 0.23.1, Transformers 5.5.4 ve PyTorch 2.11.0+cu130 kullanıyordu. Veriyi ürettikten sonra eğitimi başlatmak için:

```shell
python -X utf8 training/train.py --config configs/v13.json --ad v13
```

## Megazeka ailesi

[Megazeka](https://github.com/pandakingpunc/megazeka) Türkçe yazımı düzeltir. [Megazeka-Sayı](https://github.com/pandakingpunc/megazeka-sayi) yazıyla söylenen sayıları bağlama uygun rakam biçimine dönüştürür. [Megazeka-Denklem](https://github.com/pandakingpunc/megazeka-denklem) bir bilinmeyenli denklemleri çözer. Megazeka-Kesir’in odağı, bir kesir sorusunun nasıl okunduğunu ve çözüldüğünü Türkçe adımlarla göstermektir.

## English summary

Megazeka-Kesir is a Turkish fraction-solving LoRA adapter for Qwen2.5-1.5B-Instruct. It shows the calculation behind an answer, including how it reads fractions written in words. In two separate groups of 24 short questions it produced Turkish explanations for all 48 inputs without an added language instruction. On a held-out set of 120 questions it returned the correct final value in 103 cases. Twenty responses contained at least one incorrect intermediate equality. The repository includes the evaluation inputs, raw predictions and scoring code.

## Lisans ve yazar

Kaynak kod [MIT](LICENSE), model adaptörü [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0), özgün veri [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/) lisansıyla yayımlanmıştır.

Mustafa Karatüm · [ORCID 0009-0006-7053-2872](https://orcid.org/0009-0006-7053-2872)
