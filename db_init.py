import requests
import firebase_admin
from firebase_admin import credentials, firestore
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from Allergen import Allergen
from Item import Item

# SCRAPE INFO
MENU_URL = "https://app.mymenumanager.net/fit/ajax.php"

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://app.mymenumanager.net',
    'Connection': 'keep-alive',
    'Referer': 'https://app.mymenumanager.net/fit/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

today = datetime.now().strftime("%Y-%m-%d")
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

# FIREBASE INFO
cred = credentials.Certificate('tasteful-panthers-firebase-adminsdk-fbsvc-e6f97e55eb.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


# DATABASE CLEAR FUNCTION
def clear_all_meals():
    meals_ref = db.collection('meals')
    collections = db.collections()
    for collection in collections:
        print(collection.id)
        for doc in collection.stream():
            print(f"\t{doc.id}")

    # Freeze the stream into a list before iterating.
    docs = meals_ref.stream()


    for doc in docs:

        print(f"Deleting parent document: {doc.id}")
        # Freeze the subcollection stream as well.
        subcollection_ref = doc.reference.collection('meals')
        sub_docs = list(subcollection_ref.stream())
        for sub_doc in sub_docs:
            print(f"   Deleting subcollection document: {sub_doc.id} under {doc.id}")
            sub_doc.reference.delete()
        # Delete the parent date document after its subcollection has been cleared.
        doc.reference.delete()

    print('All meals (and their subcollections) have been cleared from the database.')



# DATABASE WRITE FUNCTION
def write_meals(items, date):
    # Create or get the date document
    date_ref = db.collection('meals').document(date)
    date_ref.set({})
    allergen_ref = db.collection('allergens')

    # Write each meal into the 'meals' subcollection under the date document.
    for item in items:
        meal_data = {
            'name': item.name,
            'meal_type': item.meal_type,
            'allergens': [allergen.symbol for allergen in item.allergens]
        }
        # Use .add() to auto-generate a document ID for each meal.
        date_ref.collection('meals').add(meal_data)

    # Write allergens to a separate collection
    allergens = {}
    for item in items:
        for allergen in item.allergens:
            allergens[allergen.symbol] = allergen.full

    for symbol in allergens:
        allergen_ref.document(symbol).set({'full': allergens[symbol]})

    print(f'{date} meals + allergens written to database...')


# SCRAPE FUNCTION
def parse_day(date):
    print(f'----------------------------------------------------------------------------------')
    print(f'DATE: {date}')
    print(f'----------------------------------------------------------------------------------')

    data = {
        'action': 'getMenus',
        'concept_id': '5',
        'calendar_date': f'{date}',
    }

    response = requests.post(MENU_URL, headers=headers, data=data)

    # check if request was successful
    if response.status_code == 200:
        print("Connection Successfully Established.")
    else:
        print("Error!")

    soup = BeautifulSoup(response.text, "html.parser")

    menu_blocks_divs = soup.select('div[class^="menu_blocks"]')

    items = []

    breakfast, lunch, dinner = None, None, None

    for div in menu_blocks_divs:
        classes = div.get('class')

        if 'meal1' in classes:
            breakfast = div
        if 'meal2' in classes:
            lunch = div
        if 'meal3' in classes:
            dinner = div

    meals = [breakfast, lunch, dinner]

    # PARSE MEALS
    for meal in meals:
        # Grab the menu block for this meal and get all sub-blocks that contain dish info
        pdh_menu_block = meal.find('div', class_='menu_block', attrs={"data-restaurant": "5"})
        g_bullets = pdh_menu_block.select('div[class^="g bullet"]')
        # Remove the first element if it is not an actual item (for example, sometimes a header)
        g_bullets.pop(0)

        # Loop through each category in the meal
        for bul in g_bullets:
            category = bul.select('div[class^="group_titles"]')
            #category = category[0].select('div[class^="group_title"]')[0]

            category_items = bul.find('ul', class_=False).find_all('li')

            # Loop through each dish in the category
            for item in category_items:
                item_span = item.select('span[class^="nutrition"]')
                # The HTML structure might differ sometimes
                if item_span:
                    item_name = item_span[0].text
                else:
                    item_name = item.text

                # Parse allergens
                allergens = item.find_all('span', title=True)
                allergen_objects = []

                for allergen in allergens:
                    allergen_symbol = allergen.text
                    allergen_full = allergen['title']
                    allergen_object = Allergen(allergen_symbol, allergen_full)
                    allergen_objects.append(allergen_object)

                # Determine the meal type based on which meal block we are parsing
                category_name = ""
                if meal == breakfast:
                    category_name = "Breakfast"
                elif meal == lunch:
                    category_name = "Lunch"
                elif meal == dinner:
                    category_name = "Dinner"

                if item_name:
                    curr_item = Item(item_name, allergen_objects, category_name)
                    items.append(curr_item)

        # Deduplicate items: Remove duplicates with the same (meal_type, name)
        total_count = len(items)
        deduped = {}
        for item in items:
            key = (item.meal_type, item.name)
            if key not in deduped:
                deduped[key] = item
        deduped_items = list(deduped.values())
        print(f"Deduplicated items: {len(deduped_items)} out of {total_count}")


    write_meals(deduped_items, date)

clear_all_meals()
parse_day(today)
parse_day(tomorrow)
