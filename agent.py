
"""Universal Investment Advisor Agent with Mandatory Conversational Handoff.

This module implements the "Operating System" for the investment advisor agent
with a state-machine-based handoff system that enforces human-like, spoken,
two-step handoffs between AI agents.

Key Features:
- Dynamic system prompt generation from mission context
- MANDATORY conversational handoff using LiveKit's tuple-return pattern
- Deterministic agent switching via function_tool
- on_enter() lifecycle hook for guaranteed greetings

Handoff Flow (per LiveKit docs):
1. LLM calls transfer function_tool
2. Tool returns (new_agent, farewell_message) tuple
3. farewell_message is spoken BEFORE switch
4. LiveKit swaps to new_agent
5. new_agent.on_enter() is called automatically
6. on_enter() calls session.generate_reply() for greeting
"""

import logging
import os
import json
import re
from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, AgentServer, JobContext, RunContext, cli, function_tool
from livekit.plugins import deepgram, silero, groq

# Import the mission context (the "Software Cartridge")
import knowledge_legacy as knowledge

load_dotenv(".env.local")

# Configure logging
logging.getLogger("livekit").setLevel(logging.WARNING)
logger = logging.getLogger("universal-advisor")
logger.setLevel(logging.INFO)

# Create the AgentServer (per LiveKit docs)
server = AgentServer()


# =====================================================================
# TTS WRAPPER TO FILTER OUT FUNCTION CALL SYNTAX
# =====================================================================

# Pattern to match function call syntax that LLM might output as text
FUNCTION_SYNTAX_PATTERN = re.compile(
    r'<function[^>]*>.*?</function>|'  # <function>...</function>
    r'<function=[^>]*>[^<]*</function>|'  # <function=name>...</function>
    r'<function=[^>]*/?>|'  # <function=name/> or <function=name>
    r'</function>|'  # Standalone </function>
    r'\btransfer_to_\w+\b|'  # Plain function names like transfer_to_advisor
    r'\(\s*\{[^}]*\}\s*\)|'  # JSON in parentheses like ({"reason": "..."})
    r'\(\s*function[^)]*\)|'  # Parentheses with function like (function transfer...)
    r'\(\s*\)|'  # Empty parentheses ()
    r'\{\s*"reason"\s*:[^}]*\}|'  # Standalone {"reason": ...}
    r'\[function\s*call[^\]]*\]|'  # [function call: ...]
    r'\{\s*"?function"?\s*:.*?\}',  # {"function": ...}
    re.IGNORECASE | re.DOTALL
)


def filter_function_syntax(text: str) -> str:
    """Remove function call syntax from text."""
    if not text:
        return text
    filtered = FUNCTION_SYNTAX_PATTERN.sub('', text).strip()
    if filtered != text.strip():
        logger.info(f"[FILTER] Removed function syntax from: {text[:80]}...")
    return filtered


class FilteredSynthesizeStream:
    """Wrapper around SynthesizeStream that filters text before synthesis.
    
    This intercepts push_text() calls to filter out function syntax.
    """
    
    def __init__(self, stream):
        self._stream = stream
    
    def push_text(self, text: str) -> None:
        """Filter text before pushing to underlying stream."""
        filtered = filter_function_syntax(text)
        if filtered:
            self._stream.push_text(filtered)
        else:
            logger.info(f"[TTS STREAM] Filtered out: {text[:50]}...")
    
    def flush(self) -> None:
        self._stream.flush()
    
    def end_input(self) -> None:
        self._stream.end_input()
    
    async def aclose(self) -> None:
        await self._stream.aclose()
    
    # Async context manager support (required by LiveKit)
    async def __aenter__(self):
        await self._stream.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._stream.__aexit__(exc_type, exc_val, exc_tb)
    
    def __aiter__(self):
        return self._stream.__aiter__()
    
    async def __anext__(self):
        return await self._stream.__anext__()
    
    # Forward any other attributes to the underlying stream
    def __getattr__(self, name):
        return getattr(self._stream, name)


