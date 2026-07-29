# 🤖 Custom AI Model Training Guide

Complete step-by-step guide to train your own model using Kaggle datasets and replace the Groq API in this project.

---

## 🏆 Best Model: `Phi-3 Mini 3.8B`

| Model | Size | VRAM | Speed | Verdict |
|---|---|---|---|---|
| **Phi-3 Mini** ⭐ | 3.8B | 4 GB | Fast | **Best for you** |
| Llama 3.2 3B | 3B | 4 GB | Fast | Good alternative |
| Mistral 7B | 7B | 8 GB | Medium | Need better GPU |
| Llama 3 8B | 8B | 10 GB | Medium | Need high-end GPU |

> ✅ Phi-3 Mini runs on a regular laptop (CPU or 4GB GPU), is MIT licensed, and fine-tunes in ~1 hour on Google Colab free tier.

---

## Phase 1 — Get Dataset from Kaggle

### Step 1: Install Kaggle CLI

```bash
pip install kaggle
```

Get your API key:
1. Go to [kaggle.com](https://kaggle.com) → **Account → API → Create New Token**
2. Download `kaggle.json`
3. Place it at `C:\Users\<your-name>\.kaggle\kaggle.json`

### Step 2: Download Datasets

```bash
# Best dataset — SMS Spam Collection (747 scam messages)
kaggle datasets download -d uciml/sms-spam-collection
unzip sms-spam-collection.zip

# Optional: Email spam
kaggle datasets download -d nitishabharathi/email-spam-dataset
unzip email-spam-dataset.zip
```

### Step 3: Convert to Training Format

Save this as `convert_dataset.py` and run it:

```python
import pandas as pd
import json
import random

# Load Kaggle CSV
df = pd.read_csv("spam.csv", encoding="latin-1")
df = df[["v1", "v2"]]
df.columns = ["label", "message"]

# Keep only scam/spam rows
spam_df = df[df["label"] == "spam"]

# ── Reply pools by persona type ───────────────────────────────
confused_replies = [
    "Oh dear, I am so confused. Which account are you talking about?",
    "I need to ask my son before doing anything online. Can you call back tomorrow?",
    "This is very complicated for me. Can you explain slowly?",
    "I am not good with these things. Who are you exactly?",
    "I didn't understand. Can you repeat that in simple words?",
]

nervous_replies = [
    "This is making me very nervous. Let me check with my bank directly.",
    "I am scared now. Is this really from the bank?",
    "My daughter handles all this for me. Let me call her first.",
    "I will visit the branch tomorrow to sort this out.",
]

polite_replies = [
    "Thank you for informing me, but I would prefer to handle this in person.",
    "I appreciate your call. Let me consult my family and get back to you.",
    "Sorry to trouble you, but I don't feel comfortable doing this over phone.",
]

# ── Smart reply selection based on message keywords ───────────
def pick_reply(message: str) -> str:
    msg = message.lower()

    # Threatening / urgent messages → nervous reply
    if any(w in msg for w in ["block", "suspend", "legal", "action", "urgent", "immediately", "police"]):
        return random.choice(nervous_replies)

    # Payment / OTP / link messages → confused reply
    if any(w in msg for w in ["otp", "upi", "click", "link", "pay", "transfer", "verify", "account"]):
        return random.choice(confused_replies)

    # Prize / winning / offer messages → polite reply
    if any(w in msg for w in ["won", "prize", "free", "winner", "claim", "congratulations", "offer"]):
        return random.choice(polite_replies)

    # Default → random from all pools
    return random.choice(confused_replies + nervous_replies + polite_replies)

# ── Build training pairs ──────────────────────────────────────
pairs = []
for _, row in spam_df.iterrows():
    pairs.append({
        "prompt": row["message"],
        "completion": pick_reply(row["message"])
    })

# Save as JSONL
with open("scam_data.jsonl", "w") as f:
    for pair in pairs:
        f.write(json.dumps(pair) + "\n")

print(f"✅ Created {len(pairs)} training pairs → scam_data.jsonl")
```

```bash
python convert_dataset.py
# ✅ Created 747 training pairs → scam_data.jsonl
```

### Step 4: (Optional) Merge Multiple Datasets

```python
# merge_datasets.py
import glob, json, random

all_pairs = []
for file in glob.glob("*.jsonl"):
    with open(file) as f:
        for line in f:
            all_pairs.append(json.loads(line))

random.shuffle(all_pairs)

with open("final_training_data.jsonl", "w") as f:
    for pair in all_pairs:
        f.write(json.dumps(pair) + "\n")

print(f"✅ Total training pairs: {len(all_pairs)}")
```

---

## Phase 2 — Fine-Tune on Google Colab

### Step 5: Open Google Colab

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. **Runtime → Change runtime type → T4 GPU**
3. Upload your `final_training_data.jsonl`

### Step 6: Install Dependencies

```bash
!pip install -q transformers datasets peft trl bitsandbytes accelerate
```

### Step 7: Run the Training Script

```python
import json
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, SFTConfig
import torch

# ── 1. Load dataset ──────────────────────────────────────────
with open("final_training_data.jsonl") as f:
    data = [json.loads(line) for line in f]

def format_example(row):
    return {"text": f"### Scammer:\n{row['prompt']}\n\n### You:\n{row['completion']}"}

dataset = Dataset.from_list([format_example(r) for r in data])
dataset = dataset.train_test_split(test_size=0.1)

# ── 2. Load Phi-3 Mini in 4-bit (fits in free Colab GPU) ─────
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
)

model_id = "microsoft/Phi-3-mini-4k-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
model.config.use_cache = False

# ── 3. Apply LoRA (trains only ~1% of params — fast + cheap) ─
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: ~8M out of 3.8B (~0.2%)

# ── 4. Train ──────────────────────────────────────────────────
training_args = SFTConfig(
    output_dir="./honeypot-phi3",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=10,
    logging_steps=10,
    save_steps=50,
    fp16=True,
    max_seq_length=512,
    dataset_text_field="text",
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    args=training_args,
)

trainer.train()

# ── 5. Save ───────────────────────────────────────────────────
model.save_pretrained("./honeypot-phi3-final")
tokenizer.save_pretrained("./honeypot-phi3-final")
print("✅ Model saved!")
```

### Step 8: Download Your Trained Model

```python
import shutil
from google.colab import files

shutil.make_archive("honeypot-phi3-final", "zip", "./honeypot-phi3-final")
files.download("honeypot-phi3-final.zip")
```

---

## Phase 3 — Run Locally with Ollama

### Step 9: Install Ollama

Download from [ollama.com/download](https://ollama.com/download) and install.

### Step 10: Create a Modelfile

Create a file named `Modelfile` in your project root:

```dockerfile
FROM ./honeypot-phi3-final

SYSTEM """
You are a honey-pot agent that engages with scammers.
You play confused, scared, or hesitant victims to waste scammers' time.
Never reveal you are an AI. Stay in character. Keep replies under 2 sentences.
"""

PARAMETER temperature 0.7
PARAMETER num_predict 100
```

### Step 11: Register and Start

```bash
ollama create honeypot-agent -f ./Modelfile
ollama serve
# Running at http://localhost:11434
```

---

## Phase 4 — Integrate into Project

### Step 12: Update `agent.py`

Add this function and update `call_llm()`:

```python
import requests

def call_local_model(prompt: str) -> str:
    """Call your locally running fine-tuned model via Ollama."""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "honeypot-agent",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 100}
        },
        timeout=30
    )
    return response.json()["response"].strip()


def call_llm(prompt: str) -> str:
    """
    Hybrid strategy:
    1. Local Ollama (your fine-tuned model) — free & private
    2. Groq fallback
    3. Gemini fallback
    """
    try:
        return call_local_model(prompt)
    except Exception:
        logger.warning("Local model unavailable, falling back to Groq")

    if groq_client:
        try:
            result = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=settings.groq_model,
                max_tokens=150,
            )
            return result.choices[0].message.content.strip()
        except Exception:
            logger.warning("Groq failed, falling back to Gemini")

    response = gemini_model.generate_content(prompt)
    return response.text.strip()
```

---

## 📊 Timeline

| Phase | Time |
|---|---|
| Kaggle download + convert | 30 min |
| Colab setup + fine-tuning | 1–1.5 hrs |
| Download + Ollama setup | 20 min |
| Integration into project | 15 min |
| **Total** | **~2.5 hours** |

---

## ✅ Checklist

- [ ] Installed Kaggle CLI and placed `kaggle.json`
- [ ] Downloaded `sms-spam-collection` dataset
- [ ] Ran `convert_dataset.py` → got `scam_data.jsonl`
- [ ] (Optional) Merged multiple datasets into `final_training_data.jsonl`
- [ ] Opened Google Colab with T4 GPU
- [ ] Ran training script → model saved
- [ ] Downloaded `honeypot-phi3-final.zip`
- [ ] Installed Ollama and created `Modelfile`
- [ ] Ran `ollama serve`
- [ ] Updated `agent.py` with `call_local_model()`
- [ ] Tested with `test_api.sh` or `test_api.bat`

---

## 🧪 Test After Integration

```bash
curl -X POST http://localhost:8000/honeypot/message \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "test-01", "message": {"text": "Send OTP now or your account will be blocked!"}}'

# Expected: Your own trained model replies with a persona-based response 🎉
```
