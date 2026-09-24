"""Browser chat for the Nano demo model, hosted on a remote GPU."""
import json
import os
from pathlib import Path
import secrets
import threading
import torch
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = 'HuggingFaceTB/SmolLM2-360M-Instruct'
ROOT = Path(__file__).resolve().parent
revision = os.environ['MODEL_REVISION']
tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=revision)
model = AutoModelForCausalLM.from_pretrained(MODEL, revision=revision, torch_dtype=torch.float16).to('cuda').eval()
lock = threading.Lock()

def respond(message, history):
    messages = [{'role': 'system', 'content': 'You are a helpful assistant. Give clear, concise answers.'}]
    for item in history[-8:]:
        if item['role'] in ('user', 'assistant') and isinstance(item['content'], str):
            messages.append({'role': item['role'], 'content': item['content'][:4000]})
    messages.append({'role': 'user', 'content': message[:4000]})
    while True:
        tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors='pt')
        if tokens.shape[-1] <= 1536 or len(messages) <= 2:
            break
        del messages[1:3]
    if tokens.shape[-1] > 1536:
        return 'Please shorten your message to fit this model’s context.'
    with lock, torch.inference_mode():
        tokens = tokens.to('cuda')
        result = model.generate(tokens, attention_mask=torch.ones_like(tokens), max_new_tokens=192,
                                do_sample=True, temperature=0.6, top_p=0.9,
                                pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(result[0, tokens.shape[-1]:], skip_special_tokens=True)

credentials = ROOT / 'access.json'
if not credentials.exists():
    credentials.write_text(json.dumps({'username': 'demo', 'password': secrets.token_urlsafe(15)}))
    credentials.chmod(0o600)
auth = json.loads(credentials.read_text())
app = gr.ChatInterface(respond, type='messages', title='SmolLM2 on A30',
                       description='Chat with the 360M model used in the Nano demonstration. This hosted copy uses GPU FP16 weights; the Nano uses Q4 CPU inference.',
                       examples=['Why does a steel ship float?', 'Explain language model tokens in two sentences.'],
                       theme=gr.themes.Soft(primary_hue='green'))
app.queue(default_concurrency_limit=1, max_size=8).launch(server_name='0.0.0.0', server_port=6006,
        auth=(auth['username'], auth['password']), show_error=False)
