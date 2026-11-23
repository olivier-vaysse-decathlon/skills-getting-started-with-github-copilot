import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregistrationTests(unittest.TestCase):
    def setUp(self):
        self.activities_patch = patch.dict(
            activities,
            {
                "Chess & Games": {
                    "description": "Chess",
                    "schedule": "Friday",
                    "max_participants": 5,
                    "participants": [
                        "student+chess@example.com",
                        "other@example.com",
                        "student+chess@example.com",
                    ],
                },
                "Art": {
                    "description": "Art",
                    "schedule": "Monday",
                    "max_participants": 5,
                    "participants": ["student+chess@example.com"],
                },
            },
            clear=True,
        )
        self.activities_patch.start()
        self.addCleanup(self.activities_patch.stop)
        self.client = TestClient(app)

    def test_unregister_removes_all_registrations_only_for_selected_activity(self):
        path = "/activities/Chess%20%26%20Games/signup"
        email = "student+chess@example.com"

        response = self.client.delete(path, params={"email": email})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(activities["Chess & Games"]["participants"], ["other@example.com"])
        self.assertEqual(activities["Art"]["participants"], [email])
        self.assertEqual(self.client.post(path, params={"email": email}).status_code, 200)

    def test_unregister_reports_missing_activity_or_participant(self):
        missing_activity = self.client.delete(
            "/activities/Unknown/signup", params={"email": "student@example.com"}
        )
        missing_participant = self.client.delete(
            "/activities/Art/signup", params={"email": "student@example.com"}
        )

        self.assertEqual(missing_activity.status_code, 404)
        self.assertEqual(missing_activity.json()["detail"], "Activity not found")
        self.assertEqual(missing_participant.status_code, 404)
        self.assertEqual(
            missing_participant.json()["detail"], "Student is not signed up for this activity"
        )
        self.assertEqual(activities["Art"]["participants"], ["student+chess@example.com"])


if __name__ == "__main__":
    unittest.main()
