"""
AI Helpers — Google Gemini (FREE tier) integration.
"""
import re
from flask import current_app

_model = None


def _get_model():
    """Lazy-load Gemini model."""
    global _model
    if _model is not None:
        return _model
    try:
        import google.generativeai as genai
        api_key = current_app.config.get("GEMINI_API_KEY", "")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-1.5-flash")
        return _model
    except Exception as e:
        print(f"[AI] Failed to init Gemini: {e}")
        return None


def sanitize_prompt(text: str) -> str:
    """Basic prompt injection protection."""
    # Remove common injection patterns
    dangerous = [
        r"ignore\s+(previous|above|all)\s+(instructions|prompts)",
        r"you\s+are\s+now",
        r"system\s*:\s*",
        r"<\|.*?\|>",
        r"\[INST\]",
        r"\[/INST\]",
    ]
    cleaned = text
    for pattern in dangerous:
        cleaned = re.sub(pattern, "[filtered]", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def chat_with_ai(messages: list, system_prompt: str = None) -> str:
    """
    Chat with Gemini.
    messages: list of {"role": "user"|"assistant", "content": "..."}
    """
    model = _get_model()
    if not model:
        return "AI is not configured. Please set GEMINI_API_KEY in your environment."

    try:
        # Build conversation for Gemini
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(f"System instructions: {system_prompt}\n\n")

        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt_parts.append(f"{role}: {sanitize_prompt(msg['content'])}\n")

        prompt_parts.append("Assistant: ")
        full_prompt = "".join(prompt_parts)

        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[AI] Chat error: {e}")
        return f"AI error: {str(e)}"


def generate_notes(topic: str) -> str:
    """Generate structured notes on a topic."""
    prompt = f"""Create comprehensive, well-structured study notes on the topic: "{topic}"

Include:
- Key concepts and definitions
- Important points organized with headers
- Examples where helpful
- Summary at the end

Format using Markdown."""

    return chat_with_ai([{"role": "user", "content": prompt}],
                        system_prompt="You are a helpful study assistant that creates clear, organized notes.")


def refine_content(content: str, mode: str) -> str:
    """Refine content: summary, qa, or mindmap."""
    prompts = {
        "summary": f"Summarize the following content concisely:\n\n{content}",
        "qa": f"Generate 10 study questions and answers from this content:\n\n{content}",
        "mindmap": f"Create a Mermaid mindmap diagram from this content. Use 'mindmap' syntax. Keep it clean and organized:\n\n{content}",
    }

    prompt = prompts.get(mode, prompts["summary"])
    return chat_with_ai([{"role": "user", "content": prompt}],
                        system_prompt="You are a study assistant. Be concise and well-structured.")


def analyze_resume(text: str) -> dict:
    """Analyze resume text and return structured feedback."""
    prompt = f"""Analyze this resume and provide feedback in the following JSON format:
{{
    "strengths": ["list of strengths"],
    "missing_skills": ["skills that could be added"],
    "improvements": ["specific improvement suggestions"],
    "ats_suggestions": ["ATS optimization tips"],
    "overall_score": 75,
    "summary": "brief overall assessment"
}}

Resume text:
{text}

Return ONLY valid JSON, no markdown code blocks."""

    result = chat_with_ai([{"role": "user", "content": prompt}],
                          system_prompt="You are an expert resume reviewer. Return only valid JSON.")

    # Try to parse JSON from response
    import json
    try:
        # Strip markdown code blocks if present
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "strengths": [],
            "missing_skills": [],
            "improvements": [],
            "ats_suggestions": [],
            "overall_score": 0,
            "summary": result,
        }


def generate_mindmap_from_transcript(transcript: str) -> str:
    """Generate Mermaid mindmap code from a YouTube transcript."""
    prompt = f"""From this YouTube video transcript, create a Mermaid mindmap diagram.

Rules:
- Use the Mermaid 'mindmap' syntax
- Start with 'mindmap' on the first line
- Use proper indentation for hierarchy
- Keep nodes concise (max 5 words per node)
- Include 3-5 main branches with 2-4 sub-items each
- Make it informative and well-organized

Transcript:
{transcript[:3000]}

Return ONLY the Mermaid mindmap code, nothing else."""

    return chat_with_ai([{"role": "user", "content": prompt}],
                        system_prompt="You generate clean Mermaid mindmap diagrams. Return only the mermaid code.")
