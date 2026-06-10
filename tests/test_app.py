from copy import deepcopy
from urllib.parse import quote

from fastapi.testclient import TestClient
import pytest

import src.app as app_module


client = TestClient(app_module.app)
original_activities = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    app_module.activities = deepcopy(original_activities)
    yield
    app_module.activities = deepcopy(original_activities)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog():
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant_and_rejects_duplicates():
    activity_name = "Soccer Club"
    encoded_activity = quote(activity_name)

    signup_response = client.post(
        f"/activities/{encoded_activity}/signup",
        params={"email": "student@mergington.edu"},
    )

    duplicate_response = client.post(
        f"/activities/{encoded_activity}/signup",
        params={"email": "student@mergington.edu"},
    )

    assert signup_response.status_code == 200
    assert signup_response.json() == {
        "message": f"Signed up student@mergington.edu for {activity_name}"
    }
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"
    assert "student@mergington.edu" in app_module.activities[activity_name]["participants"]


def test_unregister_removes_participant_and_rejects_missing_participant():
    activity_name = "Gym Class"
    encoded_activity = quote(activity_name)
    email = "john@mergington.edu"

    unregister_response = client.delete(
        f"/activities/{encoded_activity}/signup",
        params={"email": email},
    )

    missing_response = client.delete(
        f"/activities/{encoded_activity}/signup",
        params={"email": email},
    )

    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert missing_response.status_code == 400
    assert missing_response.json()["detail"] == "Student is not signed up for this activity"
    assert email not in app_module.activities[activity_name]["participants"]