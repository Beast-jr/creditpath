import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _post(endpoint: str, payload: dict) -> dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Cannot connect to API at {API_BASE_URL}. Is the backend running?")
    except requests.exceptions.Timeout:
        raise TimeoutError("API request timed out. Please try again.")
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        raise ValueError(f"API error: {detail}")


def assess(profile_dict: dict) -> dict:
    return _post("/assess", profile_dict)


def recommend(profile_dict: dict) -> dict:
    return _post("/recommend", profile_dict)


def whatif(profile_dict: dict) -> dict:
    return _post("/whatif", profile_dict)
