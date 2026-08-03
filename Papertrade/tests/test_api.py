import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test database URL before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_papertrade.db"

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_papertrade.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestPaperTradeAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if os.path.exists("./test_papertrade.db"):
            try:
                os.remove("./test_papertrade.db")
            except OSError:
                pass


    def setUp(self):
        # Clear tables between tests
        db = TestingSessionLocal()
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()

    def _create_user(self, username="trader1", email="trader1@example.com", password="password123"):
        response = self.client.post(
            "/auth/signup",
            json={"username": username, "email": email, "password": password},
        )
        return response

    def _get_token(self, username="trader1", password="password123"):
        login_res = self.client.post(
            "/auth/login",
            data={"username": username, "password": password},
        )
        return login_res.json()["access_token"]


    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("PaperTrade", response.text)


    def test_signup_and_login(self):
        # Successful signup
        res = self._create_user()
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["username"], "trader1")
        self.assertEqual(data["balance"], 100000.0)

        # Duplicate signup should fail
        dup_res = self._create_user()
        self.assertEqual(dup_res.status_code, 400)

        # Login success via JSON payload
        token = self._get_token()
        self.assertTrue(len(token) > 0)

        # Login success via Form-Data (what Swagger UI Authorize button uses)
        form_login = self.client.post(
            "/auth/login",
            data={"username": "trader1", "password": "password123"},
        )
        self.assertEqual(form_login.status_code, 200)
        self.assertTrue(len(form_login.json()["access_token"]) > 0)

        # Login invalid pass
        bad_login = self.client.post(
            "/auth/login",
            data={"username": "trader1", "password": "wrongpassword"},
        )
        self.assertEqual(bad_login.status_code, 401)



    def test_unauthorized_access(self):
        res = self.client.get("/portfolio/holdings")
        self.assertEqual(res.status_code, 401)

    @patch("app.services.trade_service.get_current_price", return_value=150.0)
    @patch("app.routers.portfolio_router.get_current_price", return_value=150.0)
    @patch("app.routers.watchlist_router.get_current_price", return_value=150.0)
    def test_buy_and_sell_flow(self, mock_price1, mock_price2, mock_price3):
        self._create_user()
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Buy 10 AAPL @ 150.0 = $1500
        buy_res = self.client.post(
            "/trade/buy",
            json={"symbol": "AAPL", "quantity": 10},
            headers=headers,
        )
        self.assertEqual(buy_res.status_code, 200)
        self.assertEqual(buy_res.json()["symbol"], "AAPL")
        self.assertEqual(buy_res.json()["price"], 150.0)
        self.assertEqual(buy_res.json()["quantity"], 10)

        # Check holdings
        holdings_res = self.client.get("/portfolio/holdings", headers=headers)
        self.assertEqual(holdings_res.status_code, 200)
        holdings = holdings_res.json()
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]["symbol"], "AAPL")
        self.assertEqual(holdings[0]["quantity"], 10)

        # Check summary: cash balance = 100000 - 1500 = 98500
        summary_res = self.client.get("/portfolio/summary", headers=headers)
        self.assertEqual(summary_res.status_code, 200)
        self.assertEqual(summary_res.json()["cash_balance"], 98500.0)
        self.assertEqual(summary_res.json()["invested_value"], 1500.0)
        self.assertEqual(summary_res.json()["net_worth"], 100000.0)

        # 2. Sell 5 AAPL @ 150.0 = $750 proceeds
        sell_res = self.client.post(
            "/trade/sell",
            json={"symbol": "AAPL", "quantity": 5},
            headers=headers,
        )
        self.assertEqual(sell_res.status_code, 200)

        # Verify holdings quantity reduced to 5
        holdings_after_sell = self.client.get("/portfolio/holdings", headers=headers).json()
        self.assertEqual(holdings_after_sell[0]["quantity"], 5)

        # Check badges earned (First Trade, Profit Taker)
        badges_res = self.client.get("/badges/", headers=headers)
        self.assertEqual(badges_res.status_code, 200)
        badge_names = [b["badge_name"] for b in badges_res.json()]
        self.assertIn("First Trade", badge_names)
        self.assertIn("Profit Taker", badge_names)

    @patch("app.services.trade_service.get_current_price", return_value=100.0)
    def test_buy_invalid_quantity_or_funds(self, mock_price):
        self._create_user()
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Quantity 0 or negative
        invalid_qty = self.client.post(
            "/trade/buy",
            json={"symbol": "AAPL", "quantity": 0},
            headers=headers,
        )
        self.assertEqual(invalid_qty.status_code, 422)  # Pydantic Field(gt=0)

        # Too expensive buy (more than 100,000 cash balance)
        too_much = self.client.post(
            "/trade/buy",
            json={"symbol": "AAPL", "quantity": 2000},  # 2000 * 100 = 200,000
            headers=headers,
        )
        self.assertEqual(too_much.status_code, 400)
        self.assertIn("Insufficient virtual balance", too_much.json()["detail"])

    @patch("app.routers.watchlist_router.get_current_price", return_value=200.0)
    def test_watchlist(self, mock_price):
        self._create_user()
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Add symbol
        add_res = self.client.post("/watchlist/add", json={"symbol": "MSFT"}, headers=headers)
        self.assertEqual(add_res.status_code, 200)

        # Duplicate add
        dup_add = self.client.post("/watchlist/add", json={"symbol": "MSFT"}, headers=headers)
        self.assertEqual(dup_add.status_code, 400)

        # Get watchlist
        get_res = self.client.get("/watchlist/", headers=headers)
        self.assertEqual(get_res.status_code, 200)
        items = get_res.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["symbol"], "MSFT")
        self.assertEqual(items[0]["current_price"], 200.0)

        # Remove symbol
        rem_res = self.client.delete("/watchlist/remove/MSFT", headers=headers)
        self.assertEqual(rem_res.status_code, 200)

        # Verify empty watchlist
        get_res_empty = self.client.get("/watchlist/", headers=headers)
        self.assertEqual(len(get_res_empty.json()), 0)

    @patch("app.routers.portfolio_router.get_current_price", return_value=100.0)
    def test_leaderboard(self, mock_price):
        # Create two users
        self._create_user(username="user_a", email="usera@example.com")
        self._create_user(username="user_b", email="userb@example.com")

        token = self._get_token(username="user_a")
        headers = {"Authorization": f"Bearer {token}"}

        lb_res = self.client.get("/portfolio/leaderboard", headers=headers)
        self.assertEqual(lb_res.status_code, 200)
        lb = lb_res.json()
        self.assertEqual(len(lb), 2)
        self.assertEqual(lb[0]["rank"], 1)
        self.assertEqual(lb[1]["rank"], 2)


if __name__ == "__main__":
    unittest.main()
