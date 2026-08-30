from chatbot.qualification import analyze_message, apply_conversation_lead_capture


def test_analyze_message_detects_interest_and_sentiment():
    product, intent, sentiment = analyze_message("I’m interested in a demo for document intelligence")
    assert product == "document_intelligence"
    assert intent > 0
    assert sentiment == "positive"


def test_chatbot_captures_lead_in_steps():
    session = {}

    state, reply = apply_conversation_lead_capture(session, "I’m interested in a demo for document intelligence")
    assert state["active"] is True
    assert state["current_field"] == "context"
    assert "problem" in reply.lower() or "workflow" in reply.lower()

    state, reply = apply_conversation_lead_capture(state, "We have a lot of handwritten forms that need digitization")
    assert state["data"]["requirement"]
    assert state["current_field"] == "name_company"
    assert "name" in reply.lower() and "company" in reply.lower()

    state, reply = apply_conversation_lead_capture(state, "I’m Alex Morgan from BluePeak Labs")
    assert state["data"]["name"] == "Alex Morgan"
    assert state["data"]["company"] == "BluePeak Labs"
    assert state["current_field"] == "email"
    assert "email" in reply.lower()

    state, reply = apply_conversation_lead_capture(state, "alex.morgan@bluepeaklabs.com")
    assert state["data"]["email"] == "alex.morgan@bluepeaklabs.com"
    assert state["current_field"] == "phone"
    assert "phone" in reply.lower()

    state, reply = apply_conversation_lead_capture(state, "+1 415-555-0199")
    assert state["data"]["phone"] == "+1 415-555-0199"
    assert state["status"] == "completed"
    assert "thank" in reply.lower()


def test_greeting_starts_natural_conversation_flow():
    state, reply = apply_conversation_lead_capture({}, "Hi")
    assert state["active"] is True
    assert state["current_field"] == "context"
    assert "problem" in reply.lower() or "workflow" in reply.lower() or "manual work" in reply.lower()


def test_name_reply_during_context_is_not_misread_as_requirement():
    state, _ = apply_conversation_lead_capture({}, "Hi")
    state, reply = apply_conversation_lead_capture(state, "I am Alex")
    assert state["data"]["name"] == "Alex"
    assert state["current_field"] == "email"
    assert "email" in reply.lower()


def test_negative_sentiment_does_not_force_lead_collection():
    state, reply = apply_conversation_lead_capture({}, "I am not interested and frustrated")
    assert state["status"] == "declined"
    assert "not interested" in reply.lower() or "thanks" in reply.lower()
