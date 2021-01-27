import flask
import sqlalchemy

from ruddock import search_utils
from ruddock.resources import MemberSearchMode

def search_members_by_name(query, mode=None):
  """
  Searches members by name. Returns a list of user_id values that match the
  search query. By default, this searches all members. If mode is set to
  'current', then only current members are searched. If mode is set to
  'alumni', then only alumni are searched.
  """
  table = "members NATURAL JOIN members_extra"
  if mode is None:
    pass
  elif mode == "current":
    table += " NATURAL JOIN members_current"
  elif mode == "alumni":
    table += " NATURAL JOIN members_alumni"
  else:
    # Invalid request.
    raise ValueError

  # Don't name this 'query'!
  db_query = sqlalchemy.text("""
    SELECT user_id, name
    FROM {}
    ORDER BY name
    """.format(table))
  members = flask.g.db.execute(db_query)

  # Results from the search
  results = []

  # Parse the query.
  query_keywords = search_utils.parse_keywords(query)
  # Nothing to search here.
  if len(query_keywords) < 1:
    return results

  # The last keyword is special, since it can be a partial match (this handles
  # the case where the user is still typing).
  last_keyword = query.lower().split()[-1]

  # We want names that match every keyword in the query, allowing partial
  # matches on the last word.
  for member in members:
    member_keywords = search_utils.parse_keywords(member['name'])
    matches = search_utils.count_matches(member_keywords,
        query_keywords, [last_keyword])
    if matches >= len(query_keywords):
      results.append(member['user_id'])
  return results

# Template for queries (to reduce redundancy).
# Remainder of FROM clause and optional WHERE clause is customizable.
BASE_USER_QUERY = """
SELECT user_id, first_name, last_name, email, member_type, birthday,
  matriculation_year, graduation_year, msc, phone, building, room_number, major
FROM members
  NATURAL JOIN members_extra
  NATURAL LEFT JOIN users
{0}
ORDER BY user_id
"""

def get_member(user_id):
  """
  Loads details for the requested user. Returns None if no valid
  user exists.
  """
  query = sqlalchemy.text(BASE_USER_QUERY.format(
    "WHERE user_id = :i"))
  result = flask.g.db.execute(query, i=user_id).first()
  # Technically this does exactly the same thing as returning result
  # immediately, but it's a bit more clear what's going on this way.
  if result is None:
    return None
  return result