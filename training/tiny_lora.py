#!/usr/bin/env python3
"""Tiny character transformer with ordinary LoRA. Requires compatible PyTorch >=1.10.

Educational full-precision training, not QLoRA and not a pretrained assistant.
"""
import argparse
import hashlib
import math
import random
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['base', 'adapt', 'generate'])
    parser.add_argument('--text', type=Path, help='Your real UTF-8 training corpus')
    parser.add_argument('--checkpoint', type=Path, help='Trusted checkpoint from this script')
    parser.add_argument('--output', type=Path, default=Path('runs/tiny.pt'))
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--steps', type=int, default=250)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--context', type=int, default=64)
    parser.add_argument('--dim', type=int, default=64)
    parser.add_argument('--heads', type=int, default=4)
    parser.add_argument('--layers', type=int, default=2)
    parser.add_argument('--rank', type=int, default=4)
    parser.add_argument('--learning-rate', type=float, default=0.001)
    parser.add_argument('--prompt', default='The ')
    parser.add_argument('--tokens', type=int, default=128)
    args = parser.parse_args()
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    if args.device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable. Install a matching JetPack PyTorch wheel or use --device cpu.')
    if min(args.steps, args.batch_size, args.context, args.dim, args.heads, args.layers, args.rank, args.tokens) < 1:
        raise ValueError('Sizes and step counts must be positive')
    if args.dim % args.heads:
        raise ValueError('dim must be divisible by heads')
    torch.set_num_threads(4)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if args.device == 'cuda':
        torch.cuda.manual_seed_all(args.seed)
    saved = None
    if args.stage != 'base':
        if args.checkpoint is None:
            raise ValueError('Provide --checkpoint for adapt or generate')
        saved = torch.load(str(args.checkpoint), map_location='cpu')
        config, vocab = saved['config'], saved['vocab']
    else:
        if args.text is None:
            raise ValueError('Provide --text with your corpus')
        vocab = sorted(set(args.text.read_text(encoding='utf-8')))
        config = {'context': args.context, 'dim': args.dim, 'heads': args.heads,
                  'layers': args.layers, 'rank': args.rank}
    stoi = {ch: i for i, ch in enumerate(vocab)}

    class LoRALinear(nn.Module):
        def __init__(self, in_features, out_features):
            super().__init__()
            self.base = nn.Linear(in_features, out_features)
            self.lora_a = nn.Parameter(torch.randn(config['rank'], in_features) * 0.02)
            self.lora_b = nn.Parameter(torch.zeros(out_features, config['rank']))
            self.enabled = False

        def forward(self, x):
            out = self.base(x)
            if self.enabled:
                out = out + F.linear(F.linear(x, self.lora_a), self.lora_b)
            return out

    class Block(nn.Module):
        def __init__(self):
            super().__init__()
            d = config['dim']
            self.norm1, self.norm2 = nn.LayerNorm(d), nn.LayerNorm(d)
            self.q, self.k, self.v, self.proj = [LoRALinear(d, d) for _ in range(4)]
            self.up, self.down = LoRALinear(d, 4 * d), LoRALinear(4 * d, d)

        def forward(self, x):
            b, t, d = x.shape
            h = config['heads']
            z = self.norm1(x)
            q, k, v = [layer(z).view(b, t, h, d // h).transpose(1, 2) for layer in (self.q, self.k, self.v)]
            scores = q @ k.transpose(-2, -1) / math.sqrt(d // h)
            mask = torch.ones(t, t, device=x.device, dtype=torch.bool).triu(1)
            weights = F.softmax(scores.masked_fill(mask, float('-inf')), dim=-1)
            attention = (weights @ v).transpose(1, 2).contiguous().view(b, t, d)
            x = x + self.proj(attention)
            return x + self.down(F.gelu(self.up(self.norm2(x))))

    class TinyLM(nn.Module):
        def __init__(self):
            super().__init__()
            self.tokens = nn.Embedding(len(vocab), config['dim'])
            self.positions = nn.Embedding(config['context'], config['dim'])
            self.blocks = nn.ModuleList([Block() for _ in range(config['layers'])])
            self.norm = nn.LayerNorm(config['dim'])
            self.head = nn.Linear(config['dim'], len(vocab))

        def forward(self, ids):
            x = self.tokens(ids) + self.positions(torch.arange(ids.shape[1], device=ids.device))
            for block in self.blocks:
                x = block(x)
            return self.head(self.norm(x))

    model = TinyLM().to(args.device)
    if saved:
        model.load_state_dict(saved['state_dict'])
    enabled = args.stage == 'adapt' or (saved is not None and saved['adapted'])
    for module in model.modules():
        if isinstance(module, LoRALinear):
            module.enabled = enabled
    for name, parameter in model.named_parameters():
        parameter.requires_grad_(('lora_' in name) if args.stage == 'adapt' else ('lora_' not in name))
    print('Parameters:', sum(p.numel() for p in model.parameters()),
          'trainable:', sum(p.numel() for p in model.parameters() if p.requires_grad))

    def encode(text):
        unknown = set(text) - set(vocab)
        if unknown:
            raise ValueError('Characters absent from base vocabulary: ' + repr(sorted(unknown)))
        return torch.tensor([stoi[ch] for ch in text], dtype=torch.long)

    if args.stage == 'generate':
        ids = encode(args.prompt)
        if not len(ids):
            raise ValueError('Prompt cannot be empty')
        ids = ids.unsqueeze(0).to(args.device)
        model.eval()
        with torch.no_grad():
            for _ in range(args.tokens):
                logits = model(ids[:, -config['context']:])[:, -1, :]
                next_id = torch.multinomial(F.softmax(logits, dim=-1), 1)
                ids = torch.cat((ids, next_id), dim=1)
        print(''.join(vocab[i] for i in ids[0].tolist()))
        return
    if args.text is None:
        raise ValueError('Provide --text with the training/adaptation corpus')
    corpus = args.text.read_text(encoding='utf-8')
    encoded = encode(corpus)
    split = int(len(encoded) * 0.9)
    train, valid = encoded[:split], encoded[split:]
    context = config['context']
    if min(len(train), len(valid)) <= context:
        raise ValueError('Need at least context+1 characters in each 90/10 split. Supply a longer corpus.')
    if args.output.exists():
        raise FileExistsError('Choose a new --output to preserve the previous experiment')
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.learning_rate)

    def batch(sequence, generator):
        starts = torch.randint(len(sequence) - context, (args.batch_size,), generator=generator)
        x = torch.stack([sequence[i:i + context] for i in starts.tolist()]).to(args.device)
        y = torch.stack([sequence[i + 1:i + context + 1] for i in starts.tolist()]).to(args.device)
        return x, y

    train_rng = torch.Generator().manual_seed(args.seed)
    valid_rng = torch.Generator().manual_seed(args.seed + 1)
    vx, vy = batch(valid, valid_rng)
    for step in range(args.steps):
        model.train()
        x, y = batch(train, train_rng)
        loss = F.cross_entropy(model(x).reshape(-1, len(vocab)), y.reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
        optimizer.step()
        if step == 0 or (step + 1) % 50 == 0 or step + 1 == args.steps:
            model.eval()
            with torch.no_grad():
                validation = F.cross_entropy(model(vx).reshape(-1, len(vocab)), vy.reshape(-1)).item()
            print('step={} train_loss={:.4f} fixed_val_batch_loss={:.4f}'.format(step + 1, loss.item(), validation))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({'state_dict': model.cpu().state_dict(), 'config': config, 'vocab': vocab,
                'adapted': enabled, 'seed': args.seed, 'steps': args.steps,
                'learning_rate': args.learning_rate, 'batch_size': args.batch_size,
                'corpus_sha256': hashlib.sha256(corpus.encode('utf-8')).hexdigest(),
                'torch_version': torch.__version__, 'device': args.device}, str(args.output))
    print('Saved', args.output)


if __name__ == '__main__':
    main()
