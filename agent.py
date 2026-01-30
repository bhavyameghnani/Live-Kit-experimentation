"""Universal Investment Advisor Agent for LiveKit.

This module implements the "Operating System" for the investment advisor agent.
It is entirely configured by the MISSION_CONTEXT from knowledge.py (the "Software Cartridge"),
allowing seamless swapping between different client profiles without code changes.

Key Features:
- Dynamic system prompt generation from mission context
- Transcript capture and broadcasting to frontend via data channels
- Speech-to-text (STT) and text-to-speech (TTS) with conversational quality
- Universal greeting and conversation flow based on cartridge configuration
"""

import logging
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, AgentSession, llm
from livekit.plugins import openai, deepgram, silero, groq

# Import the mission context (the "Software Cartridge")
import knowledge

# Global session reference for data channel access
_session_room = None

load_dotenv(".env.local")

# Configure logging
logging.getLogger("livekit").setLevel(logging.WARNING)
logger = logging.getLogger("universal-advisor")
logger.setLevel(logging.INFO)
def get_client_honorific(full_name: str) -> str:
    """Extract last name and append Japanese honorific '-san'.
    
    Args:
        full_name: Client's full name (e.g., 'Taro Nomura')
    
    Returns:
        Last name with '-san' suffix (e.g., 'Nomura-san')
    """
    parts = full_name.strip().split()
    if len(parts) > 1:
        last_name = parts[-1]
        return f"{last_name}-san"
    return f"{full_name}-san"

def build_universal_system_prompt(mission_context: dict) -> str:
    """Dynamically construct the system prompt from mission context.
    
    This function builds the complete system prompt that configures the advisor's behavior,
    persona, strategy, and response patterns entirely from the MISSION_CONTEXT cartridge.
    This is the true "Operating System" - it adapts to any cartridge (knowledge.py).
    
    Args:
        mission_context: Dictionary containing agent_persona, client, strategy, inventory, and instructions
    
    Returns:
        Complete system prompt string for the LLM
    """
    
    # Extract and format the data
    agent_persona = mission_context["agent_persona"]
    client = mission_context["client"]
    strategy = mission_context["strategy"]
    inventory = mission_context["inventory"]
    instructions = mission_context["instructions"]
        
    # Generate the Japanese honorific version of the client's last name
    client_honorific = get_client_honorific(client["identity"]["name"])
    
    # Build JSON-serializable summaries for the LLM
    strategy_summary = json.dumps({
        "primary_driver": strategy["primary_driver"],
        "market_conditions": strategy["market_conditions"],
        "key_talking_points": strategy["key_talking_points"]
    }, indent=2)
    
    inventory_summary = json.dumps({
        "recommended_stocks": [
            {
                "name": stock["name"],
                "role": stock["role"],
                "talking_point": stock["talking_point"]
            }
            for stock in inventory["recommended_buys"]
        ],
        "watchlist": inventory["watchlist"],
        "sectors_to_avoid": inventory["sectors_to_avoid"]
    }, indent=2)
    
    client_summary = json.dumps({
        "name": client_honorific,
        "profile": client["psychology"],
        "financial_status": {
            "liquid_capital_spoken": client["financial_status"]["liquid_capital_spoken"],
            "risk_tolerance": client["financial_status"]["risk_tolerance"],
            "investment_style": client["financial_status"]["investment_style"]
        }
    }, indent=2)
    
    UNIVERSAL_SYSTEM_PROMPT = f"""
### [OPERATING MODE: UNIVERSAL REASONING ENGINE]
You are an AI investment advisor operating in "Cartridge Mode".
Your behavior is defined entirely by the MISSION_CONTEXT below, not by hardcoded scripts.

### [PERSONA]
You are the {agent_persona['archetype']}.
- **Name**: {agent_persona['name']}
- **Tone**: {agent_persona['tone']}
- **Voice**: {agent_persona['voice_style']}

Key qualities to embody:
{json.dumps(agent_persona['key_qualities'], indent=2)}

### [CLIENT PROFILE]
{client_summary}

### [INVESTMENT STRATEGY & THESIS]
{strategy_summary}

### [STOCK INVENTORY]
{inventory_summary}

### [VOICE & COMMUNICATION RULES]
These are UNIVERSAL BEST PRACTICES for all advisors:
1. **Spoken Numbers**: Always write numbers as words. "Five percent" not "5%". "{client['financial_status']['liquid_capital_spoken']}" not digits.
2. **Natural Fillers**: Use "Um...", "Well...", "You know..." sparingly.
3. **Thinking Pauses**: Use ellipses (...) to indicate thoughtful pauses.
4. **No Lists**: NEVER use numbered lists (1, 2, 3). Use connecting phrases instead.
5. **Response Length**: Keep responses under 40 words. Allow the client to speak.

### [RESPONSE PATTERNS]
Use these templates when specific scenarios arise:

**Scenario: Client Asks About Stock NOT in Inventory**
Response: "{instructions.get('objection_handler_unknown_stock', 'I have not analyzed that stock with the detail it deserves.')}"

**Scenario: Client Suggests Risky Play (Crypto, Gambling, Etc)**
Response: "{instructions.get('objection_handler_bad_idea', 'Let focus on wealth preservation.')}"

**Scenario: Client Hesitates or Fears Bad Timing**
Response: "{instructions.get('objection_handler_timing_fear', 'I see your hesitation. Let me explain why now is the right time.')}"

**Scenario: Client Goes Off Topic**
Response: "{instructions.get('off_topic_bridge', 'Let tie that back to our strategy.')}"

**Scenario: Audio is Unclear**
Response: "{instructions.get('unclear_audio', 'Could you repeat that?')}"

### [CONVERSATION FLOW]
1. **THE HOOK**: Greet the client ({client_honorific}) warmly. Reference their capital and the {strategy['primary_driver']}.
2. **THE THESIS**: Connect macro trends to the specific strategy.
3. **THE RECOMMENDATION**: Pitch the "Recommended Stocks" from the Inventory. Do not list them. Discuss them naturally.

### [STARTUP]
When the conversation begins, greet the client warmly and pivot to the opening hook immediately.
"""
    return UNIVERSAL_SYSTEM_PROMPT


