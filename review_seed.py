import random
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

    print(f"Found {len(user_info)} users and {len(meals)} meals for {date_key}")

    for uid, username in user_info:
        sampled_meals = random.sample(meals, min(10, len(meals)))  # Pick up to 10 meals

        for meal_id, meal in sampled_meals:
            meal_name = meal.get("name", "Unknown Meal")
            review_id = f"{uid}_{meal_id}"

            review_data = {
                "userId": uid,
                "meal": meal_name,
                "rating": round(random.uniform(1.0, 5.0), 1),
                "tags": [],
                "reviewText": f"Test review gibberish {random.randint(1000,9999)}",
                "mediaUrl": None,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "test": True,
            }

            db.collection("reviews").document(review_id).set(review_data)

        print(f"✅ Seeded {len(sampled_meals)} reviews for user {username} ({uid})")


if __name__ == "__main__":
    seed_reviews_today()