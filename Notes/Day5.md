# TravelBytes AI — Day 5 Documentation

## Day 5: Dynamic Itinerary, AI Re-planning & Manual Editing

### Objective

Day 5 ka main objective TravelBytes AI ko ek **dynamic travel planning system** banana tha.

Normal travel planners sirf itinerary generate karte hain:

> Plan → Done

TravelBytes AI ka approach:

> Plan → Monitor → Detect Change → Re-plan → Inform User

Iska matlab hai ki agar trip ke dauran weather ya other conditions change hoti hain, system existing itinerary ko adapt kar sakta hai.

---

# 1. Dynamic Itinerary Generation

TravelBytes AI ab user ke:

- Destination
- Trip duration
- Budget
- Interests
- Available places
- Travel time
- Weather conditions

ke basis par itinerary generate karta hai.

Example:

```text
Destination: Barcelona
Duration: 3 Days
Budget: ₹8000
Interests: Heritage, Culture, Food

System available live places ko recommendation engine se process karta hai aur day-wise itinerary generate karta hai.

2. Daily Time Constraint

Itinerary generation mein daily time limit implement ki gayi.

Default:

Daily available time = 8 hours

System kisi particular day mein activities ko tabhi add karta hai jab total duration daily limit ke andar ho.

Example:

Day 1

Activity 1 → 2 hours
Activity 2 → 2 hours
Activity 3 → 2 hours
Activity 4 → 2 hours

Total → 8 hours

Agar next activity add karne se 8 hours exceed ho jaata hai, system us activity ko us day mein add nahi karta.

3. Duplicate Prevention

Itinerary generation mein duplicate places ko prevent kiya gaya.

System place names ko normalize karke check karta hai ki same place already itinerary mein use hua hai ya nahi.

Example:

Palau Guell
Palau Guell

Agar same place dobara milta hai, duplicate entry skip kar di jaati hai.

4. Weather-Aware Re-planning

TravelBytes AI ka important feature weather-aware itinerary adaptation hai.

System weather API se current weather information obtain karta hai.

Weather information mein:

Temperature
Weather code
Wind speed
Daily weather forecast

jaise data use hota hai.

Example:

Weather:
Mainly clear
Temperature:
24°C

Weather conditions recommendation scoring mein use hoti hain.

5. Indoor / Outdoor Activity Classification

Places ko indoor aur outdoor classification ke according process kiya jaata hai.

Example:

Museum
→ Indoor

Park
→ Outdoor

Ye information weather adaptation ke liye important hai.

Agar weather unsuitable ho jaata hai, system outdoor activities ko identify kar sakta hai aur suitable indoor alternatives search kar sakta hai.

6. AI Weather Re-planning

Re-planning engine ka purpose existing itinerary ko current conditions ke according modify karna hai.

Basic flow:

Existing Itinerary
        ↓
Latest Weather
        ↓
Weather Condition Analysis
        ↓
Identify Affected Activities
        ↓
Remove / Reschedule Outdoor Activities
        ↓
Find Indoor Alternatives
        ↓
Generate Updated Itinerary

Bad weather condition mein outdoor activities ko replace karne ke liye indoor places available places list se search kiye jaate hain.

7. Re-planning API

Dynamic re-planning ke liye endpoint implement kiya gaya:

POST /api/replan

Endpoint existing itinerary ke saath trip information receive karta hai.

Input mein:

destination
duration
budget
interests
itinerary

jaise fields use hote hain.

Example:

{
  "destination": "Barcelona",
  "duration": 3,
  "budget": 8000,
  "interests": "heritage,culture,food",
  "itinerary": [...]
}
8. Live Tourism Data During Re-planning

Re-planning ke waqt system static/demo tourism data par depend nahi karta.

Live places API se available tourism places retrieve kiye jaate hain.

Current implementation OpenStreetMap / Overpass based live tourism data use karti hai.

Retrieved information can include:

Place name
Category
Coordinates
Address
Website
Opening hours
Indoor/outdoor information
Tags
Description
9. Distance and Travel Time

Re-planning process mein places ke coordinates ka use karke distance aur travel time calculate kiya jaata hai.

Routing ke liye OSRM use kiya gaya.

Response mein fields include hote hain:

distance_km
travel_time_minutes

Example:

Distance: 1.69 km
Travel Time: 6 minutes

Ye information recommendation scoring mein bhi use hoti hai.

10. Recommendation Score During Re-planning

Places ko recommendation engine ke through score kiya jaata hai.

Current scoring factors:

Interest Score
Budget Score
Duration Score
Distance Score
Weather Score
Rating Score

Current weights:

Interest  → 25%
Budget    → 15%
Duration  → 10%
Distance  → 10%
Weather   → 25%
Rating    → 15%

Final score:

Final Score =
Interest × 0.25
+ Budget × 0.15
+ Duration × 0.10
+ Distance × 0.10
+ Weather × 0.25
+ Rating × 0.15
11. Recommendation Reason

System sirf numerical score return nahi karta.

Har recommended place ke liye explanation bhi generate ki jaati hai.

Example:

Recommended because it entry cost is currently unavailable,
fits well into your available time,
is suitable for the current weather,
is conveniently located.

Isse user ko samajh aata hai ki particular place recommendation mein kyun include hua.

12. Manual Itinerary Editing

User ko generated itinerary ko manually modify karne ki facility di gayi.

User:

Place remove kar sakta hai
New place add kar sakta hai
Places reorder kar sakta hai
Existing itinerary modify kar sakta hai

Iska purpose AI-generated plan ko user-controlled banana hai.

Final itinerary completely AI-controlled nahi hai.

13. AI + User Control

TravelBytes AI ka planning model:

AI generates plan
        ↓
User reviews plan
        ↓
User edits plan
        ↓
System recalculates
        ↓
Updated itinerary

Isse personalization improve hoti hai.

14. Adaptation Report

Re-planning ke baad system adaptation information maintain karta hai.

Important fields:

weather_affected
weather_adaptation_reason

In fields ka use frontend par user ko batane ke liye kiya jaata hai ki itinerary mein weather ki wajah se kya change hua.

Possible adaptation information:

Removed
Added
Rescheduled
Weather affected

Agar koi change nahi hua ho, system normal plan status bhi show kar sakta hai.

15. /api/replan Testing

Day 5 ke end mein /api/replan endpoint ko actual request ke saath test kiya gaya.

Test input:

Destination: Barcelona
Duration: 3 days
Budget: 8000
Interests:
heritage,culture,food

Testing ke liye existing 3-day itinerary provide ki gayi.

API response:

STATUS: 200
status: success

Response message:

Trip replanned using latest conditions.
16. Successful Test Output

Test response mein successfully receive hua:

budget: 8000
destination: Barcelona
duration: 3
interests: heritage,culture,food

Aur 3-day itinerary bhi return hui:

Day 1
Santa Maria del Mar

Day 2
Palau Guell

Day 3
Palau de la Musica Catalana

System ne live places bhi return kiye.

17. Live Place Data Verification

Test response mein live tourism places successfully receive hue.

Examples:

Basílica de Santa Maria del Mar
Palau Güell
Palau de la Música Catalana
Catedral de la Santa Creu i Santa Eulàlia
Museu de la Xocolata
Museu Picasso
Museu Nacional d'Art de Catalunya

Places ke saath information bhi available thi:

Latitude
Longitude
Distance
Travel Time
Opening Hours
Website
Category
Indoor/Outdoor
Recommendation Score
Recommendation Reason
18. Weather Test Result

Test ke time weather response:

Description: Mainly clear
Temperature: 24°C
Wind Speed: 7.4
Weather Code: 1

Weather conditions suitable hone ki wajah se test itinerary mein kisi activity ko weather ke basis par remove ya replace nahi kiya gaya.

Response mein:

weather_affected: false

aur:

weather_adaptation_reason: null

expected result tha.

19. Day 5 Technical Flow

Complete Day 5 flow:

User Trip Data
      ↓
Existing Itinerary
      ↓
Latest Weather
      ↓
Live Tourism Places
      ↓
Distance + Travel Time
      ↓
Recommendation Engine
      ↓
Weather Analysis
      ↓
Re-planning Engine
      ↓
Updated Itinerary
      ↓
Adaptation Report
      ↓
Frontend
20. Day 5 Files / Components Worked On

Day 5 ke major components:

app.py
recommendation.py
services/weather.py
services/routing.py
services/places_api.py
static/app.js
templates/index.html

Important functionality:

/api/replan
21. Day 5 Completion Status
Feature	Status
Dynamic itinerary	Completed
Daily time limit	Completed
Duplicate prevention	Completed
Weather integration	Completed
Weather-aware scoring	Completed
Indoor/outdoor adaptation	Completed
Live places during re-planning	Completed
Distance calculation	Completed
Travel-time calculation	Completed
Manual itinerary editing	Completed
Re-planning API	Completed
Adaptation information	Completed
/api/replan endpoint testing	Completed
Conclusion

Day 5 mein TravelBytes AI ko ek static itinerary generator se dynamic travel planning system ki taraf move kiya gaya.

The system can now:

Generate
   ↓
Monitor
   ↓
Analyze
   ↓
Re-plan
   ↓
Explain

The /api/replan endpoint was successfully tested with Barcelona trip data and returned HTTP 200 with a successful re-planning response.

The next major development phase is Day 6, which focuses on transforming the working functionality into a professional, polished TravelBytes AI dashboard suitable for the SIH demonstration.

Day 6 Preview

Day 6 mein focus hoga:

Professional dashboard UI
Modern itinerary timeline
Weather cards
AI recommendation cards
Interactive map
Better place information
Hotel section UI improvement
Re-planning alert design
Loading states
Error states
Responsive design
SIH demo-ready frontend