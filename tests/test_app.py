from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app as fastapi_app


@pytest.fixture
def activity_data():
    return {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing@example.com"],
        },
        "Robotics Club": {
            "description": "Build robots",
            "schedule": "Mondays",
            "max_participants": 10,
            "participants": [],
        },
    }


@pytest.fixture
def client(monkeypatch, activity_data):
    monkeypatch.setattr("src.app.activities", activity_data)
    return TestClient(fastapi_app)


def test_given_activities_when_get_then_returns_all_activity_data(client, activity_data):
    # Given: the app has the isolated activities fixture.
    # When: the activities endpoint is requested.
    response = client.get("/activities")

    # Then: all configured activity data is returned.
    assert response.status_code == 200
    assert response.json() == activity_data


def test_given_unregistered_student_when_signing_up_then_adds_participant(client, activity_data):
    # Given: the student is not yet registered for Chess Club.
    activity_name = "Chess Club"
    email = "new@example.com"

    # When: the student signs up.
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Then: the response succeeds and the participant is added.
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activity_data[activity_name]["participants"]


def test_given_registered_student_when_signing_up_again_then_returns_400(client, activity_data):
    # Given: the student is already registered for Chess Club.
    activity_name = "Chess Club"
    email = "existing@example.com"

    # When: the same student signs up again.
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Then: the request is rejected without duplicating the participant.
    assert response.status_code == 400
    assert activity_data[activity_name]["participants"].count(email) == 1


def test_given_unknown_activity_when_signing_up_then_returns_404(client):
    # Given: the requested activity does not exist.
    activity_name = "Unknown Club"

    # When: a student signs up for it.
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": "student@example.com"},
    )

    # Then: the API reports that the activity was not found.
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_given_registered_participant_when_removed_then_is_unregistered(client, activity_data):
    # Given: a participant is registered for an activity with spaces in its name.
    activity_name = "Chess Club"
    email = "existing@example.com"

    # When: the participant is removed.
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": email},
    )

    # Then: the response succeeds and the participant is no longer registered.
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activity_data[activity_name]["participants"]


def test_given_unknown_activity_when_removing_participant_then_returns_404(client):
    # Given: the requested activity does not exist.
    activity_name = "Unknown Club"

    # When: a participant is removed from it.
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": "student@example.com"},
    )

    # Then: the API reports that the activity was not found.
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_given_unregistered_student_when_removing_then_returns_404(client):
    # Given: the student is not registered for Chess Club.
    activity_name = "Chess Club"
    email = "missing@example.com"

    # When: the student is removed.
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": email},
    )

    # Then: the API reports that the participant was not found.
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}