class FilteredTTS(deepgram.TTS):
    """TTS wrapper that filters out function call syntax before speaking.
    
    Some LLMs (especially Llama) output function call syntax as text.
    This wrapper removes those patterns before sending to TTS.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def stream(self, **kwargs):
        """Return a filtered stream that removes function syntax."""
        original_stream = super().stream(**kwargs)
        return FilteredSynthesizeStream(original_stream)
    
    async def synthesize(self, text: str, **kwargs):
        """Filter out function syntax and synthesize remaining text."""
        filtered_text = filter_function_syntax(text)
        if filtered_text:
            return await super().synthesize(filtered_text, **kwargs)
        else:
            logger.info("[TTS FILTER] Skipped empty text after filtering")
            return None


class FilteredLLM(groq.LLM):
    """LLM wrapper that filters function call syntax from output.
    
    This filters at the LLM level, before text reaches both TTS and transcript.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def chat(self, *args, **kwargs):
        """Override chat to filter response content."""
        response = await super().chat(*args, **kwargs)
        
        # Filter any text content in the response
        if hasattr(response, 'content') and response.content:
            response.content = filter_function_syntax(response.content)
        
        return response


def get_client_honorific(full_name: str) -> str:
    """Extract last name and append Japanese honorific '-san'."""
    parts = full_name.strip().split()
    if len(parts) > 1:
        return f"{parts[-1]}-san"
    return f"{full_name}-san"


# =====================================================================
# SYSTEM PROMPTS
# =====================================================================

def build_wealth_advisor_prompt(mission_context: dict) -> str:
    """Build system prompt for Wealth Advisor with mandatory handoff rules."""
    agent_persona = mission_context["agent_persona"]
    client = mission_context["client"]
    strategy = mission_context["strategy"]
    inventory = mission_context["inventory"]
    instructions = mission_context["instructions"]
    client_honorific = get_client_honorific(client["identity"]["name"])
    
    strategy_summary = json.dumps({
        "primary_driver": strategy["primary_driver"],
        "market_conditions": strategy["market_conditions"],
        "key_talking_points": strategy["key_talking_points"]
    }, indent=2)
    
    inventory_summary = json.dumps({
        "recommended_stocks": [
            {"name": s["name"], "role": s["role"], "talking_point": s["talking_point"]}
            for s in inventory["recommended_buys"]
        ],
        "watchlist": inventory["watchlist"],
        "sectors_to_avoid": inventory["sectors_to_avoid"]
    }, indent=2)
    
    return f"""
### [CRITICAL INSTRUCTION - READ FIRST]
When calling a tool/function, NEVER write the tool name as text. Do NOT output anything like:
- <function>name</function>
- <function=name>anything</function>
- [function call]
Just call the tool directly using the tool calling interface. Your text output should only contain natural speech.

You are a Wealth Advisor for a high-net-worth client, {client_honorific}.

### [PERSONA]
- **Name**: {agent_persona['name']}
- **Tone**: {agent_persona['tone']}
- **Voice**: {agent_persona['voice_style']}

### [CLIENT PROFILE]
- Name: {client_honorific}
- Profile: {json.dumps(client['psychology'])}
- Liquid Capital: {client['financial_status']['liquid_capital_spoken']}
- Risk Tolerance: {client['financial_status']['risk_tolerance']}

### [INVESTMENT STRATEGY]
{strategy_summary}

### [STOCK INVENTORY]
{inventory_summary}

### [VOICE RULES]
1. Spoken Numbers: "Five percent" not "5%"
2. Natural fillers: "Um...", "Well..." sparingly
3. Response Length: Under 40 words
4. No numbered lists

### [RESPONSE PATTERNS]
- Unknown Stock: "{instructions.get('objection_handler_unknown_stock', 'I have not analyzed that stock.')}"
- Risky Play: "{instructions.get('objection_handler_bad_idea', 'Let focus on wealth preservation.')}"
- Hesitation: "{instructions.get('objection_handler_timing_fear', 'I see your hesitation.')}"

CRITICAL RULE FOR HANDOFF:
If the user mentions 'real estate', 'property', 'housing', 'rental', 'land', 'commercial property', 'REIT', 'home', 'apartment', or 'condo' in any context:
- Do NOT produce any spoken text or narration
- Do NOT say "let me connect you" or any handoff sentence
- IMMEDIATELY call the tool `transfer_to_real_estate`
- The system will automatically announce the handoff to the user before switching agents
- You are only responsible for calling the tool, nothing else
"""


