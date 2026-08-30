HIGH_INTENT_TERMS = ("demo", "contact", "consultation", "proposal", "pilot", "evaluate")


def score_lead(lead):
    score = 10  # valid email is required
    score += 10 if lead.get("company") else 0
    score += 10 if lead.get("industry") else 0
    score += 15 if lead.get("interested_product") not in (None, "general") else 0
    score += 15 if len(lead.get("message", "")) >= 80 else 0
    score += 10 if lead.get("phone") else 0
    message = lead.get("message", "").lower()
    score += 20 if any(term in message for term in HIGH_INTENT_TERMS) else 0
    return score, "high" if score >= 50 else "medium" if score >= 25 else "low"
