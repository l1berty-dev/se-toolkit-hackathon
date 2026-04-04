import requests
import os
import json

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def get_deadlines(course_id=None):
    """
    Returns a list of upcoming deadlines for the user's courses.
    Args:
        course_id (int, optional): Filter by course ID.
    """
    try:
        url = f"{API_BASE_URL}/assignments"
        params = {"course_id": course_id} if course_id else {}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return json.dumps(response.json(), default=str)
    except Exception as e:
        return f"Error fetching deadlines: {str(e)}"

if __name__ == "__main__":
    import sys
    # This part depends on how Nanobot calls tools. 
    # Usually, it's just a Python script that outputs JSON or is imported.
    # For now, let's keep it simple as a function.
    print(get_deadlines())
