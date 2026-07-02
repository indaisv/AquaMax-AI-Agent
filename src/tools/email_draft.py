"""Professional email drafting tool."""

from __future__ import annotations

from langchain_core.tools import tool

from src.utils.helpers import sanitize_input
from src.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def draft_email(
    recipient_name: str,
    context: str,
    tone: str = "professional",
    include_quote: bool = False,
    quote_id: str | None = None,
) -> str:
    """Draft a professional follow-up email for AquaMax customers.

    Use this tool when the customer requests an email, asks for follow-up, or after capturing a lead or generating a quotation.

    Args:
        recipient_name: Name of the recipient
        context: Context for the email (e.g., "follow-up after TENS inquiry", "quotation for ultrasound unit")
        tone: Email tone: "professional", "friendly", "urgent", or "formal"
        include_quote: Whether to reference a quotation in the email
        quote_id: Quotation ID if referencing a quote
    """
    try:
        recipient_name = sanitize_input(recipient_name) or "Valued Customer"
        context = sanitize_input(context) or "your recent inquiry with AquaMax"
        tone = tone.lower().strip()

        tone_templates = {
            "professional": {
                "greeting": f"Dear {recipient_name},",
                "closing": "Best regards,\nAquaMax Rehab Equipment Sales Team\nPhone: +91-22-XXXX-XXXX | Email: sales@aquamax-rehab.com",
            },
            "friendly": {
                "greeting": f"Hi {recipient_name},",
                "closing": "Warm regards,\nThe AquaMax Team\nWe're here to help you heal better!",
            },
            "formal": {
                "greeting": f"Dear Mr./Ms. {recipient_name},",
                "closing": "Yours sincerely,\nAquaMax Rehab Equipment Pvt. Ltd.\nMumbai, India",
            },
            "urgent": {
                "greeting": f"Dear {recipient_name},",
                "closing": "Please reply at your earliest convenience.\n\nBest regards,\nAquaMax Sales Team",
            },
        }

        template = tone_templates.get(tone, tone_templates["professional"])

        quote_section = ""
        if include_quote and quote_id:
            quote_section = (
                f"\nAs discussed, I have attached quotation #{quote_id} for your review. "
                "Please let us know if you have any questions or would like to proceed.\n"
            )

        body_lines = [
            template["greeting"],
            "",
            f"Thank you for {context}. At AquaMax Rehab Equipment, we are committed to providing the highest quality rehabilitation and physiotherapy equipment to support your recovery and clinical practice.",
            quote_section,
            "I would be happy to arrange a product demonstration, provide additional technical specifications, or discuss customization options to meet your specific requirements.",
            "",
            "Please feel free to reach out if you have any questions or need further assistance. We look forward to serving you.",
            "",
            template["closing"],
        ]

        subject = f"Follow-up: {context[:50]}... — AquaMax Rehab Equipment"

        email = {
            "subject": subject,
            "body": "\n".join(body_lines),
            "tone": tone,
            "recipient": recipient_name,
        }

        return (
            f"**Subject:** {email['subject']}\n\n"
            f"{email['body']}\n\n"
            "---\n"
            "This is a draft email. You can copy and send it, or ask me to adjust the tone or content."
        )

    except Exception as e:
        logger.error("Email drafting failed: %s", e)
        return f"Sorry, the email drafting encountered an error. Please try again. (Error: {type(e).__name__})"
