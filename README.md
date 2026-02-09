# Multi-Agent Voice Assistant

A sophisticated multi-agent voice assistant system built with LiveKit Agents that seamlessly coordinates between a **Wealth Advisor** and **Real Estate Expert**. The system intelligently hands off conversations between specialized agents based on user questions, providing expert advice across financial planning and real estate domains.

## Key Features

- **🤝 Intelligent Agent Handoff**: Automatic context-aware switching between Wealth Advisor and Real Estate Expert
- **🎨 Visual Agent Distinction**: Color-coded transcript with blue borders for Wealth Advisor and green for Real Estate Expert
- **🗣️ Natural Voice Interaction**: Real-time voice conversation with Deepgram STT/TTS
- **🧠 Powered by Groq LLM**: Uses llama-3.3-70b-versatile model for intelligent responses
- **💬 Full Transcript**: Complete conversation history with agent labels and smooth transitions
- **🎯 Specialized Knowledge**: Each agent has domain-specific expertise and can seamlessly transfer when needed

## The Agents

### 💼 Wealth Advisor (Primary Agent)
- **Visual Identity**: Blue color scheme
- **Expertise**: Financial planning, investment strategies, retirement planning, tax optimization
- **Personality**: Professional, analytical, detail-oriented financial expert
- **Handoff Trigger**: Detects questions about real estate and seamlessly transfers to the Real Estate Expert

### 🏡 Real Estate Expert
- **Visual Identity**: Green color scheme
- **Expertise**: Property investment, market analysis, real estate portfolio strategy
- **Personality**: Knowledgeable real estate professional with market insights
- **Handoff Trigger**: Returns to Wealth Advisor when financial planning questions arise

## Tech Stack

### Backend
- **LiveKit Agents SDK** (v1.3.12) - Voice agent framework
- **Python 3.13+** - Core runtime
- **Groq LLM** - llama-3.3-70b-versatile model (temperature=0 for consistency)
- **Deepgram** - Speech-to-text and text-to-speech
- **Custom FilteredTTS** - Removes function call syntax from speech output

### Frontend
- **Next.js 15** - React framework with Turbopack
- **TypeScript** - Type-safe development
- **LiveKit Components** - Pre-built UI components for voice agents
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Beautiful, customizable UI components

## Project Structure

```
multi-agent-livekit-call/
├── agent.py                    # Main agent entry point with handoff logic
├── agents/
│   ├── wealth_advisor.py       # Wealth Advisor agent definition
│   ├── real_estate_expert.py   # Real Estate Expert agent definition
│   └── utils.py                # Shared agent utilities
├── knowledge/
│   ├── wealth.py               # Wealth advisor knowledge base
│   └── real_estate.py          # Real estate knowledge base
├── app/
│   ├── page.tsx                # Main page
│   └── api/
│       └── connection-details/ # LiveKit connection endpoint
├── components/
│   ├── agents-ui/              # Enhanced LiveKit agent components
│   │   └── agent-chat-transcript.tsx  # ⭐ Visual agent distinction
│   ├── app/                    # Application components
│   │   ├── session-view.tsx    # Session management
│   │   └── chat-transcript.tsx # Transcript coordinator
│   └── ui/                     # Base UI components
├── .env.local                  # Environment configuration
└── package.json                # Dependencies
```

### Key Files

| File | Description |
|------|-------------|
| `agent.py` | Python backend that initializes both agents and handles LiveKit session |
| `agents/wealth_advisor.py` | Wealth Advisor agent class with financial expertise |
| `agents/real_estate_expert.py` | Real Estate Expert agent with property knowledge |
| `knowledge/wealth.py` | Financial planning context and knowledge base |
| `knowledge/real_estate.py` | Real estate market data and strategies |
| `components/agents-ui/agent-chat-transcript.tsx` | Enhanced transcript with visual agent distinction (blue/green) |
| `components/app/session-view.tsx` | Manages LiveKit session and UI state |

## How It Works

### Agent Handoff System

The multi-agent system uses intelligent conversation analysis to determine when to hand off between agents:

1. **Wealth Advisor** starts the conversation by default
2. When user asks about real estate, the Wealth Advisor says: *"Let me connect you with our real estate expert..."*
3. System seamlessly transitions to **Real Estate Expert** (visual indicator changes to green)
4. When financial planning topics come up, Real Estate Expert says: *"I'm back to help with your wealth planning..."*
5. Control returns to **Wealth Advisor** (visual indicator returns to blue)

### Visual Agent Distinction

The transcript UI (`agent-chat-transcript.tsx`) provides clear visual feedback:

- **`tagMessagesWithAgent()`**: Analyzes conversation flow and tags each message with the speaking agent
- **`detectAgentFromMessage()`**: Detects handoff phrases like "real estate expert" or "I'm back"
- **`getAgentStyles()`**: Returns agent-specific CSS classes
  - Wealth Advisor: `border-l-blue-500 bg-blue-50/50 dark:bg-blue-950/20`
  - Real Estate Expert: `border-l-green-500 bg-green-50/50 dark:bg-green-950/20`
- **Agent Labels**: Display "Wealth Advisor" or "Real Estate Expert" on first message from each agent

### Speech Output Filtering

Custom `FilteredTTS` class removes function call syntax from speech:
- Filters out patterns like `**transferToAgent(...)`, `**calculate(...)`, etc.
- Ensures natural, clean voice output without technical artifacts
- Maintains conversation flow during agent transitions

