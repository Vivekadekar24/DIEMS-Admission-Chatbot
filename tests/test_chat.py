import unittest
from backend.app import create_app


class ChatApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = create_app()
        app.config.update(TESTING=True)
        cls.client = app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["index_ready"])

    def test_chat_returns_dataset_answer(self):
        response = self.client.post("/api/chat", json={"message": "Which B.Tech branches are offered at DIEMS?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("CSE", response.json["answer"])
        self.assertTrue(response.json["sources"])

    def test_invalid_and_unknown_questions(self):
        self.assertEqual(self.client.post("/api/chat", json={"message": ""}).status_code, 400)
        response = self.client.post("/api/chat", json={"message": "What is the weather on Mars?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("couldn't find a reliable answer", response.json["answer"])
