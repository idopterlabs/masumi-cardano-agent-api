## Masumi Cardano Agent API

The Masumi [MIP-003](https://github.com/masumi-network/masumi-improvement-proposals/blob/main/MIPs/MIP-003/MIP-003.md) compliant API for the [JCat - Cardano Agent](https://github.com/idopterlabs/masumi-cardano-agent) created using the [Masumi Agent Template](https://github.com/idopterlabs/masumi-agent-template)

## Setup

1. **Create and activate a new Python virtual environment:**

```bash
python -m venv .venv && source .venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Set ENVs**: See `.env.example` as reference.

3. **Run the API:**

```bash
python main.py
```