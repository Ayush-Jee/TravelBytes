# Day 2 — Tourism Data & Local Business Ecosystem

## Date
Day 2 of TravelBytes AI Development

---

# 1. Day 2 Objective

The main objective of Day 2 was to build the tourism data layer of TravelBytes AI.

The system was extended from a basic travel planner into a tourism recommendation platform containing:

- Tourist places
- Hotels
- Restaurants
- Local guides
- Local experiences
- Multiple destination cities
- Interest-based business matching
- Business category filtering
- Database-driven recommendations

---

# 2. What Was Built

## 2.1 Tourism Places Database

A SQLite database was created to store tourist destinations and their properties.

Each tourism place contains:

- Name
- City
- Category
- Estimated cost
- Visit duration
- Rating
- Indoor/Outdoor classification
- Interest tags

Example:

```text
Victoria Memorial
City: Kolkata
Category: Heritage
Cost: ₹50
Duration: 2.5 hours
Rating: 4.6
Type: Outdoor
Tags: heritage, history, photography
3. Local Tourism Business Database

A separate database table was created for tourism-related businesses.

The system currently supports:

Hotels
Restaurants
Guides
Experiences

Each business contains:

Name
City
Type
Category
Price range
Rating
Location
Interest tags

This creates the foundation for connecting tourists with the local tourism ecosystem.

4. Multiple Cities

Tourism data was added for three demo cities:

Kolkata
Jaipur
Delhi

This allows TravelBytes AI to demonstrate that the system is not restricted to a single destination.

5. Database Structure

Two major tables are currently used.

Places Table
places
│
├── id
├── name
├── city
├── category
├── cost
├── duration
├── rating
├── indoor
└── tags
Businesses Table
businesses
│
├── id
├── name
├── city
├── type
├── category
├── price_range
├── rating
├── location
└── tags
6. Duplicate-Safe Data Insertion

The database initialization logic checks whether a place or business already exists before inserting it.

A place is identified using:

name + city

A business is also identified using:

name + city

This prevents duplicate records from being inserted every time the Flask application starts.

7. Tourism Place Retrieval

The backend can retrieve tourism places according to the destination entered by the user.

Example:

User enters:
Kolkata
        ↓
Flask API
        ↓
SQLite Database
        ↓
Kolkata tourism places

The same mechanism works for:

Kolkata
Jaipur
Delhi
8. Local Business Retrieval

The backend can also retrieve businesses according to:

Destination city
Business type

For example:

/api/businesses?city=Kolkata&type=hotel

can return Kolkata hotels.

The system can similarly retrieve:

hotel
restaurant
guide
experience
9. Interest-Based Business Matching

A business recommendation system was added.

The system compares:

User Interests
        ↓
Business Tags
        ↓
Interest Match
        ↓
Business Score

For example, if the user enters:

food, culture

a restaurant having tags:

food, bengali, culture

will receive a higher match score.

10. Business Recommendation Score

Businesses are ranked using an explainable scoring system.

Current scoring:

Business Score =
Interest Match × 70%
+
Rating Score × 30%

In Python:

final_score = (
    interest_score * 0.70 +
    rating_score * 0.30
)

The score is converted into an AI Match Score on the frontend.

Example:

🤖 AI Match Score: 86%
11. Tourist Place Recommendation

Tourist places are also ranked according to user preferences.

The current recommendation score considers:

Interest Match
+
Budget Suitability
+
Rating

Current weighting:

Interest Match → 50%
Budget → 30%
Rating → 20%

This allows the system to prioritize places that better match the user's requirements.

12. Basic Itinerary Generation

The recommendation engine generates a basic day-wise itinerary.

The itinerary considers the estimated duration of each place.

A daily sightseeing limit is currently used:

8 hours/day

When the daily limit is reached, the next place is moved to the following day.

Example:

Day 1
├── Victoria Memorial
├── Indian Museum
└── Park Street

Day 2
├── Science City
└── Eco Park
13. Business Category Filters

The frontend now provides category filters:

All
Hotels
Restaurants
Guides
Experiences

Users can filter the recommended local businesses without requesting the data again from the server.

14. Unknown Destination Handling

The system now handles destinations for which tourism data is not available.

Example:

User enters:
Mumbai

If Mumbai is not currently present in the database, the backend returns:

Tourism data for Mumbai is currently unavailable.

This prevents the system from showing an empty or misleading itinerary.

15. Frontend ↔ Backend Integration

The frontend communicates with the Flask backend using JavaScript fetch() requests.

The flow is:

User
 ↓
Travel Form
 ↓
JavaScript
 ↓
Flask API
 ↓
SQLite Database
 ↓
Recommendation Engine
 ↓
JSON Response
 ↓
Frontend
 ↓
Itinerary + Recommendations
16. Files Modified / Used

The main project files involved in Day 2 are:

TravelBytes-AI/
│
├── app.py
├── database.py
├── recommendation.py
├── travelbytes.db
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── app.js
│
└── docs/
    └── DAY_2.md
17. Role of Each File
app.py

Main Flask application.

Responsible for:

Starting the server
Handling API requests
Receiving user input
Calling database functions
Calling recommendation functions
Returning JSON responses
database.py

Responsible for:

Creating SQLite tables
Adding tourism data
Adding business data
Retrieving places
Retrieving businesses
Preventing duplicate records
recommendation.py

Responsible for:

Calculating interest scores
Calculating budget scores
Calculating rating scores
Ranking tourist places
Ranking local businesses
Generating a basic itinerary
templates/index.html

Responsible for the main TravelBytes AI interface.

It contains:

Destination input
Duration input
Budget input
Interest input
Generate Trip button
Itinerary section
Tourism recommendations
Local business section
Business category filters
static/app.js

Responsible for:

Reading user input
Sending requests to Flask
Receiving JSON responses
Displaying itinerary
Displaying recommendations
Displaying local businesses
Filtering businesses
static/style.css

Responsible for the visual appearance of the application.

travelbytes.db

SQLite database containing:

Tourism places
Local businesses
18. Technologies Used in Day 2
Python

Used for:

Backend logic
Recommendation calculations
Database interaction
Flask

Used for:

REST API routes
Frontend/backend communication
SQLite

Used for:

Storing tourism data
Storing business data
JavaScript

Used for:

API requests
Dynamic frontend updates
Business filtering
HTML/CSS

Used for:

User interface
Displaying recommendations and itinerary
19. Key Concepts Learned

During Day 2, the following concepts were implemented/understood:

SQLite database
Database tables
SQL CREATE TABLE
SQL INSERT
SQL SELECT
SQL filtering
Database connections
Flask API routes
Query parameters
JSON API responses
JavaScript fetch()
Async/Await
Recommendation scoring
Interest matching
Ranking
Client-side filtering
Error handling
Multi-city data handling
20. Day 2 Architecture
                USER
                  │
                  ▼
          ┌─────────────────┐
          │  TravelBytes UI │
          └────────┬────────┘
                   │
                   ▼
             JavaScript
                   │
                   ▼
            Flask Backend
                   │
          ┌────────┴────────┐
          ▼                 ▼
     SQLite Database   Recommendation
          │                Engine
          │                 │
          ▼                 ▼
   Tourism Places      AI Ranking
   Local Businesses         │
          │                 │
          └────────┬────────┘
                   ▼
          Itinerary + Local
        Business Recommendations
                   │
                   ▼
              Frontend UI
21. Day 2 Outcome

At the end of Day 2, TravelBytes AI can:

Retrieve tourism destinations from a database
Support multiple demo cities
Rank tourist places according to user interests
Consider budget suitability
Consider place ratings
Generate a basic day-wise itinerary
Retrieve hotels
Retrieve restaurants
Retrieve local guides
Retrieve local experiences
Match businesses with user interests
Rank businesses using an AI Match Score
Filter businesses by category
Handle unsupported destinations gracefully
Connect the frontend with the Flask backend
Store tourism data using SQLite
22. Supported Demo Cities

Currently available:

Kolkata
Jaipur
Delhi

More cities can be added later without changing the basic architecture.

23. Day 2 Testing

The application should be tested with:

Test 1 — Kolkata
Destination: Kolkata
Duration: 3
Budget: ₹8000
Interests: heritage, food, culture

Expected result:

Kolkata tourist places
AI-ranked recommendations
Day-wise itinerary
Relevant local businesses
Test 2 — Jaipur
Destination: Jaipur
Duration: 3
Budget: ₹8000
Interests: heritage, culture

Expected result:

Jaipur tourist places
AI-ranked recommendations
Jaipur businesses
Category filters
Test 3 — Delhi
Destination: Delhi
Duration: 2
Budget: ₹5000
Interests: heritage, food

Expected result:

Delhi tourist places
AI-ranked recommendations
Delhi businesses
Category filters
Test 4 — Unsupported Destination
Destination: Mumbai

Expected result:

Tourism data for Mumbai is currently unavailable.
24. Current Limitations

The current recommendation engine is intentionally simple and explainable.

It does not yet fully consider:

Real-time weather
Traffic
Road conditions
Live closures
Actual travel time
Distance optimization
Opening/closing hours
Live business availability
Dynamic itinerary re-planning

These features are planned for the upcoming development days.

25. Next Day — Day 3

Day 3 will focus on making the recommendation engine more intelligent.

Planned improvements:

Interest
   +
Budget
   +
Duration
   +
Distance
   +
Travel Time
   +
Rating
   +
Indoor/Outdoor
   +
Time Constraints
        ↓
Improved Recommendation Score
        ↓
Better Itinerary

The goal is to move from a basic recommendation system toward a more intelligent tourism planning engine.

26. Day 2 Completion Status
Tourism Database              ✅
Local Business Database       ✅
Hotels                        ✅
Restaurants                   ✅
Guides                        ✅
Experiences                   ✅
Interest Matching             ✅
AI Match Score                ✅
Business Filters              ✅
Multi-City Support            ✅
Unknown City Handling         ✅
Basic Itinerary               ✅
Frontend Integration          ✅
Backend Integration           ✅

DAY 2 STATUS: COMPLETED ✅
27. Conclusion

Day 2 established the tourism data and local business foundation of TravelBytes AI.

The project has now progressed from a basic Flask application to a database-driven tourism recommendation platform.

The next major step is to improve the intelligence of the recommendation and itinerary engine and prepare it for real-time tourism conditions.


### 📁 Save exactly here

```text
TravelBytes-AI
└── docs
    └── DAY_2.md