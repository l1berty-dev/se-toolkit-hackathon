import requests
import os
import json

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def get_grades(student_id="student_01"):
    """
    Returns a list of grades for the current user.
    """
    try:
        url = f"{API_BASE_URL}/grades"
        params = {"student_id": student_id}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return json.dumps(response.json(), default=str)
    except Exception as e:
        return f"Error fetching grades: {str(e)}"

if __name__ == "__main__":
    print(get_grades())
