import sqlite3


DATABASE = "travelbytes.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():

    connection = get_connection()

    # ==========================================
    # PLACES TABLE
    # ==========================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            category TEXT NOT NULL,
            cost INTEGER DEFAULT 0,
            duration REAL DEFAULT 2,
            rating REAL DEFAULT 0,
            indoor INTEGER DEFAULT 0,
            tags TEXT
        )
    """)

    # ==========================================
    # BUSINESSES TABLE
    # ==========================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            price_range TEXT,
            rating REAL DEFAULT 0,
            location TEXT,
            tags TEXT
        )
    """)

    connection.commit()

    # ==========================================
    # TOURIST PLACES DATA
    # ==========================================

    places = [

        # --------------------------------------
        # KOLKATA
        # --------------------------------------

        (
            "Victoria Memorial",
            "Kolkata",
            "Heritage",
            50,
            2.5,
            4.6,
            0,
            "heritage,history,photography"
        ),

        (
            "Indian Museum",
            "Kolkata",
            "Museum",
            50,
            2.5,
            4.5,
            1,
            "history,culture,museum"
        ),

        (
            "Eco Park",
            "Kolkata",
            "Nature",
            50,
            3,
            4.4,
            0,
            "nature,family,photography"
        ),

        (
            "Science City",
            "Kolkata",
            "Science",
            100,
            3,
            4.5,
            1,
            "science,family,education"
        ),

        (
            "Park Street",
            "Kolkata",
            "Food",
            500,
            2,
            4.4,
            0,
            "food,shopping,nightlife"
        ),

        # --------------------------------------
        # JAIPUR
        # --------------------------------------

        (
            "Hawa Mahal",
            "Jaipur",
            "Heritage",
            50,
            1.5,
            4.7,
            0,
            "heritage,history,photography"
        ),

        (
            "City Palace",
            "Jaipur",
            "Heritage",
            200,
            2.5,
            4.6,
            1,
            "heritage,history,culture"
        ),

        (
            "Jantar Mantar",
            "Jaipur",
            "Science",
            100,
            1.5,
            4.5,
            0,
            "science,history,education"
        ),

        (
            "Albert Hall Museum",
            "Jaipur",
            "Museum",
            50,
            2,
            4.6,
            1,
            "museum,history,culture"
        ),

        (
            "Jal Mahal",
            "Jaipur",
            "Nature",
            0,
            1,
            4.5,
            0,
            "nature,photography,heritage"
        ),

        # --------------------------------------
        # DELHI
        # --------------------------------------

        (
            "India Gate",
            "Delhi",
            "Heritage",
            0,
            1,
            4.7,
            0,
            "heritage,history,photography"
        ),

        (
            "Red Fort",
            "Delhi",
            "Heritage",
            35,
            2,
            4.6,
            0,
            "heritage,history,culture"
        ),

        (
            "National Museum",
            "Delhi",
            "Museum",
            20,
            2.5,
            4.5,
            1,
            "museum,history,culture"
        ),

        (
            "Lotus Temple",
            "Delhi",
            "Culture",
            0,
            1.5,
            4.6,
            1,
            "culture,photography"
        ),

        (
            "National Zoological Park",
            "Delhi",
            "Nature",
            100,
            3,
            4.3,
            0,
            "nature,family,photography"
        )
    ]

    # ==========================================
    # INSERT PLACES WITHOUT DUPLICATES
    # ==========================================

    for place in places:

        existing_place = connection.execute("""
            SELECT id
            FROM places
            WHERE LOWER(name) = LOWER(?)
            AND LOWER(city) = LOWER(?)
        """, (place[0], place[1])).fetchone()

        if existing_place is None:

            connection.execute("""
                INSERT INTO places
                (
                    name,
                    city,
                    category,
                    cost,
                    duration,
                    rating,
                    indoor,
                    tags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, place)

    connection.commit()

    # ==========================================
    # LOCAL BUSINESS DATA
    # ==========================================

    businesses = [

        # --------------------------------------
        # KOLKATA HOTELS
        # --------------------------------------

        (
            " Central Hotel",
            "Kolkata",
            "hotel",
            "Budget Hotel",
            "₹₹",
            4.2,
            "Park Street",
            "budget,family,central"
        ),

        (
            " Heritage Stay",
            "Kolkata",
            "hotel",
            "Heritage Hotel",
            "₹₹₹",
            4.5,
            "Esplanade",
            "heritage,culture"
        ),

        # --------------------------------------
        # KOLKATA RESTAURANTS
        # --------------------------------------

        (
            " Bengali Kitchen",
            "Kolkata",
            "restaurant",
            "Bengali Cuisine",
            "₹₹",
            4.4,
            "Park Street",
            "food,bengali,culture"
        ),

        (
            " Street Food Hub",
            "Kolkata",
            "restaurant",
            "Street Food",
            "₹",
            4.3,
            "New Market",
            "food,street-food,budget"
        ),

        # --------------------------------------
        # KOLKATA EXPERIENCES
        # --------------------------------------

        (
            " Heritage Walk",
            "Kolkata",
            "experience",
            "Walking Tour",
            "₹₹",
            4.6,
            "B.B.D. Bagh",
            "heritage,history,walking"
        ),

        (
            " Hooghly Sunset Experience",
            "Kolkata",
            "experience",
            "River Experience",
            "₹₹₹",
            4.5,
            "Prinsep Ghat",
            "nature,photography,experience"
        ),

        # --------------------------------------
        # KOLKATA GUIDES
        # --------------------------------------

        (
            " Local History Guide",
            "Kolkata",
            "guide",
            "Local Guide",
            "₹₹",
            4.7,
            "Central Kolkata",
            "guide,history,culture"
        ),

        (
            " Food Tour Guide",
            "Kolkata",
            "guide",
            "Food Guide",
            "₹₹",
            4.6,
            "North Kolkata",
            "guide,food,local"
        ),

        # --------------------------------------
        # JAIPUR HOTELS
        # --------------------------------------

        (
            " Jaipur Heritage Stay",
            "Jaipur",
            "hotel",
            "Heritage Hotel",
            "₹₹₹",
            4.6,
            "Old Jaipur",
            "heritage,culture,family"
        ),

        (
            " Jaipur Budget Hotel",
            "Jaipur",
            "hotel",
            "Budget Hotel",
            "₹",
            4.2,
            "MI Road",
            "budget,family,central"
        ),

        # --------------------------------------
        # JAIPUR RESTAURANTS
        # --------------------------------------

        (
            " Rajasthani Kitchen",
            "Jaipur",
            "restaurant",
            "Rajasthani Cuisine",
            "₹₹",
            4.5,
            "Old Jaipur",
            "food,culture,rajasthani"
        ),

        (
            " Jaipur Street Food",
            "Jaipur",
            "restaurant",
            "Street Food",
            "₹",
            4.3,
            "Johari Bazaar",
            "food,street-food,budget"
        ),

        # --------------------------------------
        # JAIPUR EXPERIENCES
        # --------------------------------------

        (
            " Jaipur Heritage Walk",
            "Jaipur",
            "experience",
            "Heritage Walk",
            "₹₹",
            4.7,
            "Old Jaipur",
            "heritage,history,walking"
        ),

        (
            " Jaipur Cultural Experience",
            "Jaipur",
            "experience",
            "Cultural Experience",
            "₹₹₹",
            4.5,
            "Amer",
            "culture,heritage,experience"
        ),

        # --------------------------------------
        # JAIPUR GUIDES
        # --------------------------------------

        (
            " Jaipur History Guide",
            "Jaipur",
            "guide",
            "Local History Guide",
            "₹₹",
            4.7,
            "Old Jaipur",
            "guide,history,culture"
        ),

        (
            " Jaipur Food Guide",
            "Jaipur",
            "guide",
            "Food Guide",
            "₹₹",
            4.5,
            "Johari Bazaar",
            "guide,food,local"
        ),

        # --------------------------------------
        # DELHI HOTELS
        # --------------------------------------

        (
            " Delhi Central Hotel",
            "Delhi",
            "hotel",
            "Budget Hotel",
            "₹₹",
            4.2,
            "Connaught Place",
            "budget,family,central"
        ),

        (
            " Delhi Heritage Stay",
            "Delhi",
            "hotel",
            "Heritage Hotel",
            "₹₹₹",
            4.5,
            "Old Delhi",
            "heritage,culture,history"
        ),

        # --------------------------------------
        # DELHI RESTAURANTS
        # --------------------------------------

        (
            " Delhi Food House",
            "Delhi",
            "restaurant",
            "North Indian Cuisine",
            "₹₹",
            4.4,
            "Connaught Place",
            "food,culture,family"
        ),

        (
            " Delhi Street Food",
            "Delhi",
            "restaurant",
            "Street Food",
            "₹",
            4.3,
            "Chandni Chowk",
            "food,street-food,budget"
        ),

        # --------------------------------------
        # DELHI EXPERIENCES
        # --------------------------------------

        (
            " Delhi Heritage Walk",
            "Delhi",
            "experience",
            "Heritage Walk",
            "₹₹",
            4.6,
            "Old Delhi",
            "heritage,history,walking"
        ),

        (
            " Delhi Cultural Experience",
            "Delhi",
            "experience",
            "Cultural Experience",
            "₹₹",
            4.5,
            "Central Delhi",
            "culture,history,experience"
        ),

        # --------------------------------------
        # DELHI GUIDES
        # --------------------------------------

        (
            " Delhi History Guide",
            "Delhi",
            "guide",
            "Local History Guide",
            "₹₹",
            4.7,
            "Old Delhi",
            "guide,history,culture"
        ),

        (
            " Delhi Food Guide",
            "Delhi",
            "guide",
            "Food Guide",
            "₹₹",
            4.6,
            "Chandni Chowk",
            "guide,food,local"
        )
    ]

    # ==========================================
    # INSERT BUSINESSES WITHOUT DUPLICATES
    # ==========================================

    for business in businesses:

        existing_business = connection.execute("""
            SELECT id
            FROM businesses
            WHERE LOWER(name) = LOWER(?)
            AND LOWER(city) = LOWER(?)
        """, (business[0], business[1])).fetchone()

        if existing_business is None:

            connection.execute("""
                INSERT INTO businesses
                (
                    name,
                    city,
                    type,
                    category,
                    price_range,
                    rating,
                    location,
                    tags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, business)

    connection.commit()

    connection.close()


# ==========================================
# GET TOURIST PLACES
# ==========================================

def get_places(city):

    connection = get_connection()

    places = connection.execute("""
        SELECT *
        FROM places
        WHERE LOWER(city) = LOWER(?)
    """, (city.strip(),)).fetchall()

    connection.close()

    return [dict(place) for place in places]


# ==========================================
# GET LOCAL BUSINESSES
# ==========================================

def get_businesses(city, business_type=None):

    connection = get_connection()

    if business_type:

        businesses = connection.execute("""
            SELECT *
            FROM businesses
            WHERE LOWER(city) = LOWER(?)
            AND LOWER(type) = LOWER(?)
        """, (city.strip(), business_type.strip())).fetchall()

    else:

        businesses = connection.execute("""
            SELECT *
            FROM businesses
            WHERE LOWER(city) = LOWER(?)
        """, (city.strip(),)).fetchall()

    connection.close()

    return [dict(business) for business in businesses]