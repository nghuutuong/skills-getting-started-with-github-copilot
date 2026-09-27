from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activity = response.json()["Basketball Team"]
    assert set(activity) == {"description", "schedule", "max_participants", "participants"}
    assert activity["participants"] == []


def test_signup_adds_participant(client):
    email = "student@example.com"

    response = client.post("/activities/Basketball Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Basketball Team"}
    assert email in activities["Basketball Team"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "student@example.com"
    client.post("/activities/Basketball Team/signup", params={"email": email})

    response = client.post("/activities/Basketball Team/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities["Basketball Team"]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post("/activities/Unknown Activity/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = "student@example.com"
    client.post("/activities/Basketball Team/signup", params={"email": email})

    response = client.delete("/activities/Basketball Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Basketball Team"}
    assert email not in activities["Basketball Team"]["participants"]


def test_unregister_rejects_nonparticipant(client):
    response = client.delete(
        "/activities/Basketball Team/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"