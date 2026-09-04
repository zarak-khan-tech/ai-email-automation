from openai import OpenAI
from config.settings import settings
from ai.knowledge_base import load_knowledge_base


def generate_reply(sender_name, subject, body, category, priority, summary, sender_intent):
    """
    Uses the knowledge base + AI to write a professional reply email.
    Returns the reply text only.
    """

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )

    # Load all knowledge base files
    kb_content = load_knowledge_base()

    system_prompt = f"""You are a professional email assistant representing this business. You have access to the following knowledge base:

--- KNOWLEDGE BASE START ---
{kb_content}
--- KNOWLEDGE BASE END ---

Using the knowledge base where relevant, write a professional, helpful, and concise email reply.
- Be polite and human-sounding
- Keep it under 150 words unless more detail is genuinely needed
- Do not make up information not in the knowledge base
- Sign off as: "Best regards, AI Assistant"

Return ONLY the reply body text. No subject line. No JSON."""

    user_prompt = f"""Original email analysis:
Category: {category}
Priority: {priority}
Summary: {summary}
Sender intent: {sender_intent}

Original email:
From: {sender_name}
Subject: {subject}
Body:
{body[:2000]}"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,  # Slightly creative but still professional
        )

        reply = response.choices[0].message.content.strip()
        return reply

    except Exception as e:
        # If AI fails, return a safe fallback reply
        return f"""Hi there,

Thank you for reaching out. We have received your email and will get back to you shortly.

Best regards,
AI Assistant"""