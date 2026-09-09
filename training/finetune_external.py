#!/usr/bin/env python3
"""LoRA/QLoRA on a separate modern GPU, then merge for GGUF export.

This script is not for the original Nano. See docs/TRAINING.md.
"""
import argparse
import json
from pathlib import Path

BASE_MODEL = 'HuggingFaceTB/SmolLM2-135M-Instruct'
BASE_REVISION = '12fd25f77366fa6b3b4b768ec3050bf629380bac'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=['lora', 'qlora'], default='lora')
    parser.add_argument('--train', type=Path, help='JSONL records with prompt and response')
    parser.add_argument('--validation', type=Path, help='Separate held-out JSONL records')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--merge-adapter', type=Path, help='Merge a trusted adapter from this script, without training')
    parser.add_argument('--rank', type=int, default=8)
    parser.add_argument('--max-length', type=int, default=256)
    parser.add_argument('--epochs', type=float, default=1)
    parser.add_argument('--learning-rate', type=float, default=0.0002)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Choose a new output directory')
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                              DataCollatorForSeq2Seq, Trainer, TrainingArguments, set_seed)
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    set_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION)
    tokenizer.pad_token = tokenizer.eos_token
    if args.merge_adapter:
        base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, revision=BASE_REVISION, torch_dtype=torch.float32)
        merged = PeftModel.from_pretrained(base, str(args.merge_adapter)).merge_and_unload()
        merged.save_pretrained(str(args.output), safe_serialization=True)
        tokenizer.save_pretrained(str(args.output))
        print('Merged full-precision model:', args.output)
        return
    if not torch.cuda.is_available():
        raise RuntimeError('Training requires a separate CUDA-enabled GPU machine')
    if args.train is None or args.validation is None:
        raise ValueError('Provide separate --train and --validation JSONL files')
    if args.rank < 1 or args.max_length < 16 or args.epochs <= 0:
        raise ValueError('Use positive rank/epochs and max-length >= 16')
    quantization = None
    if args.method == 'qlora':
        if torch.cuda.get_device_capability()[0] < 6:
            raise RuntimeError('QLoRA example requires Pascal or newer. Original Nano is unsupported.')
        quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                                         bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, revision=BASE_REVISION,
                torch_dtype=torch.float16, quantization_config=quantization, device_map={'': 0})
    model.config.use_cache = False
    if quantization is not None:
        model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(r=args.rank, lora_alpha=2 * args.rank,
                lora_dropout=0.05, target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM'))
    model.print_trainable_parameters()

    def records(path):
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        if not rows:
            raise ValueError('Empty dataset: ' + str(path))
        for row in rows:
            if not all(isinstance(row.get(k), str) and row[k].strip() for k in ['prompt', 'response']):
                raise ValueError('Every row needs nonempty prompt and response strings')
        return rows

    training, validation = records(args.train), records(args.validation)
    train_pairs = {(r['prompt'], r['response']) for r in training}
    if any((r['prompt'], r['response']) in train_pairs for r in validation):
        raise ValueError('Exact duplicate examples appear in training and validation')

    def tokenize(rows):
        encoded = []
        for row in rows:
            messages = [{'role': 'user', 'content': row['prompt']}]
            prefix = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            full = tokenizer.apply_chat_template(messages + [{'role': 'assistant', 'content': row['response']}], tokenize=True)
            if full[:len(prefix)] != prefix:
                raise ValueError('Chat-template prefix mismatch')
            if len(full) > args.max_length:
                raise ValueError('Example exceeds max-length. Shorten it or increase --max-length.')
            labels = [-100] * len(prefix) + full[len(prefix):]
            if not any(x != -100 for x in labels):
                raise ValueError('Example contains no response tokens')
            encoded.append({'input_ids': full, 'attention_mask': [1] * len(full), 'labels': labels})
        return encoded

    trainer = Trainer(model=model,
        args=TrainingArguments(output_dir=str(args.output / 'trainer'), num_train_epochs=args.epochs,
            per_device_train_batch_size=1, per_device_eval_batch_size=1, gradient_accumulation_steps=8,
            learning_rate=args.learning_rate, fp16=True, logging_steps=10, save_strategy='no',
            eval_strategy='epoch', report_to='none', seed=args.seed, data_seed=args.seed),
        train_dataset=tokenize(training), eval_dataset=tokenize(validation),
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=None, label_pad_token_id=-100))
    trainer.train()
    model.save_pretrained(str(args.output / 'adapter'))
    tokenizer.save_pretrained(str(args.output / 'adapter'))
    (args.output / 'run.json').write_text(json.dumps({'base_model': BASE_MODEL, 'revision': BASE_REVISION,
        'method': args.method, 'seed': args.seed, 'rank': args.rank, 'max_length': args.max_length,
        'epochs': args.epochs, 'learning_rate': args.learning_rate, 'train_examples': len(training),
        'validation_examples': len(validation), 'torch': torch.__version__}, indent=2))
    print('Saved adapter:', args.output / 'adapter')


if __name__ == '__main__':
    main()
