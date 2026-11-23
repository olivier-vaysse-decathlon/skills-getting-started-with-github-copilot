import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class BackendAPITests(unittest.TestCase):
    def setUp(self):
        self.activity_data = {
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
        self.activities_patch = patch.dict(activities, self.activity_data, clear=True)
        self.activities_patch.start()
        self.addCleanup(self.activities_patch.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_root_redirects_to_served_frontend(self):
        response = self.client.get("/", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/static/index.html")
        page = self.client.get(response.headers["location"])
        self.assertEqual(page.status_code, 200)
        self.assertIn("text/html", page.headers["content-type"])

    def test_get_activities_returns_details_and_participants(self):
        activities["Art"]["participants"].clear()

        response = self.client.get("/activities")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.activity_data)

    def test_get_activities_returns_empty_dictionary_when_no_activities_exist(self):
        activities.clear()

        response = self.client.get("/activities")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_signup_adds_participant_only_to_selected_activity(self):
        email = "new+art@example.com"
        expected = self.client.get("/activities").json()

        response = self.client.post("/activities/Art/signup", params={"email": email})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": f"Signed up {email} for Art"})
        expected["Art"]["participants"].append(email)
        self.assertEqual(self.client.get("/activities").json(), expected)

    def test_signup_rejects_duplicate_without_changing_activities(self):
        expected = self.client.get("/activities").json()

        response = self.client.post(
            "/activities/Art/signup", params={"email": "student+chess@example.com"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"detail": "Student already signed up for this activity"}
        )
        self.assertEqual(self.client.get("/activities").json(), expected)

    def test_signup_reports_missing_activity_without_changing_activities(self):
        expected = self.client.get("/activities").json()

        response = self.client.post(
            "/activities/Unknown/signup", params={"email": "student@example.com"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(self.client.get("/activities").json(), expected)

    def test_unregister_removes_all_registrations_only_for_selected_activity(self):
        path = "/activities/Chess%20%26%20Games/signup"
        email = "student+chess@example.com"
        activities["Chess & Games"]["participants"].append(email)
        expected = self.client.get("/activities").json()

        response = self.client.delete(path, params={"email": email})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"message": f"Unregistered {email} from Chess & Games"}
        )
        expected["Chess & Games"]["participants"] = ["other@example.com"]
        self.assertEqual(self.client.get("/activities").json(), expected)
        self.assertEqual(self.client.post(path, params={"email": email}).status_code, 200)
        expected["Chess & Games"]["participants"].append(email)
        self.assertEqual(self.client.get("/activities").json(), expected)

    def test_unregister_reports_missing_activity_without_changing_activities(self):
        expected = self.client.get("/activities").json()

        response = self.client.delete(
            "/activities/Unknown/signup", params={"email": "student@example.com"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(self.client.get("/activities").json(), expected)

    def test_unregister_reports_missing_participant_without_changing_activities(self):
        expected = self.client.get("/activities").json()

        response = self.client.delete(
            "/activities/Art/signup", params={"email": "student@example.com"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(), {"detail": "Student is not signed up for this activity"}
        )
        self.assertEqual(self.client.get("/activities").json(), expected)


if __name__ == "__main__":
    unittest.main()
