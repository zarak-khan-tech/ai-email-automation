import json
from openai import OpenAI
from config.settings import settings


def classify_email(sender_name, sender_email, subject, body):
    """
    Sends email to AI and gets back:
    - category (support, sales, spam, etc.)
    - priority (low, medium, high, urgent)
    - summary
    - extracted_info (intent, key facts, etc.)
    """
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )

    system_prompt = """You are an intelligent email assistant. When given an email, return a JSON object with exactly these fields:

{
  "category": one of ["support", "sales_inquiry", "spam", "complaint", "general_inquiry", "job_application", "invoice", "partnership", "urgent_action", "other"],
  "priority": one of ["low", "medium", "high", "urgent"],
  "summary": "one sentence summary",
  "extracted_info": {
    "sender_intent": "what does the sender want?",
    "key_facts": ["fact1", "fact2"],
    "action_required": true or false,
    "deadline_mentioned": "date if any, else null",
    "sentiment": one of ["positive", "neutral", "negative", "frustrated"]
  }
}

Return ONLY valid JSON. No explanation. No markdown."""

    user_prompt = f"""From: {sender_name} <{sender_email}>
Subject: {subject}
Body:
{body[:3000]}"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # Low = more predictable, accurate
        )

        # Get the AI's reply text
        ai_text = response.choices[0].message.content.strip()

        # Sometimes AI wraps JSON in ```json ... ``` — remove that
        if ai_text.startswith("```"):
            ai_text = ai_text.replace("```json", "").replace("```", "").strip()

        # Parse JSON
        result = json.loads(ai_text)
        return result

    except json.JSONDecodeError:
        # AI didn't return valid JSON
        return {
            "category": "other",
            "priority": "medium",
            "summary": "AI failed to parse this email",
            "extracted_info": {
                "sender_intent": "unknown",
                "key_facts": [],
                "action_required": False,
                "deadline_mentioned": None,
                "sentiment": "neutral"
            }
        }

    except Exception as e:
        # API failed or other error
        return {
            "category": "other",
            "priority": "medium",
            "summary": f"Error: {str(e)}",
            "extracted_info": {
                "sender_intent": "unknown",
                "key_facts": [],
                "action_required": False,
                "deadline_mentioned": None,
                "sentiment": "neutral"
            }
        }