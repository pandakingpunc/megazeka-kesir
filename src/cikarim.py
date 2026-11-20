"""Megazeka-Kesir modeliyle JSONL test sorularına yanıt üret."""

import argparse
import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
TABAN = "unsloth/Qwen2.5-1.5B-Instruct-unsloth-bnb-4bit"
YAYIN_ADAPTORU = "pandakingpunc/megazeka-kesir-qwen2.5-1.5b-tr"
MAKS_YENI_TOKEN = 512


def yukle(adapter=None):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TABAN, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(
        TABAN, device_map="cuda", dtype=torch.bfloat16
    )
    if adapter:
        from peft import PeftModel

        revision = "v1.0" if adapter == YAYIN_ADAPTORU else None
        model = PeftModel.from_pretrained(model, adapter, revision=revision)
    return tokenizer, model.eval()


def uret(tokenizer, model, sorular, max_new_tokens=MAKS_YENI_TOKEN):
    import torch

    metinler = [
        tokenizer.apply_chat_template(
            [{"role": "user", "content": soru}],
            tokenize=False,
            add_generation_prompt=True,
        )
        for soru in sorular
    ]
    girdiler = tokenizer(metinler, return_tensors="pt", padding=True).to(model.device)
    with torch.inference_mode():
        cikti = model.generate(
            **girdiler,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )
    yeni_tokenler = cikti[:, girdiler["input_ids"].shape[1]:]
    return [
        metin.strip()
        for metin in tokenizer.batch_decode(yeni_tokenler, skip_special_tokens=True)
    ]


def sorulari_oku(yol, limit):
    kayitlar = []
    with yol.open(encoding="utf-8") as dosya:
        for satir_no, satir in enumerate(dosya, start=1):
            if not satir.strip():
                continue
            try:
                kayit = json.loads(satir)
                soru = next(
                    mesaj["content"] for mesaj in kayit["messages"]
                    if mesaj["role"] == "user"
                )
                if not isinstance(soru, str):
                    raise ValueError("kullanıcı mesajının içeriği metin olmalı")
                kayitlar.append((kayit["meta"]["id"], soru))
            except (ValueError, KeyError, TypeError, StopIteration) as hata:
                raise ValueError(f"{yol}:{satir_no}: geçersiz test kaydı") from hata
            if limit and len(kayitlar) >= limit:
                break
    return kayitlar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", help="PEFT adaptör klasörü veya depo adı")
    parser.add_argument("--test", type=Path, default=KOK / "data" / "test.jsonl")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-new-tokens", type=int, default=MAKS_YENI_TOKEN)
    parser.add_argument("--limit", type=int, default=0, help="0 tüm kayıtları işler")
    args = parser.parse_args()
    if args.batch_size <= 0 or args.max_new_tokens <= 0 or args.limit < 0:
        parser.error("Grup boyutu ve yeni token sayısı pozitif, limit ise en az 0 olmalı.")
    if args.test.resolve() == args.out.resolve():
        parser.error("Test ve çıktı için ayrı dosya yolları verin.")

    try:
        kayitlar = sorulari_oku(args.test, args.limit)
    except (OSError, ValueError) as hata:
        parser.error(str(hata))
    if kayitlar:
        tokenizer, model = yukle(args.adapter)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as dosya:
        for baslangic in range(0, len(kayitlar), args.batch_size):
            grup = kayitlar[baslangic:baslangic + args.batch_size]
            tahminler = uret(tokenizer, model, [soru for _, soru in grup], args.max_new_tokens)
            for (kimlik, _), tahmin in zip(grup, tahminler, strict=True):
                kayit = {"id": kimlik, "prediction": tahmin}
                dosya.write(json.dumps(kayit, ensure_ascii=False) + "\n")
            dosya.flush()
            print(f"{baslangic + len(grup)}/{len(kayitlar)}", flush=True)


if __name__ == "__main__":
    main()
