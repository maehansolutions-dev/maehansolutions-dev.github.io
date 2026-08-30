from datetime import datetime, timezone

from database.mongo import get_database


class ChatRepository:
    def create_session(self, session_id):
        now = datetime.now(timezone.utc)
        get_database()["chat_sessions"].update_one({"session_id": session_id}, {"$setOnInsert": {"session_id": session_id, "created_at": now, "status": "active"}, "$set": {"updated_at": now}}, upsert=True)

    def session(self, session_id):
        return get_database()["chat_sessions"].find_one({"session_id": session_id}, {"_id": 0}) or {}

    def update_session(self, session_id, updates):
        get_database()["chat_sessions"].update_one({"session_id": session_id}, {"$set": {**updates, "updated_at": datetime.now(timezone.utc)}})

    def add_message(self, session_id, role, content):
        now = datetime.now(timezone.utc)
        get_database()["chat_messages"].insert_one({"session_id": session_id, "role": role, "content": content, "timestamp": now})
        get_database()["chat_sessions"].update_one({"session_id": session_id}, {"$set": {"updated_at": now}})

    def set_lead_capture_state(self, session_id, lead_state):
        self.update_session(session_id, {"lead_capture": lead_state})

    def lead_capture_state(self, session_id):
        return self.session(session_id).get("lead_capture", {})

    def history(self, session_id):
        rows = get_database()["chat_messages"].find({"session_id": session_id}, {"_id": 0, "role": 1, "content": 1}).sort("timestamp", 1).limit(12)
        return list(rows)
