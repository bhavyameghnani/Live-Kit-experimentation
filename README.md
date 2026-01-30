# 🤖 Universal Investment Advisor Agent

A real-time voice agent that gives investment advice through LiveKit. Swap clients instantly by changing one file—**no code changes needed**.

---

## What It Does

- 🎤 Listens to client speech in real-time
- 💬 Responds as an AI investment advisor
- 📊 Gives personalized advice based on client profile
- 📡 Broadcasts conversation to your frontend
- 🔄 **Switch clients by swapping knowledge files**

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -e .
```

### 2. Set Up Environment
Create `.env.local` in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
LIVEKIT_URL=ws://your-livekit-server:7880
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
DEEPGRAM_API_KEY=your_deepgram_key
```

### 3. Run the Agent
```bash
python agent.py console
```

The agent will:
- Connect to LiveKit
- Wait for a client to join
- Start the conversation automatically

---

## Project Structure

```
.
├── agent.py              ← The "Operating System" (don't change)
├── knowledge.py          ← Client profile (Taro Nomura)
├── knowledge_jane.py     ← Alternative client (Jane Chen)
├── README.md
├── .gitignore
└── pyproject.toml
```

---

## 🔄 How It Works: Cartridge System

### The Concept
- **`agent.py`** = Universal advisor engine (stays the same)
- **`knowledge.py`** = Client configuration (swap to change behavior)

### Switch Clients in 1 Line

**For Taro Nomura** (Japanese investor, wealth preservation):
```python
import knowledge
```

**For Jane Chen** (Tech startup founder, growth investing):
```python
import knowledge_jane as knowledge
```

No other changes needed. The agent adapts automatically.

---

## What's in Each Knowledge File?

Each `knowledge_*.py` file contains:

```python
MISSION_CONTEXT = {
    "agent_persona": {
        "name": "Advisor name",
        "tone": "How they talk",
        "key_qualities": [...]
    },
    
    "client": {
        "name": "Client name",
        "financial_status": {...},
        "psychology": {...}  # Pain points, fears, needs
    },
    
    "strategy": {
        "primary_driver": "Market thesis",
        "key_talking_points": [...]
    },
    
    "inventory": {
        "recommended_buys": [...],
        "watchlist": [...],
        "sectors_to_avoid": [...]
    },
    
    "instructions": {
        "opening_hook": "How to start",
        "objection_handler_*": "How to respond to client concerns"
    }
}
```

---

## 🛠️ Creating a New Client

1. Copy `knowledge.py` to `knowledge_mynewclient.py`
2. Update all the fields with your new client's info
3. Change the import in `agent.py`:
   ```python
   import knowledge_mynewclient as knowledge
   ```
4. Done!

---

## 📊 Current Clients

### Taro Nomura 🇯🇵
- **Role**: Corporate executive  
- **Style**: Old money, calm, thoughtful  
- **Strategy**: Defense sector + policy pivot  
- **Stocks**: Tokyo Keiki, Mitsubishi Heavy, Shin-Etsu

### Jane Chen 💻
- **Role**: Startup founder  
- **Style**: Fast-paced, energetic, cutting-edge  
- **Strategy**: AI infrastructure + crypto  
- **Stocks**: NVIDIA, MicroStrategy, Broadcom

---

## 📡 Real-Time Features

### Transcript Broadcasting
- Client speech → logged + sent to frontend
- Agent speech → logged + sent to frontend
- Frontend receives via WebSocket data channel

### Voice Quality
- **STT**: Deepgram Nova-2 (high accuracy)
- **LLM**: Groq Llama 3.3 70B (fast, intelligent)
- **TTS**: Deepgram Aura (natural sounding)
- **VAD**: Silero (detects when client is speaking)

---

## 🔧 Customization

### Change the Greeting
Edit `instructions["opening_hook"]` in your knowledge file:
```python
"opening_hook": "Hello {client_name}, let's talk about {liquid_capital}..."
```

### Change LLM Model
Edit `agent.py` line ~270:
```python
llm=groq.LLM(model="your-model-here")
```

### Change Voice
Edit `agent.py` line ~265:
```python
tts=TranscriptCaptureTTS(model="your-voice-here")
```

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to LiveKit | Check `.env.local` credentials and server URL |
| Client not recognized | Verify client is in same room with unique identity |
| No transcript appearing | Check frontend is listening on "transcript" data channel |
| Poor speech quality | Adjust VAD parameters in `agent.py` entrypoint() |
| Agent is too slow | Check Groq API status |

---

## 📝 Environment Variables

| Variable | Required | Example |
|----------|----------|---------|
| `GROQ_API_KEY` | ✅ | `gsk_xxx...` |
| `LIVEKIT_URL` | ✅ | `ws://localhost:7880` |
| `LIVEKIT_API_KEY` | ✅ | `devkey` |
| `LIVEKIT_API_SECRET` | ✅ | `secret123` |

---

## 🎬 Production Checklist

- [ ] API keys configured (don't commit `.env.local`)
- [ ] LiveKit server running and reachable
- [ ] Dependencies installed (`pip install -e .`)
- [ ] Test connection with sample client
- [ ] Verify transcript reaches frontend
- [ ] Check logs for errors
- [ ] Use production LiveKit deployment

---

## 📚 File Breakdown

| File | Purpose |
|------|---------|
| `agent.py` | Main agent orchestration, speech processing, LiveKit integration |
| `knowledge.py` | Taro Nomura client config (wealth preservation) |
| `knowledge_jane.py` | Jane Chen client config (growth investing) |
| `pyproject.toml` | Dependencies and project metadata |
| `.gitignore` | Excludes Python, logs, env files, IDE files |
| `README.md` | This file |

---

## 🤝 Support

For issues, check the logs:
```bash
# Agent logs to console + application logger
# Look for AGENT_SAID, USER_SAID, and error messages
```

---

**Ready to deploy?** Swap `knowledge.py`, set your `.env.local`, and run!