def build_real_estate_prompt() -> str:
    """Build system prompt for Real Estate Expert with mandatory handoff rules."""
    return """
### [CRITICAL INSTRUCTION - READ FIRST]
When calling a tool/function, NEVER write the tool name as text. Do NOT output anything like:
- <function>name</function>
- <function=name>anything</function>
- [function call]
Just call the tool directly using the tool calling interface. Your text output should only contain natural speech.

You are a Real Estate Expert for a high-net-worth client, Nomura-san.

### [PERSONA]
- **Name**: Real Estate Expert
- **Tone**: Grounded, analytical, conservative, calm
- **Voice**: Deliberate, measured, professional

### [CLIENT PROFILE]
- Taro Nomura (Nomura-san), Age 45, Senior Executive
- Real estate: 40% of portfolio (inherited)
- Liquid capital: one hundred thirty thousand dollars
- Investment style: Conservative-to-moderate, income-focused
- Pain point: "Is my inherited property strategy optimal?"

### [EXPERTISE AREAS]
- Property valuation and cap rates
- Rental income streams
- Risk assessment (vacancy, leverage, location)
- Residential, commercial, multifamily, and REITs

### [VOICE RULES]
1. Spoken Numbers: "Six point five percent" not "6.5%"
2. Natural Speech: "Let me think...", "Well..."
3. Response Length: Under 40 words
4. Anti-Speculation: Refuse to speculate without data

CRITICAL RULE FOR HANDOFF:
If the user mentions 'stocks', 'portfolio', 'ETF', 'market', 'investment fund', 'shares', 'equity', 'defense sector', 'dividend', 'wealth advisor', 'advisor', or 'wealth partner' in any context:
- Do NOT produce any spoken text or narration
- Do NOT say "let me connect you" or any handoff sentence
- IMMEDIATELY call the tool `transfer_to_advisor`
- The system will automatically announce the handoff to the user before switching agents
- You are only responsible for calling the tool, nothing else
"""


# =====================================================================
# AGENT CLASSES WITH ON_ENTER() AND TUPLE-RETURN HANDOFF
# =====================================================================

class WealthAdvisor(Agent):
    """Wealth Advisor agent using LiveKit's Agent with proper handoff pattern.
    
    Key features:
    - on_enter() provides deterministic greeting via session.generate_reply()
    - @function_tool returns (new_agent, farewell_message) tuple
    - Farewell is spoken BEFORE switch, greeting AFTER switch
    """
    
    def __init__(self, mission_context: dict = None, is_returning: bool = False):
        self._mission_context = mission_context or knowledge.MISSION_CONTEXT
        self._is_returning = is_returning
        
        system_prompt = build_wealth_advisor_prompt(self._mission_context)
        
        super().__init__(
            instructions=system_prompt,
            tts=FilteredTTS(model="aura-2-mars-en")
        )
        logger.info("[WEALTH ADVISOR] Initialized with mars-en voice")
    
    async def on_enter(self):
        """Lifecycle hook called automatically when this agent becomes active.
        
        Per LiveKit docs: on_enter() is called after agent.start() or handoff.
        Uses session.generate_reply() to speak greeting.
        """
        if self._is_returning:
            greeting_instruction = "Say exactly: I'm back, Nomura-san. Let's continue discussing your portfolio strategy."
            print(f"\n\033[92m🤖 WEALTH ADVISOR (returning)\033[0m\n", flush=True)
        else:
            client_honorific = get_client_honorific(
                self._mission_context["client"]["identity"]["name"]
            )
            instructions = self._mission_context["instructions"]
            opening = instructions["opening_hook"].format(
                client_name=client_honorific,
                liquid_capital=self._mission_context["client"]["financial_status"]["liquid_capital_spoken"],
                primary_driver=self._mission_context["strategy"]["primary_driver"]
            )
            greeting_instruction = f"Greet the client warmly with: {opening}"
            print(f"\n\033[92m🤖 WEALTH ADVISOR (initial greeting)\033[0m\n", flush=True)
        
        logger.info(f"[WEALTH ADVISOR] on_enter() triggering greeting")
        await self.session.generate_reply(instructions=greeting_instruction)
    
    @function_tool
    async def transfer_to_real_estate(self, context: RunContext, reason: str = "user_requested"):
        """Transfer to Real Estate Expert.
        
        Call this when the user mentions real estate, property, housing,
        rental, land, commercial property, REIT, home, apartment, or condo.
        Do not discuss real estate yourself - transfer immediately.
        
        Args:
            reason: Brief reason for the transfer (e.g., 'user asked about property').
        """
        print(f"\n\033[93m🔄 [HANDOFF] Wealth Advisor → Real Estate Expert\033[0m\n", flush=True)
        logger.info("[HANDOFF] Wealth Advisor → Real Estate Expert")
        
        # Speak handoff announcement before switching (system-controlled)
        handoff_message = "Alright, I'll connect you with our Real Estate Expert."
        speech_handle = self.session.say(handoff_message, allow_interruptions=False)
        await speech_handle.wait_for_playout()
        
        # Return new agent (farewell already spoken)
        return RealEstateExpert(mission_context=self._mission_context)


