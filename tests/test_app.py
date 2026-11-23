from copy import deepcopy

import pytest

from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def activity_data(monkeypatch):
    data = {
        "Chess & Games": {
            "description": "Chess",
            "schedule": "Friday",
            "max_participants": 5,
            "participants": [
                "student+chess@example.com",
                "other@example.com",
            ],
        },
        "Art": {
            "description": "Art",
            "schedule": "Monday",
            "max_participants": 5,
            "participants": ["student+chess@example.com"],
        },
    }
    monkeypatch.setattr(app_module, "activities", data)
    return data


@pytest.fixture
def client(activity_data):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_served_frontend(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)
    page = client.get(expected_location)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]


def test_get_activities_returns_details_and_participants(client, activity_data):
    # Arrange
    activity_data["Art"]["participants"].clear()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activity_data


def test_get_activities_returns_empty_dictionary_when_no_activities_exist(
    client, activity_data
):
    # Arrange
    activity_data.clear()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {}


def test_signup_adds_participant_only_to_selected_activity(client, activity_data):
    # Arrange
    email = "new+art@example.com"

    # Act
    response = client.post("/activities/Art/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Art"}
    assert activity_data["Art"]["participants"] == [
        "student+chess@example.com",
        email,
    ]
    assert activity_data["Chess & Games"]["participants"] == [
        "student+chess@example.com",
        "other@example.com",
    ]


def test_signup_rejects_duplicate_without_changing_activities(client, activity_data):
    # Arrange
    expected_activities = deepcopy(activity_data)

    # Act
    response = client.post(
        "/activities/Art/signup", params={"email": "student+chess@example.com"}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activity_data == expected_activities


def test_signup_reports_missing_activity_without_changing_activities(
    client, activity_data
):
    # Arrange
    expected_activities = deepcopy(activity_data)

    # Act
    response = client.post(
        "/activities/Unknown/signup", params={"email": "student@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data == expected_activities


def test_unregister_removes_all_registrations_only_for_selected_activity(
    client, activity_data
):
    # Arrange
    path = "/activities/Chess%20%26%20Games/signup"
    email = "student+chess@example.com"
    activity_data["Chess & Games"]["participants"].append(email)

    # Act
    response = client.delete(path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess & Games"}
    assert activity_data["Chess & Games"]["participants"] == ["other@example.com"]
    assert activity_data["Art"]["participants"] == ["student+chess@example.com"]

    # Act
    signup_response = client.post(path, params={"email": email})

    # Assert
    assert signup_response.status_code == 200
    assert activity_data["Chess & Games"]["participants"] == [
        "other@example.com",
        email,
    ]


def test_unregister_reports_missing_activity_without_changing_activities(
    client, activity_data
):
    # Arrange
    expected_activities = deepcopy(activity_data)

    # Act
    response = client.delete(
        "/activities/Unknown/signup", params={"email": "student@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data == expected_activities


def test_unregister_reports_missing_participant_without_changing_activities(
    client, activity_data
):
    # Arrange
    expected_activities = deepcopy(activity_data)

    # Act
    response = client.delete(
        "/activities/Art/signup", params={"email": "student@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activity_data == expected_activities
