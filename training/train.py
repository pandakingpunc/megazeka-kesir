"""Megazeka-Kesir QLoRA egitimi (Unsloth + TRL SFTTrainer).

Kullanim (Unsloth Studio ortaminin Python'u ile, proje kokunden):
  python -X utf8 training/train.py --config configs/v1.json --ad v1 [--max-steps N] [--max-val-examples N] [--resume]

Studio'nun v1'de kullandigi yolu izler: FastLanguageModel (4-bit) + get_peft_model, mesajlar
tokenizer sohbet sablonuyla "text" alanina duzlestirilir, SFTTrainer olusturulduktan sonra
unsloth.chat_templates.train_on_responses_only ile yalniz asistan yanitlarinda kayip hesaplanir.

Ciktilar:
  models/checkpoints/<ad>/checkpoint-N   kontrol noktalari
  models/<ad>/                           son adaptor + tokenizer + egitim_ayari.json
  models/<ad>-best/                      en dusuk val kaybindaki adaptor (best_info.json ile)
  reports/gecmis-<ad>.jsonl              baslangic satiri + her log adiminda kayip gecmisi
  Test degerlendirmesi ayri bir komutla calistirilir.
"""
import os
import sys

KOK_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Unsloth'un derlenmis trainer onbellegi cwd'ye degil proje icindeki .cache'e yazilsin.
os.environ.setdefault("UNSLOTH_COMPILE_LOCATION", os.path.join(KOK_, ".cache", "unsloth_compiled_cache"))
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import argparse
import datetime
import json
import math
import time
from pathlib import Path

KOK = Path(KOK_)
VARSAYILAN = {
    "logging_steps": 10,
    "optim": "adamw_8bit",
    "gradient_checkpointing": "unsloth",
    "save_total_limit": 3,
}
INSTRUCTION_PART = "<|im_start|>user\n"
RESPONSE_PART = "<|im_start|>assistant\n"
CEVAP_ONEKLERI = ("İşlem:", "Soru:", "Kesir:", "Sonuç:", "Okunuş:")


def yol(p):
    p = Path(p)
    return p if p.is_absolute() else KOK / p


def satir_say(p):
    with open(p, encoding="utf-8") as f:
        return sum(1 for s in f if s.strip())


def adim_hesapla(n, batch, ga, epochs, max_steps):
    if max_steps and max_steps > 0:
        return int(max_steps)
    return math.ceil(math.ceil(n / batch) / ga) * epochs


def adim_korumasi(n, cfg, max_steps, etiket):
    toplam = adim_hesapla(n, cfg["batch_size"], cfg["gradient_accumulation"], cfg["epochs"], max_steps)
    if toplam < cfg["warmup_steps"]:
        sys.exit(
            f"HATA ({etiket}): toplam optimizer adimi ({toplam}) < warmup_steps ({cfg['warmup_steps']}). "
            f"Ornek={n}, batch={cfg['batch_size']}, birikim={cfg['gradient_accumulation']}, epoch={cfg['epochs']}, "
            f"max_steps={max_steps}. Egitim baslatilmadi."
        )
    return toplam


