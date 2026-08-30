import logging
from functools import lru_cache

from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_database():
    """Create one lazily-initialized client; callers never receive credentials."""
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
    return client[settings.MONGODB_DATABASE]


def database_is_available():
    try:
        get_database().command("ping")
        return True
    except PyMongoError:
        logger.warning("MongoDB health check failed")
        return False
