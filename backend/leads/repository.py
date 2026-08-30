import logging
from datetime import datetime, timezone

from django.conf import settings
from django.core.mail import send_mail

from database.mongo import get_database
from .scoring import score_lead

logger = logging.getLogger(__name__)

class LeadRepository:
    collection_name = "leads"

    def create(self, lead, source="website", chatbot_generated=False):
        score, quality = score_lead(lead)
        now = datetime.now(timezone.utc)
        document = {**lead, "lead_source": source, "chatbot_generated": chatbot_generated, "status": "new", "lead_score": score, "lead_quality": quality, "created_at": now, "updated_at": now}
        result = get_database()[self.collection_name].insert_one(document)
        
        # Send an email notification via Brevo
        try:
            name = lead.get("name", "Unknown")
            email = lead.get("email", "Not provided")
            phone = lead.get("phone", "Not provided")
            company = lead.get("company", "Not provided")
            message = lead.get("message", "No message")
            
            subject = f"New Lead Captured: {name}"
            body = (
                f"A new lead was captured on the website.\n\n"
                f"Name: {name}\n"
                f"Email: {email}\n"
                f"Phone: {phone}\n"
                f"Company: {company}\n\n"
                f"Message:\n{message}\n\n"
                f"Source: {source}\n"
                f"Chatbot Generated: {chatbot_generated}\n"
                f"Lead Score: {score}/100 ({quality})"
            )
            
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            logger.info("Lead notification email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send lead notification email: {e}")

        return str(result.inserted_id), score, quality
