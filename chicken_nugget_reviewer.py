from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("tasteful-panthers-firebase-adminsdk-fbsvc-e6f97e55eb.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def today_key():
    now = datetime.now()
    return f"{now.year}-{now.month:02d}-{now.day:02d}"

def seed_reviews_today():
    # Get all users
    users = list(db.collection("users").stream())
    user_info = []
    for u in users:
        data = u.to_dict() or {}
        username = data.get("displayName") or data.get("name") or u.id
        user_info.append((u.id, username))

    # Get today's meals
    date_key = today_key()
    meals_ref = db.collection("meals").document(date_key).collection("meals")
    meals_docs = list(meals_ref.stream())
    meals = [(m.id, m.to_dict()) for m in meals_docs]

    # Filter only chicken nuggets
    nuggets = [(m_id, m) for m_id, m in meals if m.get("name", "").lower() == "chicken nuggets"]

    if not nuggets:
        print(f"❌ No 'chicken nuggets' meal found for {date_key}")
        return

    nugget_id, nugget_data = nuggets[0]
    nugget_name = nugget_data.get("name", "chicken nuggets")

    print(f"Found {len(user_info)} users and 1 'chicken nuggets' meal for {date_key}")

    for uid, username in user_info:
        review_id = f"{uid}_{nugget_id}"
        review_data = {
            "userId": uid,
            "meal": nugget_name,
            "rating": 5.0,
            "tags": [],
            "reviewText": "Chicken nuggets are the best!",
            "mediaUrl": None,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "test": True,
        }
        db.collection("reviews").document(review_id).set(review_data)
        print(f"✅ Seeded chicken nuggets review for user {username} ({uid})")

if __name__ == "__main__":
    seed_reviews_today()