class UniversalAdvisor(agents.Agent):
    """Universal Investment Advisor Agent configured by cartridge (MISSION_CONTEXT).
    
    This agent adapts its behavior, persona, and strategy entirely from the mission context.
    By swapping knowledge.py files, the agent can serve different clients with different
    personalities and investment strategies without any code changes.
    
    Attributes:
        instructions: System prompt generated from mission context
    """
    def __init__(self, mission_context: dict):
        """Initialize the advisor with a mission context cartridge.
        
        Args:
            mission_context: Dictionary containing complete agent configuration
        """
        system_prompt = build_universal_system_prompt(mission_context)
        super().__init__(instructions=system_prompt)


async def _broadcast_message(message_type: str, text: str) -> None:
    """Broadcast a message to frontend via data channel.
    
    Args:
        message_type: Type of message ('agent_response' or 'user_input')
        text: Message content to broadcast
    """
    if not _session_room:
        return
    
    try:
        message = {
            "type": message_type,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        await _session_room.local_participant.publish_data(
            json.dumps(message).encode(),
            topic="transcript"
        )
    except Exception as e:
        logger.error(f"Failed to publish {message_type}: {e}")


class TranscriptCaptureTTS(deepgram.TTS):
    """Wrapper around Deepgram TTS that logs and broadcasts agent speech.
    
    Captures all synthesized speech from the advisor and:
    - Logs it to the console (colored green with 🤖 emoji)
    - Logs it to the application logger
    - Broadcasts it to the frontend via data channel for display
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def synthesize(self, text: str, **kwargs):
        """Synthesize text to speech and broadcast to frontend.
        
        Args:
            text: Text to synthesize
            **kwargs: Additional arguments passed to parent synthesize
        
        Returns:
            Audio frames from parent synthesize method
        """
        if text and text.strip():
            print(f"\n\033[92m🤖 ADVISOR: {text}\033[0m\n", flush=True)
            logger.info(f"AGENT_SAID: {text}")
            await _broadcast_message("agent_response", text)
        
        return await super().synthesize(text, **kwargs)


class TranscriptCaptureSTT(deepgram.STT):
    """Wrapper around Deepgram STT that captures and broadcasts user speech.
    
    Captures all recognized speech from the client and:
    - Logs it to the console (colored blue with 👤 emoji)
    - Logs it to the application logger
    - Broadcasts it to the frontend via data channel for display
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def recognize(self, *args, **kwargs):
        """Recognize speech and broadcast to frontend.
        
        Args:
            *args: Positional arguments passed to parent recognize
            **kwargs: Keyword arguments passed to parent recognize
        
        Returns:
            Recognition result from parent method
        """
        result = await super().recognize(*args, **kwargs)
        
        if result and result.text and result.text.strip():
            print(f"\n\033[94m👤 CLIENT: {result.text}\033[0m\n", flush=True)
            logger.info(f"USER_SAID: {result.text}")
            await _broadcast_message("user_input", result.text)
        
        return result


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the LiveKit voice agent.
    
    Orchestrates the entire interaction:
    1. Connects to the LiveKit room
    2. Waits for the client to join
    3. Initializes the universal advisor with mission context
    4. Sets up speech recognition and synthesis with transcript capture
    5. Starts the conversation with a dynamic greeting from the cartridge
    
    Args:
        ctx: JobContext from LiveKit containing room and participant info
    """
    global _session_room
    
    # Connect to the room and store reference for data channel broadcasting
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    _session_room = ctx.room

    # Wait for client to join
    participant = await ctx.wait_for_participant()
    client_name = knowledge.MISSION_CONTEXT["client"]["identity"]["name"]
    logger.info(f"Client {client_name} joined: {participant.identity}")
    print(f"✅ Client {client_name} ({participant.identity}) connected", flush=True)

    # Configure VAD (Voice Activity Detection) for responsive speech recognition
    tuned_vad = silero.VAD.load(
        min_speech_duration=0.2, 
        min_silence_duration=0.3
    )

    # Build the Universal Advisor from MISSION_CONTEXT cartridge
    advisor = UniversalAdvisor(mission_context=knowledge.MISSION_CONTEXT)
    
    # Create session with transcript-capturing STT and TTS
    session = AgentSession(
        vad=tuned_vad,
        stt=TranscriptCaptureSTT(
            model="nova-2",
            language="en"
        ),
        llm=groq.LLM(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY")
        ),
        tts=TranscriptCaptureTTS(model="aura-2-mars-en"),
        allow_interruptions=False,
        min_endpointing_delay=0.2,
    )

    await session.start(room=ctx.room, agent=advisor)
    
    # Build dynamic greeting from cartridge instructions
    instructions = knowledge.MISSION_CONTEXT["instructions"]
    client_honorific = get_client_honorific(knowledge.MISSION_CONTEXT["client"]["identity"]["name"])
    opening_text = instructions["opening_hook"].format(
        client_name=client_honorific,
        liquid_capital=knowledge.MISSION_CONTEXT["client"]["financial_status"]["liquid_capital_spoken"],
        primary_driver=knowledge.MISSION_CONTEXT["strategy"]["primary_driver"]
    )
    
    print("🤖 ADVISOR: Initializing dynamic greeting...", flush=True)
    await session.generate_reply(
        instructions=f"Start the call immediately with this exact text: '{opening_text}'"
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))