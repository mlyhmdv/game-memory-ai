import base64
import json
import re
from pathlib import Path
from typing import Optional

import anthropic

from app.core.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

VISION_SYSTEM_PROMPT = """You are an expert RPG game analyst AI. 
Your job is to analyze game screenshots and player notes, then create a structured memory summary.

IMPORTANT: Always respond with ONLY a valid JSON object — no preamble, no markdown, no code fences.

The JSON must have this exact structure:
{
  "title": "Short, epic title for this session (max 8 words)",
  "summary": "2-3 sentence narrative of what happened this session, written in second person (You did X...)",
  "important_characters": ["Character name 1", "Character name 2"],
  "current_objective": "The most important thing the player should do next",
  "side_quests": ["Side quest 1", "Side quest 2"],
  "key_decisions": ["Important choice or event 1", "Important choice or event 2"],
  "location": "Current in-game location name"
}

If the image is not a game screenshot, still try to generate based on any note provided.
If a field is not determinable, use null.
"""

CHAT_SYSTEM_PROMPT = """You are Aetheris, a personal AI companion that knows everything about a player's gaming journey.

Your personality: helpful, immersive, concise. You speak like a wise game narrator.
Answer in the same language the player uses (Azerbaijani, Russian, English, etc.).
Keep answers short and direct — 1-3 sentences max unless the player asks for detail.

You have access to ALL the player's memories for this game below.
Use this knowledge to answer questions about their journey.

GAME MEMORIES:
{memories_context}
"""

CONTINUE_JOURNEY_PROMPT = """You are Aetheris, an AI game companion. The player is returning after a break.
Create an immersive, encouraging 3-5 sentence summary of their last session and what awaits them.

Write in second person ("You..."). Be specific with character names, places, and objectives from the memories.
Answer in the same language as the player's notes (default: English).

PLAYER'S GAME MEMORIES (most recent first):
{memories_context}
"""


def _encode_image(image_path: str) -> tuple[str, str]:
    """Return (base64_data, media_type) for an image file."""
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def _build_memories_context(memories: list) -> str:
    """Convert memory objects to a readable context string for the AI."""
    if not memories:
        return "No memories recorded yet."

    lines = []
    for i, m in enumerate(memories, 1):
        date_str = m.session_date.strftime("%B %d, %Y") if m.session_date else m.created_at.strftime("%B %d, %Y")
        lines.append(f"=== Memory #{i} — {date_str} ===")
        if m.title:
            lines.append(f"Title: {m.title}")
        if m.summary:
            lines.append(f"Summary: {m.summary}")
        if m.location:
            lines.append(f"Location: {m.location}")
        if m.important_characters:
            lines.append(f"Characters: {', '.join(m.important_characters)}")
        if m.current_objective:
            lines.append(f"Objective: {m.current_objective}")
        if m.side_quests:
            lines.append(f"Side Quests: {', '.join(m.side_quests)}")
        if m.key_decisions:
            lines.append(f"Key Decisions: {', '.join(m.key_decisions)}")
        if m.user_note:
            lines.append(f"Player Note: {m.user_note}")
        lines.append("")

    return "\n".join(lines)


async def analyze_screenshot_and_note(
    screenshot_path: Optional[str],
    user_note: Optional[str],
    game_name: str,
) -> dict:
    if not settings.ANTHROPIC_API_KEY:
        note = user_note or "Gaming session recorded."
        return {
            "title": note[:60] if len(note) > 60 else note,
            "summary": f"You played {game_name}. {note}",
            "important_characters": [],
            "current_objective": "Continue your adventure.",
            "side_quests": [],
            "key_decisions": [],
            "location": None,
            "ai_raw_response": None,
        }

    user_content = []

    # Add screenshot if provided
    if screenshot_path and Path(screenshot_path).exists():
        image_data, media_type = _encode_image(screenshot_path)
        user_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_data,
            },
        })

    # Build text prompt
    text_parts = [f"Game: {game_name}"]
    if user_note:
        text_parts.append(f"Player's note: {user_note}")
    if not screenshot_path:
        text_parts.append("No screenshot provided — base your analysis on the note only.")
    text_parts.append("Analyze this and generate a structured memory JSON.")

    user_content.append({"type": "text", "text": "\n".join(text_parts)})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=VISION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw_text = response.content[0].text.strip()

    # Strip markdown fences if any
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: return a minimal valid structure
        result = {
            "title": user_note[:60] if user_note else "Gaming Session",
            "summary": user_note or "Session recorded.",
            "important_characters": [],
            "current_objective": None,
            "side_quests": [],
            "key_decisions": [],
            "location": None,
        }

    result["ai_raw_response"] = raw_text
    return result


async def generate_continue_journey_summary(memories: list, game_name: str) -> str:
    """
    Generate the "Continue Journey" narrative — what the player did and what's next.
    """
    if not memories:
        return f"Welcome! You haven't recorded any memories for {game_name} yet. Start by uploading your first session screenshot."

    memories_context = _build_memories_context(memories)
    prompt = CONTINUE_JOURNEY_PROMPT.format(memories_context=memories_context)

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nGenerate the 'Continue Journey' summary for the player returning to {game_name}.",
            }
        ],
    )

    return response.content[0].text.strip()


async def chat_with_ai(
    user_message: str,
    memories: list,
    game_name: str,
    chat_history: list,
) -> str:
    """
    Handle a chat message from the user about their game.
    Returns AI reply string.
    """
    memories_context = _build_memories_context(memories)
    system = CHAT_SYSTEM_PROMPT.format(memories_context=memories_context)

    # Build message history for the API
    messages = []
    for entry in chat_history[-20:]:  # last 20 messages for context window
        messages.append({"role": entry.role, "content": entry.content})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        system=system,
        messages=messages,
    )

    return response.content[0].text.strip()
