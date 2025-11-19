from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("tasteful-panthers-firebase-adminsdk-fbsvc-e6f97e55eb.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def backfill_popularity():
    print(f"🚀 Starting backfill at {datetime.now()}")

    # Step 1: Scan all reviews
    reviews_ref = db.collection("reviews")
    reviews = list(reviews_ref.stream())
    print(f"🔎 Found {len(reviews)} reviews")

    user_totals = {}
    review_updates = 0

    for r in reviews:
        data = r.to_dict() or {}
        uid = data.get("userId")
        if not uid:
            print(f"⚠️ Review {r.id} missing userId, skipping")
            continue

        likes = data.get("likes")
        if not isinstance(likes, int):
            likes = 0
            db.collection("reviews").document(r.id).update({"likes": 0})
            review_updates += 1
            print(f"🛠️ Fixed missing likes on review {r.id}")

        user_totals[uid] = user_totals.get(uid, 0) + likes

    print(f"✅ Processed reviews. Fixed {review_updates} missing likes fields.")
    print(f"📊 Aggregated totals for {len(user_totals)} users")

    # Step 2: Write userPopularity docs
    for uid, total in user_totals.items():
        user_doc = db.collection("users").document(uid).get()
        username = uid
        if user_doc.exists:
            udata = user_doc.to_dict() or {}
            username = udata.get("username", uid)

        pop_ref = db.collection("userPopularity").document(uid)
        pop_ref.set({
            "userId": uid,
            "username": username,
            "totalLikes": total,
            "lastUpdated": firestore.SERVER_TIMESTAMP,
        }, merge=True)

        print(f"⭐ Updated popularity for {username} ({uid}): {total} likes")

    print(f"🎉 Backfill complete at {datetime.now()}")

if __name__ == "__main__":
    backfill_popularity()