## Getting Started

### Prerequisites

- **Node.js** 18+ and **pnpm** (or npm/yarn)
- **Python** 3.13+
- **LiveKit account** (free at [livekit.io](https://livekit.io))
- **Groq API key** (free at [console.groq.com](https://console.groq.com))
- **Deepgram API key** (free at [deepgram.com](https://deepgram.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd multi-agent-livekit-call
   ```

2. **Install frontend dependencies**
   ```bash
   pnpm install
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r req.txt
   ```

4. **Configure environment variables**
   
   Create `.env.local` in the root directory:
   ```env
   # LiveKit Configuration
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   
   # AI Services
   GROQ_API_KEY=your_groq_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   ```

### Running the Application

1. **Start the Python agent backend**
   ```bash
   python agent.py dev
   ```
   
   This starts the LiveKit agent with both Wealth Advisor and Real Estate Expert.

2. **Start the Next.js frontend** (in a separate terminal)
   ```bash
   pnpm dev
   ```
   
   Open [http://localhost:3000](http://localhost:3000) in your browser.

3. **Start a conversation**
   - Click "Start call" to begin
   - Try asking: "What's a good investment strategy for retirement?"
   - Then: "What about real estate investment opportunities?"
   - Watch the agent smoothly hand off and the UI change colors!

## Customization

### Adding New Agents

1. Create a new agent file in `agents/` (e.g., `tax_specialist.py`)
2. Define agent personality and knowledge in `knowledge/`
3. Add handoff logic in `agent.py`
4. Update `agent-chat-transcript.tsx` to add new color scheme
5. Define detection phrase in `detectAgentFromMessage()`

### Modifying Agent Personalities

Edit the system prompts in:
- `agents/wealth_advisor.py` - Wealth Advisor personality and expertise
- `agents/real_estate_expert.py` - Real Estate Expert tone and knowledge

### Changing Visual Styles

Update colors in `components/agents-ui/agent-chat-transcript.tsx`:
```typescript
function getAgentStyles(agent: string | null) {
  switch (agent) {
    case 'wealth':
      return 'border-l-blue-500 bg-blue-50/50 dark:bg-blue-950/20';
    case 'real_estate':
      return 'border-l-green-500 bg-green-50/50 dark:bg-green-950/20';
    // Add your custom agent colors here
  }
}
```

## Configuration

### App Configuration (`app-config.ts`)

Customize branding and features:

```typescript
export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Your Company',
  pageTitle: 'Multi-Agent Financial Advisor',
  pageDescription: 'AI-powered wealth and real estate advice',
  
  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  
  startButtonText: 'Start Consultation',
  // ... other settings
};
```

### Agent Configuration

Modify agent behavior in respective files:
- **Temperature**: Set to 0 in `agent.py` for deterministic responses
- **Model**: Currently uses `llama-3.3-70b-versatile` (Groq)
- **Voice**: Deepgram's `aura-asteria-en` for natural speech

## Architecture Highlights

### Frontend
- **React Components**: Modular, reusable UI components
- **Real-time Updates**: LiveKit SDK for instant transcript updates
- **Performance**: `useMemo` for efficient agent tag computation
- **Responsive**: Works on desktop and mobile browsers

### Backend
- **Multi-Agent Pattern**: Clean separation of agent responsibilities
- **Knowledge Separation**: Modular knowledge bases for each domain
- **Session Management**: LiveKit handles connection lifecycle
- **Error Handling**: Graceful fallbacks and reconnection logic

## Troubleshooting

### Frontend won't start
```bash
# Clear dependencies and reinstall
rm -rf node_modules .next
pnpm install
pnpm dev
```

### Agent won't connect
- Verify `.env.local` has correct LiveKit credentials
- Check LiveKit project is active at [cloud.livekit.io](https://cloud.livekit.io)
- Ensure Python agent is running (`python agent.py dev`)

### No audio
- Check microphone permissions in browser
- Verify Deepgram API key is valid
- Test with browser console open to see errors

### Agent doesn't hand off
- Check handoff phrases in agent code match expected patterns
- Review `detectAgentFromMessage()` logic in `agent-chat-transcript.tsx`
- Ensure agent responses include trigger phrases

## Development Tips

- **Debug Mode**: Check browser console for transcript tagging logic
- **Agent Testing**: Test each agent independently before adding handoffs
- **Knowledge Updates**: Modify knowledge bases without changing core agent logic
- **UI Customization**: All visual components are in `components/` and fully editable

## Deployment

### Frontend (Vercel)
```bash
vercel deploy
```

### Backend (LiveKit Cloud Agents)
Follow [LiveKit Agents deployment guide](https://docs.livekit.io/agents/deployment)

## Use Cases

- **Financial Advisory**: Comprehensive wealth planning with specialized real estate advice
- **Customer Support**: Multi-department support with intelligent routing
- **Education**: Subject-matter experts that hand off based on topic
- **Healthcare**: Primary care agents that refer to specialists

## Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents)
- [LiveKit Components React](https://docs.livekit.io/reference/components-react)
- [Groq API Documentation](https://console.groq.com/docs)
- [Deepgram API Documentation](https://developers.deepgram.com)

## License

This project demonstrates multi-agent voice assistant capabilities. Customize freely for your use case.
