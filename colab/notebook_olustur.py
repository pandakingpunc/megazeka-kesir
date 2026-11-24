"""Colab not defterini yerel training/train.py ve configs/*q35* dosyalarindan uretir.

Kullanim (proje kokunden):  python colab/notebook_olustur.py
Cikti: colab/megazeka_kesir_q35_4b.ipynb  (train.py ve ayarlar not defterine gomulu; tek kaynak yerel dosyalar)
"""
import hashlib
import json
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "colab" / "megazeka_kesir_q35_4b.ipynb"
HF_VERI = "pandakingpunc/megazeka-kesir-tr-steps"
HF_REV = "v1.0"
# HF adi -> yerel ad (data/v13), yerel dosyalarin sha256'si yayindakiyle ayni olmali
VERI = {"train.jsonl": "train.jsonl", "validation.jsonl": "val.jsonl", "test.jsonl": "test.jsonl"}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def md(metin):
    return {"cell_type": "markdown", "metadata": {}, "source": metin.strip("\n").splitlines(True)}


def kod(metin):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": metin.strip("\n").splitlines(True)}


def main():
    train_py = (KOK / "training" / "train.py").read_text(encoding="utf-8")
    ayar = json.loads((KOK / "configs" / "v2-q35-4b.json").read_text(encoding="utf-8"))
    pilot = {**ayar, "warmup_steps": 5, "eval_steps": 10, "save_steps": 10,
             "not": "Duman testi: 20 adim, 16 val ornegi."}
    hashler = {hf: sha(KOK / "data" / "v13" / yerel) for hf, yerel in VERI.items()}

    hucreler = [
        md("""
# Megazeka-Kesir v2.0 · Qwen3.5-4B egitimi (Colab L4)

v1.0 (v1.3) verisi ve ayarlariyla ayni egitim, yalniz taban degisir: Qwen2.5-1.5B -> **Qwen3.5-4B** (Apache-2.0).
Calisma zamani turu olarak **L4** secin. T4'te bfloat16 yok; Qwen3.5 float32'ye duser ve egitim ~4 kat yavaslar.

Sira: **1-4 hazirlik + duman testi** (birkac dakika) -> **5 kisa cikarim** -> **6 tam egitim** (L4'te ~3 saat).
Kopma olursa 1-3'u tekrar calistir, sonra 6'da `DEVAM = True` yapip calistir (son checkpoint'ten surer).
Ciktilar Drive'da: `MyDrive/megazeka-kesir-colab/` (models/, reports/).
Bu not defteri `colab/notebook_olustur.py` ile yerel dosyalardan uretildi; elle degil orada duzenle.
"""),
        kod("""
# 1) GPU + Drive
!nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
import os
from google.colab import drive
drive.mount('/content/drive')
KOK = '/content/drive/MyDrive/megazeka-kesir-colab'
for d in ('training', 'configs', 'data/v13', 'models', 'reports'):
    os.makedirs(f'{KOK}/{d}', exist_ok=True)
os.environ['UNSLOTH_COMPILE_LOCATION'] = '/content/unsloth_compiled_cache'  # Drive'a degil, yerel diske
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['PYTHONUTF8'] = '1'
os.chdir(KOK)
print('KOK =', KOK)
"""),
        kod("""
# 2) Kurulum (Unsloth + Qwen3.5 dogrusal dikkat cekirdekleri)
!pip install -q --upgrade unsloth
!pip install -q flash-linear-attention
import importlib.metadata as im
for p in ('unsloth', 'unsloth_zoo', 'trl', 'transformers', 'peft', 'bitsandbytes', 'torch', 'flash-linear-attention'):
    try: print(f'{p:24s}', im.version(p))
    except Exception as e: print(f'{p:24s} YOK ({e})')
"""),
        kod(f"""
# 3) Egitim betigi, ayarlar ve veri (HF {HF_VERI}@{HF_REV}, sha256 denetimli)
import hashlib, json, shutil
from huggingface_hub import hf_hub_download

TRAIN_PY = {train_py!r}
AYAR = {ayar!r}
PILOT = {pilot!r}
HASH = {hashler!r}
YEREL = {VERI!r}

open(f'{{KOK}}/training/train.py', 'w', encoding='utf-8').write(TRAIN_PY)
json.dump(AYAR, open(f'{{KOK}}/configs/v2-q35-4b.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(PILOT, open(f'{{KOK}}/configs/pilot-q35-4b.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for hf_ad, yerel in YEREL.items():
    hedef = f'{{KOK}}/data/v13/{{yerel}}'
    if not os.path.isfile(hedef) or hashlib.sha256(open(hedef, 'rb').read()).hexdigest() != HASH[hf_ad]:
        shutil.copy(hf_hub_download('{HF_VERI}', hf_ad, repo_type='dataset', revision='{HF_REV}'), hedef)
    h = hashlib.sha256(open(hedef, 'rb').read()).hexdigest()
    assert h == HASH[hf_ad], f'{{yerel}}: sha256 uyusmuyor {{h}}'
    print(f'{{yerel:12s}} sha256 OK  {{sum(1 for _ in open(hedef, encoding="utf-8"))}} satir')
"""),
        kod("""
# 4) DUMAN TESTI: 20 adim, 16 val ornegi -> maske denetimi + egitim + kayit
!rm -f reports/gecmis-pilot-q35-4b.jsonl
!python -X utf8 training/train.py --config configs/pilot-q35-4b.json --ad pilot-q35-4b --max-steps 20 --max-val-examples 16 2>&1 | tee reports/pilot-q35-4b.log | grep -v -E "^\\s*$|it/s\\]$"
import json
a = json.load(open('models/pilot-q35-4b/egitim_ayari.json'))
sn_adim = 1 / a['adim_per_sn']
print(f"\\nVRAM tepe {a['vram_tepe_mib']} MiB · {sn_adim:.1f} sn/adim · tam egitim (2250 adim, eval haric) ~ {2250*sn_adim/3600:.1f} saat")
"""),
        kod("""
# 5) Kisa cikarim: pilot adaptoru yukle, Turkce kesir sorusu sor (20 adimdan kalite beklenmez; boru hattini sinar)
import torch
from unsloth import FastLanguageModel
model, tok = FastLanguageModel.from_pretrained('models/pilot-q35-4b', max_seq_length=1792, load_in_4bit=True)
tok = getattr(tok, 'tokenizer', tok)
FastLanguageModel.for_inference(model)
for soru in ('3/4+1/2', '2/9 ile 5/6 sayılarını topla.'):
    metin = tok.apply_chat_template([{'role': 'user', 'content': soru}], tokenize=False,
                                    add_generation_prompt=True, enable_thinking=False)
    girdi = tok(metin, return_tensors='pt', add_special_tokens=False).to('cuda')
    cikti = model.generate(**girdi, max_new_tokens=300, do_sample=False)
    print('SORU:', soru, '\\n', tok.decode(cikti[0][girdi['input_ids'].shape[1]:], skip_special_tokens=True), '\\n' + '-' * 60)
del model; torch.cuda.empty_cache()
"""),
        kod("""
# 6) TAM EGITIM: arka planda baslar, bu hucre 5 dk'da bir ilerlemeyi yazar ve egitim bitene kadar calisir.
# Kopma olursa: hucre 1, 2, 3'u calistir, sonra DEVAM = True yapip bu hucreyi calistir (son checkpoint'ten surer).
import subprocess, time, json
DEVAM = False
ad = 'v2-q35-4b'
log, gecmis = f'reports/{ad}.log', f'reports/gecmis-{ad}.jsonl'
komut = f"python -X utf8 training/train.py --config configs/{ad}.json --ad {ad}" + (" --resume" if DEVAM else "")
p = subprocess.Popen(f"{komut} >> {log} 2>&1", shell=True)
print(time.strftime('%H:%M'), 'basladi | pid', p.pid, '|', komut, flush=True)
t0 = time.time()
while p.poll() is None:
    time.sleep(300)
    try:
        satirlar = [json.loads(x) for x in open(gecmis, encoding='utf-8') if x.strip()]
        tr = [x for x in satirlar if x.get('loss') is not None]
        ev = [x for x in satirlar if x.get('eval_loss') is not None]
        if tr:
            print(f"{time.strftime('%H:%M')} adim {tr[-1]['adim']}/2250  loss {tr[-1]['loss']:.4f}"
                  + (f"  | son eval {ev[-1]['eval_loss']:.4f} (adim {ev[-1]['adim']})" if ev else '')
                  + f"  | {(time.time()-t0)/60:.0f} dk", flush=True)
        else:
            print(time.strftime('%H:%M'), 'hazirlaniyor (model/veri/derleme)...', flush=True)
    except Exception as e:
        print('izleme:', e, flush=True)
print(time.strftime('%H:%M'), 'BITTI, cikis kodu', p.returncode)
!grep -E "^\\[(bitti|vram|kayit|en iyi)\\]|HATA|Error" {log} | tail -15
"""),
    ]
    nb = {
        "nbformat": 4, "nbformat_minor": 0,
        "metadata": {"colab": {"provenance": [], "gpuType": "L4", "name": CIKTI.name},
                     "kernelspec": {"name": "python3", "display_name": "Python 3"},
                     "language_info": {"name": "python"}, "accelerator": "GPU"},
        "cells": hucreler,
    }
    CIKTI.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazildi: {CIKTI} ({CIKTI.stat().st_size} bayt)")


if __name__ == "__main__":
    main()
