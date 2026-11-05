"""pgl.news.*: PGL news and announcements."""
from api.routes import Query, endpoint


@endpoint("pgl.news.information_list")
def information_list(_query: Query) -> dict:
    """Return a placeholder with no announcements."""
    return {"list": [], "total_count": 0}