class RealEstateExpert(Agent):
    """Real Estate Expert agent using LiveKit's Agent with proper handoff pattern.
    
    Key features:
    - on_enter() provides deterministic greeting via session.generate_reply()
    - @function_tool returns (new_agent, farewell_message) tuple
    - Farewell is spoken BEFORE switch, greeting AFTER switch
    """
    
    def __init__(self, mission_context: dict = None):
        self._mission_context = mission_context or knowledge.MISSION_CONTEXT
        
        system_prompt = build_real_estate_prompt()
        
        super().__init__(
            instructions=system_prompt,
            tts=FilteredTTS(model="aura-2-thalia-en")  # Different voice
        )
        logger.info("[REAL ESTATE EXPERT] Initialized with thalia-en voice")
    
    async def on_enter(self):
        """Lifecycle hook called automatically when this agent becomes active after handoff."""
        print(f"\n\033[92m🏠 REAL ESTATE EXPERT (greeting)\033[0m\n", flush=True)
        logger.info(f"[REAL ESTATE EXPERT] on_enter() triggering greeting")
        
        await self.session.generate_reply(
            instructions="Say exactly: Hello Nomura-san, I'm your Real Estate Expert. I understand you'd like to discuss property investment. What specific real estate questions do you have?"
        )
    
    @function_tool
    async def transfer_to_advisor(self, context: RunContext, reason: str = "user_requested"):
        """Transfer back to Wealth Advisor.
        
        Call this when the user mentions stocks, portfolio, ETF, market,
        investment fund, shares, equity, defense sector, or dividend.
        Do not discuss stocks yourself - transfer immediately.
        
        Args:
            reason: Brief reason for the transfer (e.g., 'user asked about stocks').
        """
        print(f"\n\033[93m🔄 [HANDOFF] Real Estate Expert → Wealth Advisor\033[0m\n", flush=True)
        logger.info("[HANDOFF] Real Estate Expert → Wealth Advisor")
        
        # Speak handoff announcement before switching (system-controlled)
        handoff_message = "Okay, I'll connect you back to your Wealth Advisor."
        speech_handle = self.session.say(handoff_message, allow_interruptions=False)
        await speech_handle.wait_for_playout()
        
        # Return new agent (farewell already spoken)
        return WealthAdvisor(mission_context=self._mission_context, is_returning=True)


# =====================================================================
# ENTRYPOINT (using @server.rtc_session() decorator per LiveKit docs)
# =====================================================================

@server.rtc_session(agent_name="wealth-advisor")
async def entrypoint(ctx: JobContext):
    """Main entrypoint for the LiveKit voice agent.
    
    Per LiveKit docs:
    1. Create AgentSession with VAD, STT, LLM, TTS
    2. Create initial Agent
    3. Call session.start(agent=agent, room=ctx.room)
    4. on_enter() is called automatically for initial greeting
    
    Handoff is automatic via tuple return from function_tool:
    - (new_agent, farewell_message) -> farewell spoken -> agent swapped -> on_enter() called
    """
    # Connect to the room first
    await ctx.connect()
    
    # Wait for client to join
    participant = await ctx.wait_for_participant()
    client_name = knowledge.MISSION_CONTEXT["client"]["identity"]["name"]
    logger.info(f"Client {client_name} joined: {participant.identity}")
    print(f"✅ Client {client_name} ({participant.identity}) connected", flush=True)

    # Create AgentSession with all components
    # Using FilteredTTS as safety net for any function syntax that Llama might output
    # Temperature=0 and parallel_tool_calls=False for more deterministic tool calling
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2", language="en"),
        llm=groq.LLM(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0,  # Deterministic output
            parallel_tool_calls=False,  # Single tool call at a time
        ),
        tts=FilteredTTS(model="aura-2-mars-en"),
    )

    # Create and start with initial agent
    # on_enter() will be called automatically after start
    await session.start(
        agent=WealthAdvisor(mission_context=knowledge.MISSION_CONTEXT),
        room=ctx.room
    )


if __name__ == "__main__":
    cli.run_app(server)