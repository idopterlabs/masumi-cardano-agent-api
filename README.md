## Masumi Agent DeGen

Generates a fun comparison between two different Cardano Wallets

## Setup

1. **Create and activate a new Python virtual environment:**

```bash
python -m venv .venv && source .venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Plug your agent 🤖 :** The `execute_job` function is where your agent will be invoked. You might also want to change the logic for calculating the price and the shape of the inputs your agent accepts.

4. **Run your Agent API:** 

```bash
python main.py
```