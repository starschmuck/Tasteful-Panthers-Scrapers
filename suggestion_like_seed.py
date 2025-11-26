import random
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("tasteful-panthers-firebase-adminsdk-fbsvc-e6f97e55eb.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def reseed_suggestion_likes():
    suggestions_ref = db.collection("suggestions")
    suggestions = list(suggestions_ref.stream())
    print(f"Found {len(suggestions)} suggestions")

    for s in suggestions:
        suggestion_id = s.id
        random_likes = random.randint(0, 100)  # adjust range as needed
        suggestions_ref.document(suggestion_id).update({"likes": random_likes})
        print(f"👍 Assigned {random_likes} likes to suggestion {suggestion_id}")

def reseed_review_likes():
    reviews_ref = db.collection("reviews")
    reviews = list(reviews_ref.stream())
    print(f"Found {len(reviews)} reviews")

    for r in reviews:
        data = r.to_dict() or {}
        review_id = r.id

        if "likes" in data:  # only reseed if likes already exists
            random_likes = random.randint(0, 100)
            reviews_ref.document(review_id).update({"likes": random_likes})
            print(f"🔄 Reset likes to {random_likes} for review {review_id}")

def reseed_all_likes():
    reseed_suggestion_likes()
    reseed_review_likes()

if __name__ == "__main__":
    reseed_all_likes()