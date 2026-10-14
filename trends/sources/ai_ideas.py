"""Level 1 AI idea generator — kept as the first worker, now clearly labelled ai_generated."""
import json
import logging
from trends.schema import make_item, utcnow

log = logging.getLogger(__name__)
MODEL = "openai/gpt-oss-120b"
MAX_RETRIES = 3

PROMPT = """
Generate Instagram content ideas for a Gen-Z audience in India.

Return exactly valid JSON with these keys:
{
  "audios": [{"name": "audio name or search phrase", "vibe": "baddie, soft, funny, or cinematic", "use_case": "short suggested use-case"}],
  "captions": ["short Instagram caption"]
}

Requirements:
- Exactly 5 audio suggestions.
- Exactly 5 captions.
- Male and female aesthetic styles.
- Confident, stylish, Gen-Z-friendly ideas.
- Keep audio names or search phrases concise.
- Do not invent popularity statistics or claim an audio is verified
  as trending without evidence.
- These are suggestions, not verified live Instagram trends.
- Return JSON only.
"""


def generate(groq_client):
    """Return validated (audios, captions) from Groq. Retries on bad output."""
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = groq_client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": "Return only valid JSON. Do not use Markdown."},
                          {"role": "user", "content": PROMPT}],
                temperature=0.7, response_format={"type": "json_object"})
            raw = resp.choices[0].message.content
            if not raw:
                raise ValueError("empty response")
            data = json.loads(raw)
            audios, captions = data.get("audios"), data.get("captions")
            if not isinstance(audios, list) or len(audios) != 5:
                raise ValueError("expected exactly 5 audio suggestions")
            if not isinstance(captions, list) or len(captions) != 5:
                raise ValueError("expected exactly 5 captions")
            return audios, captions
        except Exception as exc:
            last = exc
            log.warning("AI attempt %s/%s failed: %s", attempt, MAX_RETRIES, exc)
    raise RuntimeError(f"AI idea generation failed: {last}")


def to_items(audios, captions):
    now, items = utcnow(), []
    for a in audios:
        if isinstance(a, str):
            a = {"name": a}
        if not isinstance(a, dict):
            continue
        try:
            items.append(make_item(
                kind="audio", title=str(a.get("name", "")), source_type="ai_generated",
                source_name="level1_brain", ttl_hours=48, confidence=0.3, observed_at=now,
                vibe=str(a.get("vibe", "")) or None, use_case=str(a.get("use_case", "")) or None,
                rights_note="AI suggestion; not verified as trending or licensed"))
        except ValueError:
            pass
    for c in captions:
        if isinstance(c, str):
            try:
                items.append(make_item(
                    kind="caption_idea", title=c, source_type="ai_generated",
                    source_name="level1_brain", ttl_hours=48, confidence=0.3, observed_at=now))
            except ValueError:
                pass
    return items