def son_checkpoint(cikti):
    if not cikti.is_dir():
        return None
    cps = [d for d in cikti.glob("checkpoint-*") if d.name.split("-")[-1].isdigit()]
    return max(cps, key=lambda d: int(d.name.split("-")[-1])) if cps else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--ad", required=True)
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-val-examples", type=int)
    args = ap.parse_args()

    with open(yol(args.config), encoding="utf-8") as f:
        cfg_dosya = json.load(f)
    cfg = {**VARSAYILAN, **cfg_dosya}
    if args.max_steps is not None and args.max_steps < 1:
        ap.error("--max-steps pozitif olmali.")
    if args.max_val_examples is not None and args.max_val_examples < 1:
        ap.error("--max-val-examples pozitif olmali.")
    if args.max_steps is not None:
        cfg["max_steps"] = args.max_steps
    max_steps = cfg.get("max_steps", 0) or 0
    ad = args.ad
    if (max_steps > 0 or args.max_val_examples is not None) and not ad.startswith("pilot-"):
        ap.error("Sinirli calistirmalarda --ad pilot- ile baslamali.")

    train_yol, val_yol = yol(cfg["train"]), yol(cfg["val"])
    for p in (train_yol, val_yol):
        if not p.is_file():
            sys.exit(f"HATA: veri dosyasi yok: {p}")

    cikti = KOK / "models" / "checkpoints" / ad
    son_adaptor = KOK / "models" / ad
    en_iyi_dir = KOK / "models" / f"{ad}-best"
    gecmis_yol = KOK / "reports" / f"gecmis-{ad}.jsonl"
    gecmis_yol.parent.mkdir(parents=True, exist_ok=True)

    # Ucuz erken koruma: ham satir sayisiyla (model yuklemeden once).
    n_ham = satir_say(train_yol)
    if not n_ham or not satir_say(val_yol):
        sys.exit("HATA: egitim ve val veri dosyalari bos olamaz.")
    adim_korumasi(n_ham, cfg, max_steps, "ham veri")

    resume_cp = None
    if args.resume:
        resume_cp = son_checkpoint(cikti)
        if resume_cp is None:
            sys.exit(f"HATA: --resume verildi ama {cikti} altinda checkpoint yok.")

    # ---- agir importlar (unsloth, trl'den ve transformers'tan once) ----
    import unsloth  # noqa: F401
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import train_on_responses_only
    import torch
    import transformers
    import trl
    from datasets import load_dataset
    from transformers import TrainerCallback
    from trl import SFTConfig, SFTTrainer

    print(f"[surum] unsloth={unsloth.__version__} trl={trl.__version__} transformers={transformers.__version__} torch={torch.__version__}")
    if trl.__version__ != "0.23.1":
        sys.exit("HATA: TRL 0.23.1 gerekli. Unsloth Studio ortamini kullanin.")
    if not torch.cuda.is_available():
        sys.exit("HATA: CUDA yok.")

    # ---- model ----
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=cfg["taban"],
        max_seq_length=cfg["max_seq_length"],
        dtype=None,
        load_in_4bit=True,
        use_gradient_checkpointing=cfg["gradient_checkpointing"],
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=cfg["rank"],
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=cfg["alpha"],
        lora_dropout=cfg["dropout"],
        bias="none",
        use_gradient_checkpointing=cfg["gradient_checkpointing"],
        random_state=cfg["seed"],
        use_rslora=False,
    )

    # ---- veri: mesajlar -> sohbet sablonuyla "text" ----
    ds = load_dataset("json", data_files={"train": str(train_yol), "validation": str(val_yol)})
    if len(ds["train"]) != n_ham:
        sys.exit(f"HATA: egitim JSONL'de {n_ham} satir, yuklenen veri {len(ds['train'])} ornek.")
    if args.max_val_examples is not None:
        ds["validation"] = ds["validation"].select(range(min(args.max_val_examples, len(ds["validation"]))))

    beklenen = {}
    for etiket, dataset in ds.items():
        def metne(ornek, i):
            mesajlar = ornek["messages"]
            if [m["role"] for m in mesajlar] != ["user", "assistant"]:
                raise ValueError(f"{etiket}#{i + 1}: user ve assistant mesajlari sirayla gerekli.")
            for mesaj in mesajlar:
                icerik = mesaj["content"]
                if not isinstance(icerik, str) or not icerik.strip():
                    raise ValueError(f"{etiket}#{i + 1}: bos veya gecersiz mesaj.")
                if "<|im_start|>" in icerik or "<|im_end|>" in icerik:
                    raise ValueError(f"{etiket}#{i + 1}: mesaj iceriginde ChatML rol isareti.")
            return {"text": tokenizer.apply_chat_template(mesajlar, tokenize=False, add_generation_prompt=False)}

        metinler = dataset.map(metne, with_indices=True, remove_columns=dataset.column_names, num_proc=None)
        ids = []
        cevaplar = []
        en_uzun = 0
        for bas in range(0, len(dataset), 256):
            metin_grubu = metinler[bas:bas + 256]["text"]
            token_grubu = tokenizer(metin_grubu, add_special_tokens=False, truncation=False)["input_ids"]
            for i, tokenlar in enumerate(token_grubu, start=bas):
                uzunluk = len(tokenlar)
                if uzunluk > cfg["max_seq_length"]:
                    raise ValueError(
                        f"{etiket}#{i + 1}: {uzunluk} token, baglam siniri {cfg['max_seq_length']}."
                    )
                en_uzun = max(en_uzun, uzunluk)
                ids.append(tokenlar)
                cevaplar.append(dataset[i]["messages"][1]["content"])
        beklenen[etiket] = (ids, cevaplar)
        ds[etiket] = metinler
        print(f"[veri:{etiket}] ornek={len(dataset)} en_uzun={en_uzun} token")
    train_ds, val_ds = ds["train"], ds["validation"]

    bf16 = torch.cuda.is_bf16_supported()
    sft_args = dict(
        per_device_train_batch_size=cfg["batch_size"],
        per_device_eval_batch_size=cfg["batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation"],
        learning_rate=cfg["learning_rate"],
        lr_scheduler_type=cfg["scheduler"],
        warmup_steps=cfg["warmup_steps"],
        weight_decay=cfg["weight_decay"],
        optim=cfg["optim"],
        bf16=bf16,
        fp16=not bf16,
        seed=cfg["seed"],
        logging_steps=cfg["logging_steps"],
        eval_strategy="steps",
        eval_steps=cfg["eval_steps"],
        save_strategy="steps",
        save_steps=cfg["save_steps"],
        save_total_limit=cfg["save_total_limit"],
        output_dir=str(cikti),
        report_to="none",
        dataset_text_field="text",
        max_seq_length=cfg["max_seq_length"],
        max_length=cfg["max_seq_length"],  # TRL 0.23 varsayilani 1024; Unsloth once bunu okur
        packing=False,
        dataset_num_proc=1,        # Windows: multiprocessing sorun cikarir
        dataloader_num_workers=0,  # Windows
        gradient_checkpointing=True,
    )
    if max_steps > 0:
        sft_args["max_steps"] = max_steps
    else:
        sft_args["num_train_epochs"] = cfg["epochs"]

    # ---- geri cagirimlar: kayip gecmisi + en iyi val adaptoru ----
    gecmis_son = {"loss": None, "eval_loss": None}

    class Gecmis(TrainerCallback):
        def on_log(self, args_, state, control, logs=None, **kw):
            if not logs or not ("loss" in logs or "eval_loss" in logs):
                return
            kayit = {
                "adim": state.global_step,
                "epoch": logs.get("epoch"),
                "loss": logs.get("loss"),
                "eval_loss": logs.get("eval_loss"),
                "lr": logs.get("learning_rate"),
                "grad_norm": logs.get("grad_norm"),
            }
            if kayit["loss"] is not None:
                gecmis_son["loss"] = kayit["loss"]
            if kayit["eval_loss"] is not None:
                gecmis_son["eval_loss"] = kayit["eval_loss"]
            with open(gecmis_yol, "a", encoding="utf-8") as f:
                f.write(json.dumps(kayit, ensure_ascii=False) + "\n")

    en_iyi = {"loss": float("inf"), "adim": None}
    if args.resume and (en_iyi_dir / "best_info.json").is_file():
        bilgi = json.loads((en_iyi_dir / "best_info.json").read_text(encoding="utf-8"))
        en_iyi = {"loss": bilgi["eval_loss"], "adim": bilgi["adim"]}

    class EnIyi(TrainerCallback):
        trainer = None

        def on_evaluate(self, args_, state, control, metrics=None, **kw):
            el = (metrics or {}).get("eval_loss")
            if el is None or not math.isfinite(el) or el >= en_iyi["loss"]:
                return
            en_iyi.update(loss=el, adim=state.global_step)
            en_iyi_dir.mkdir(parents=True, exist_ok=True)
            self.trainer.model.save_pretrained(str(en_iyi_dir))
            tokenizer.save_pretrained(str(en_iyi_dir))
            (en_iyi_dir / "best_info.json").write_text(
                json.dumps({"adim": state.global_step, "eval_loss": el}, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[en iyi] adim {state.global_step}: eval_loss={el:.4f} -> {en_iyi_dir}")

    gecmis_cb, en_iyi_cb = Gecmis(), EnIyi()
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        args=SFTConfig(**sft_args),
        callbacks=[gecmis_cb, en_iyi_cb],
    )
    en_iyi_cb.trainer = trainer

    # ---- yalniz asistan yanitlarinda kayip (Studio ile ayni yol) ----
    trainer = train_on_responses_only(
        trainer,
        instruction_part=INSTRUCTION_PART,
        response_part=RESPONSE_PART,
        num_proc=1,
    )
    n_train, n_val = len(trainer.train_dataset), len(trainer.eval_dataset)
    for etiket, dataset in (("train", trainer.train_dataset), ("validation", trainer.eval_dataset)):
        ids_beklenen, cevaplar = beklenen[etiket]
        if len(dataset) != len(ids_beklenen):
            raise ValueError(f"{etiket}: {len(ids_beklenen)} ornekten {len(dataset)} ornek kaldi.")
        onek_hatasi = 0
        for i, satir in enumerate(dataset):
            ids, labels = satir["input_ids"], satir["labels"]
            if ids != ids_beklenen[i] or len(labels) != len(ids):
                raise ValueError(f"{etiket}#{i + 1}: tokenlar degisti, kesildi veya etiket uzunlugu uyusmuyor.")
            egitilen = [j for j, label in enumerate(labels) if label != -100]
            if not egitilen or egitilen[0] == 0 or egitilen != list(range(egitilen[0], egitilen[-1] + 1)):
                raise ValueError(f"{etiket}#{i + 1}: yanit maskesi bos veya kesintili.")
            if any(labels[j] != ids[j] for j in egitilen):
                raise ValueError(f"{etiket}#{i + 1}: egitim etiketleri tokenlarla uyusmuyor.")
            metin = tokenizer.decode([labels[j] for j in egitilen], clean_up_tokenization_spaces=False)
            if metin != cevaplar[i] + "<|im_end|>":
                raise ValueError(f"{etiket}#{i + 1}: maske tam asistan cevabini ve bitis tokenini kapsamiyor.")
            onek_hatasi += not cevaplar[i].startswith(CEVAP_ONEKLERI)
        print(f"[maske:{etiket}] {len(dataset)} ornek dogrulandi, beklenen onek disinda={onek_hatasi}")
    del beklenen

    # ---- adim bilgisi + koruma (maskeleme sonrasi gercek ornek sayisiyla) ----
    efektif = cfg["batch_size"] * cfg["gradient_accumulation"]
    toplam_adim = adim_korumasi(n_train, cfg, max_steps, "maske sonrasi")
    bilgi = {
        "tip": "baslangic",
        "tarih": datetime.datetime.now().isoformat(timespec="seconds"),
        "ad": ad,
        "ornek_sayisi_egitim": n_train,
        "ornek_sayisi_val": n_val,
        "batch_size": cfg["batch_size"],
        "gradient_accumulation": cfg["gradient_accumulation"],
        "efektif_batch": efektif,
        "epoch": cfg["epochs"],
        "max_steps": max_steps or None,
        "toplam_optimizer_adimi": toplam_adim,
        "warmup_steps": cfg["warmup_steps"],
        "surumler": {"unsloth": unsloth.__version__, "trl": trl.__version__, "transformers": transformers.__version__},
    }
    print(f"[plan] egitim={n_train} val={n_val} efektif_batch={efektif} toplam_optimizer_adimi={toplam_adim} warmup={cfg['warmup_steps']}")
    mod = "a" if args.resume else "w"
    with open(gecmis_yol, mod, encoding="utf-8") as f:
        if args.resume:
            bilgi["tip"] = "devam"
            bilgi["checkpoint"] = resume_cp.name
        f.write(json.dumps(bilgi, ensure_ascii=False) + "\n")

    # ---- egitim ----
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    sonuc = trainer.train(resume_from_checkpoint=str(resume_cp) if resume_cp else None)
    sure = time.time() - t0
    if trainer.state.global_step != toplam_adim:
        raise RuntimeError(f"Tamamlanan adim {trainer.state.global_step} != planlanan {toplam_adim}.")
    # son adimda degerlendirme yapilmadiysa yap (best callback'i de tetikler)
    if not any(h.get("eval_loss") is not None and h["step"] == trainer.state.global_step for h in trainer.state.log_history):
        trainer.evaluate()
    if not all(x is not None and math.isfinite(x) for x in gecmis_son.values()):
        raise RuntimeError(f"Egitim veya val kaybi gecersiz: {gecmis_son}")
    vram = torch.cuda.max_memory_allocated() / 2**20
    vram_ayrilan = torch.cuda.max_memory_reserved() / 2**20
    adim_sn = trainer.state.global_step / sure if sure else None
    print(f"[bitti] adim={trainer.state.global_step} sure={sure:.1f}s adim/sn={adim_sn:.3f} "
          f"son_loss={gecmis_son['loss']} son_eval_loss={gecmis_son['eval_loss']}")
    print(f"[vram] tepe max_memory_allocated={vram:.0f} MiB (reserved {vram_ayrilan:.0f} MiB)")

    # ---- son adaptor ----
    son_adaptor.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(son_adaptor))
    tokenizer.save_pretrained(str(son_adaptor))
    ayar = {
        "ad": ad,
        "config": cfg,
        "max_val_examples": args.max_val_examples,
        "tarih": datetime.datetime.now().isoformat(timespec="seconds"),
        "toplam_adim": trainer.state.global_step,
        "son_egitim_kaybi": gecmis_son["loss"],
        "son_degerlendirme_kaybi": gecmis_son["eval_loss"],
        "en_iyi_degerlendirme_kaybi": None if en_iyi["adim"] is None else en_iyi["loss"],
        "en_iyi_adim": en_iyi["adim"],
        "egitim_ornek_sayisi": n_train,
        "val_ornek_sayisi": n_val,
        "efektif_batch": efektif,
        "egitim_suresi_sn": round(sure, 1),
        "adim_per_sn": None if adim_sn is None else round(adim_sn, 4),
        "vram_tepe_mib": round(vram),
        "surumler": bilgi["surumler"],
    }
    (son_adaptor / "egitim_ayari.json").write_text(json.dumps(ayar, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[kayit] son adaptor -> {son_adaptor}" + (f"; en iyi (adim {en_iyi['adim']}, eval_loss {en_iyi['loss']:.4f}) -> {en_iyi_dir}" if en_iyi["adim"] else ""))


if __name__ == "__main__":
    main()
