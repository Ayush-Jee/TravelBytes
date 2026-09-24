def calculate_interest_score(place, interests):
    """
    Calculates how well a place matches
    the user's interests.
    """

    if not interests:
        return 0

    user_interests = [
        interest.strip().lower()
        for interest in interests.split(",")
        if interest.strip()
    ]

    place_tags = [
        tag.strip().lower()
        for tag in place.get("tags", "").split(",")
        if tag.strip()
    ]

    if len(user_interests) == 0:
        return 0

    matches = 0

    for interest in user_interests:
        if interest in place_tags:
            matches += 1

    return matches / len(user_interests)

def calculate_rating_score(place):
    """
    Converts place rating into a 0-1 score.

    Live API data me rating missing (None) ho sakti hai.
    Missing rating ko neutral score diya jata hai.
    """

    rating = place.get("rating")

    if rating is None or rating == "":
        return 0.5

    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return 0.5

    return min(
        max(rating / 5, 0),
        1
    )


def calculate_budget_score(place, budget):
    cost = place.get("cost")

    # Live API me cost missing ho sakta hai
    if cost is None or cost == "":
        return 0.5

    try:
        cost = float(cost)
    except (TypeError, ValueError):
        return 0.5

    try:
        budget = float(budget)
    except (TypeError, ValueError):
        return 0.5

    if budget <= 0:
        return 0.5

    if cost <= budget * 0.10:
        return 1.0
    elif cost <= budget * 0.25:
        return 0.8
    elif cost <= budget * 0.50:
        return 0.5
    else:
        return 0.2
    
    
def calculate_duration_score(place, available_hours=8):
    """
    Calculates how well the place duration
    fits within available sightseeing time.
    """

    duration = place.get("duration")

    if duration is None or duration == "":
        return 0.5

    try:
        place_duration = float(duration)
    except (TypeError, ValueError):
        return 0.5

    if place_duration <= 0:
        return 0

    if place_duration <= available_hours * 0.25:
        return 1

    elif place_duration <= available_hours * 0.50:
        return 0.9

    elif place_duration <= available_hours * 0.75:
        return 0.7

    elif place_duration <= available_hours:
        return 0.5

    else:
        return 0.2


def calculate_distance_score(distance_km=None):
    """
    Calculates distance suitability.

    Shorter distances receive higher scores.
    """

    if distance_km is None or distance_km == "":
        return 0.5

    try:
        distance_km = float(distance_km)
    except (TypeError, ValueError):
        return 0.5

    if distance_km <= 3:
        return 1.0

    elif distance_km <= 7:
        return 0.8

    elif distance_km <= 12:
        return 0.6

    elif distance_km <= 20:
        return 0.4

    else:
        return 0.2

def calculate_weather_score(place, weather=None):
    """
    Calculates how suitable a place is for
    the current weather conditions.
    """

    if not weather:
        return 0.5

    # Weather can be a dictionary from the API
    # or a simple string.
    if isinstance(weather, dict):
        weather_text = str(
            weather.get("description", "")
        ).lower()
    else:
        weather_text = str(
            weather
        ).lower()

    indoor = bool(
        place.get("indoor", 0)
    )

    bad_weather_keywords = [
        "rain",
        "drizzle",
        "thunderstorm",
        "snow",
        "fog"
    ]

    bad_weather = any(
        keyword in weather_text
        for keyword in bad_weather_keywords
    )

    if bad_weather:

        if indoor:
            return 1.0

        return 0.05

    # Good / clear weather
    if (
        "clear" in weather_text
        or "sun" in weather_text
        or "mainly clear" in weather_text
    ):

        if indoor:
            return 0.7

        return 1.0

    # Neutral weather
    if indoor:
        return 0.8

    return 0.6

def adapt_places_for_weather(
    places,
    weather=None
):
    """
    Adapts the available places according
    to current weather conditions.

    During bad weather:
    - Indoor places are prioritized.
    - Outdoor places remain available but
      are marked as weather-affected.
    """

    if not places:
        return places

    if not weather:
        return places

    if isinstance(weather, dict):
        weather_text = str(
            weather.get("description", "")
        ).lower()
    else:
        weather_text = str(
            weather
        ).lower()

    bad_weather_keywords = [
        "rain",
        "drizzle",
        "thunderstorm",
        "snow",
        "fog"
    ]

    bad_weather = any(
        keyword in weather_text
        for keyword in bad_weather_keywords
    )

    # No weather disruption
    if not bad_weather:

        for place in places:
            place["weather_affected"] = False
            place["weather_adaptation_reason"] = None

        return places

    indoor_places = []
    outdoor_places = []

    for place in places:

        if bool(place.get("indoor", 0)):
            place["weather_affected"] = False
            place["weather_adaptation_reason"] = (
                "Indoor activity prioritized "
                "because of current weather."
            )

            indoor_places.append(place)

        else:
            place["weather_affected"] = True
            place["weather_adaptation_reason"] = (
                "Outdoor activity may be less suitable "
                "because of current weather."
            )

            outdoor_places.append(place)

    # Indoor places first during bad weather
    return indoor_places + outdoor_places


def calculate_score(
    place,
    interests,
    budget,
    available_hours=8,
    distance_km=None,
    weather=None
):
    """
    Calculates the final intelligent
    recommendation score.

    Factors:
    - Interest
    - Budget
    - Duration
    - Distance
    - Weather
    - Rating
    """

    interest_score = calculate_interest_score(
        place,
        interests
    )

    budget_score = calculate_budget_score(
        place,
        budget
    )

    duration_score = calculate_duration_score(
        place,
        available_hours
    )

    distance_score = calculate_distance_score(
        distance_km
    )

    weather_score = calculate_weather_score(
        place,
        weather
    )

    rating_score = calculate_rating_score(
        place
    )

    final_score = (
        interest_score * 0.25 +
        budget_score * 0.15 +
        duration_score * 0.10 +
        distance_score * 0.10 +
        weather_score * 0.25 +
        rating_score * 0.15
    )

    return round(
        final_score,
        3
    )


def get_recommendation_reason(
    place,
    interests,
    budget,
    available_hours=8,
    distance_km=None,
    weather=None
):
    """
    Generates an explanation for
    why a place was recommended.
    """

    reasons = []

    interest_score = calculate_interest_score(
        place,
        interests
    )

    budget_score = calculate_budget_score(
        place,
        budget
    )

    duration_score = calculate_duration_score(
        place,
        available_hours
    )

    rating_score = calculate_rating_score(
        place
    )

    if interest_score >= 0.5:
        reasons.append(
            "matches your interests"
        )

    cost = place.get("cost")

    if cost is not None and cost != "":
        if budget_score >= 0.8:
            reasons.append(
                "fits your budget"
            )
    else:
        reasons.append(
            "entry cost is currently unavailable"
        )

    if duration_score >= 0.8:
        reasons.append(
            "fits well into your available time"
        )

    if rating_score >= 0.85:
        reasons.append(
            "has a high rating"
        )

    if weather:

        weather_score = calculate_weather_score(
            place,
            weather
        )

        if weather_score >= 0.8:
            reasons.append(
                "is suitable for the current weather"
            )

    if distance_km is not None:

        distance_score = calculate_distance_score(
            distance_km
        )

        if distance_score >= 0.8:
            reasons.append(
                "is conveniently located"
            )

        elif distance_score <= 0.4:
            reasons.append(
                "is relatively far from the destination"
            )

    if not reasons:
        reasons.append(
            "is a balanced option for your trip"
        )

    return (
        "Recommended because it "
        + ", ".join(reasons)
        + "."
    )


def recommend_places(
    places,
    interests,
    budget,
    available_hours=8,
    weather=None
):
    """
    Ranks tourism places according to
    multiple user and trip factors.

    Real OSRM distance is used when
    available.
    """

    recommended_places = []

    for place in places:

        # --------------------------------
        # GET REAL ROUTING DISTANCE
        # --------------------------------

        distance_km = place.get(
            "distance_km"
        )

        # --------------------------------
        # CALCULATE AI SCORE
        # --------------------------------

        score = calculate_score(
            place,
            interests,
            budget,
            available_hours,
            distance_km=distance_km,
            weather=weather
        )

        place["score"] = score

        # --------------------------------
        # GENERATE EXPLANATION
        # --------------------------------

        place["recommendation_reason"] = (
            get_recommendation_reason(
                place,
                interests,
                budget,
                available_hours,
                distance_km=distance_km,
                weather=weather
            )
        )

        recommended_places.append(
            place
        )

    # --------------------------------
    # SORT BY AI SCORE
    # --------------------------------

    recommended_places.sort(
        key=lambda place: place["score"],
        reverse=True
    )

    return recommended_places


def generate_itinerary(
    places,
    duration,
    daily_hours=8
):
    """
    Creates a day-wise itinerary from
    recommended places.

    Places are distributed across the
    requested number of days while
    respecting the daily time limit.
    """

    itinerary = []

    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = 1

    if duration <= 0:
        duration = 1

    try:
        daily_hours = float(daily_hours)
    except (TypeError, ValueError):
        daily_hours = 8.0

    # Create the requested number of days
    for day_number in range(1, duration + 1):
        itinerary.append({
            "day": day_number,
            "places": [],
            "total_hours": 0.0
        })

    if not places:
        return itinerary

    used_names = set()

    for place in places:

        name = str(
            place.get("name", "")
        ).strip().lower()

        # Avoid duplicate places
        if name and name in used_names:
            continue

        duration_value = place.get("duration")

        # Ignore places without a usable duration
        if duration_value is None or duration_value == "":
            continue

        try:
            place_duration = float(duration_value)
        except (TypeError, ValueError):
            continue

        if place_duration <= 0:
            continue

        selected_day = None

        # Find the first day where the place fits
        for day_data in itinerary:

            if (
                day_data["total_hours"]
                + place_duration
                <= daily_hours
            ):
                selected_day = day_data
                break

        # If no day has enough space,
        # do not add the place.
        if selected_day is None:
            continue

        selected_day["places"].append(place)

        selected_day["total_hours"] = round(
            selected_day["total_hours"]
            + place_duration,
            1
        )

        if name:
            used_names.add(name)

    return itinerary

# ========================================
# BUSINESS RECOMMENDATIONS
# ========================================

def calculate_business_interest_score(
    business,
    interests
):
    """
    Calculates how well a business matches
    the user's interests.
    """

    if not interests:
        return 0

    user_interests = [
        interest.strip().lower()
        for interest in interests.split(",")
        if interest.strip()
    ]

    business_tags = [
        tag.strip().lower()
        for tag in business.get(
            "tags",
            ""
        ).split(",")
        if tag.strip()
    ]

    if len(user_interests) == 0:
        return 0

    matches = 0

    for interest in user_interests:

        if interest in business_tags:
            matches += 1

    return matches / len(user_interests)


def calculate_business_rating_score(
    business
):
    """
    Converts business rating into
    a 0-1 score.
    """

    rating = business.get("rating")

    if rating is None or rating == "":
        return 0.5

    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return 0.5

    return min(
        max(rating / 5, 0),
        1
    )

    


def calculate_business_score(
    business,
    interests
):
    """
    Calculates final business
    recommendation score.
    """

    interest_score = (
        calculate_business_interest_score(
            business,
            interests
        )
    )

    rating_score = (
        calculate_business_rating_score(
            business
        )
    )

    final_score = (
        interest_score * 0.70 +
        rating_score * 0.30
    )

    return round(
        final_score,
        3
    )


def get_business_recommendation_reason(
    business,
    interests
):
    """
    Generates a simple explanation for
    why a local business was recommended.
    """

    reasons = []

    interest_score = (
        calculate_business_interest_score(
            business,
            interests
        )
    )

    rating_score = (
        calculate_business_rating_score(
            business
        )
    )

    if interest_score >= 0.5:
        reasons.append(
            "matches your interests"
        )

    if rating_score >= 0.85:
        reasons.append(
            "has a high rating"
        )

    if business.get("price_range"):
        reasons.append(
            f"offers a "
            f"{business['price_range']} "
            f"price range"
        )

    if not reasons:
        reasons.append(
            "is a suitable local option "
            "for your trip"
        )

    return (
        "Recommended because it "
        + ", ".join(reasons)
        + "."
    )


def recommend_businesses(
    businesses,
    interests
):
    """
    Ranks local businesses according
    to user interests and rating.
    """

    recommended_businesses = []

    for business in businesses:

        score = calculate_business_score(
            business,
            interests
        )

        business["score"] = score

        business["recommendation_reason"] = (
            get_business_recommendation_reason(
                business,
                interests
            )
        )

        recommended_businesses.append(
            business
        )

    recommended_businesses.sort(
        key=lambda business: business["score"],
        reverse=True
    )

    return recommended_businesses

# ========================================
# WEATHER BASED ITINERARY REPLANNING
# ========================================

def replan_itinerary_for_weather(
    old_itinerary,
    recommended_places,
    weather
):
    """
    Replan an existing itinerary according to
    bad weather conditions.

    Logic:
    - Outdoor activities are removed/replaced.
    - Indoor alternatives are preferred.
    - Existing indoor places can be moved to fill
      the vacant slots.
    - Duplicate places are avoided.
    - Daily sightseeing time stays within 8 hours.
    """

    DAILY_HOURS_LIMIT = 8.0

    # --------------------------------
    # NO OLD ITINERARY
    # --------------------------------

    if not old_itinerary:
        return generate_itinerary(
            recommended_places,
            1,
            daily_hours=DAILY_HOURS_LIMIT
        )

    # --------------------------------
    # READ WEATHER
    # --------------------------------

    if isinstance(weather, dict):

        weather_text = str(
            weather.get(
                "description",
                ""
            )
        ).lower()

    else:

        weather_text = str(
            weather
        ).lower()

    # --------------------------------
    # BAD WEATHER KEYWORDS
    # --------------------------------

    bad_weather_keywords = [
        "rain",
        "drizzle",
        "thunderstorm",
        "snow",
        "fog"
    ]

    bad_weather = any(
        keyword in weather_text
        for keyword in bad_weather_keywords
    )

    # --------------------------------
    # TEMPORARY RAIN TEST
    # --------------------------------
    # Keep this TRUE only for testing.
    # Remove/comment it after successful test.

    # bad_weather = True
    
    if not bad_weather:

        return old_itinerary

    # --------------------------------
    # IF WEATHER IS GOOD
    # --------------------------------

    if not bad_weather:

        return old_itinerary

    # --------------------------------
    # COLLECT ALL PLACES
    # --------------------------------

    all_places = []

    for place in recommended_places:

        place_copy = dict(place)

        all_places.append(
            place_copy
        )

    # --------------------------------
    # FIND INDOOR PLACES
    # --------------------------------

    indoor_places = [
        place
        for place in all_places
        if bool(
            place.get(
                "indoor",
                0
            )
        )
    ]

    # --------------------------------
    # FIND OUTDOOR PLACES
    # --------------------------------

    outdoor_places = [
        place
        for place in all_places
        if not bool(
            place.get(
                "indoor",
                0
            )
        )
    ]

    # --------------------------------
    # CREATE PLACE LOOKUP
    # --------------------------------

    place_lookup = {}

    for place in all_places:

        name = place.get(
            "name",
            ""
        ).strip().lower()

        if name:

            place_lookup[name] = place

    # --------------------------------
    # BUILD NEW ITINERARY
    # --------------------------------

    adapted_itinerary = []

    used_names = set()

    # --------------------------------
    # FIRST PASS
    # KEEP INDOOR PLACES
    # REMOVE OUTDOOR PLACES
    # --------------------------------

    removed_outdoor_places = []

    for day in old_itinerary:

        new_day_places = []

        for place in day.get(
            "places",
            []
        ):

            name = place.get(
                "name",
                ""
            ).strip().lower()

            is_indoor = bool(
                place.get(
                    "indoor",
                    0
                )
            )

            if is_indoor:

                new_day_places.append(
                    dict(place)
                )

                if name:
                    used_names.add(
                        name
                    )

            else:

                removed_outdoor_places.append(
                    place
                )

        adapted_itinerary.append({
            "day": day.get(
                "day"
            ),
            "places": new_day_places,
            "total_hours": 0
        })

    # --------------------------------
    # AVAILABLE INDOOR ALTERNATIVES
    # --------------------------------

    available_indoor_places = []

    for place in indoor_places:

        name = place.get(
            "name",
            ""
        ).strip().lower()

        if (
            name
            and
            name not in used_names
        ):

            available_indoor_places.append(
                place
            )

    # --------------------------------
    # ADD INDOOR ALTERNATIVES
    # TO DAYS WHERE OUTDOOR PLACES
    # WERE REMOVED
    # --------------------------------

    indoor_index = 0

    for day_data in adapted_itinerary:

        current_hours = 0.0

        # Calculate existing hours
        for place in day_data["places"]:

            current_hours += float(
                place.get(
                    "duration",
                    1
                )
            )

        # --------------------------------
        # ADD INDOOR PLACE IF SPACE EXISTS
        # --------------------------------

        while (
            indoor_index
            <
            len(available_indoor_places)
        ):

            candidate = (
                available_indoor_places[
                    indoor_index
                ]
            )

            candidate_duration = float(
                candidate.get(
                    "duration",
                    1
                )
            )

            if (
                current_hours
                +
                candidate_duration
                <=
                DAILY_HOURS_LIMIT
            ):

                replacement = dict(
                    candidate
                )

                replacement[
                    "weather_affected"
                ] = True

                replacement[
                    "weather_adaptation_reason"
                ] = (
                    "Added as an indoor alternative "
                    "because of bad weather."
                )

                day_data["places"].append(
                    replacement
                )

                current_hours += (
                    candidate_duration
                )

                used_names.add(
                    candidate.get(
                        "name",
                        ""
                    ).strip().lower()
                )

                indoor_index += 1

                break

            else:

                break

        day_data["total_hours"] = round(
            current_hours,
            1
        )

    # --------------------------------
    # IF OUTDOOR PLACES WERE REMOVED
    # BUT NO NEW INDOOR PLACE FIT,
    # TRY ANY UNUSED INDOOR PLACE
    # --------------------------------

    if (
        removed_outdoor_places
        and
        indoor_index
        <
        len(available_indoor_places)
    ):

        for day_data in adapted_itinerary:

            if indoor_index >= len(
                available_indoor_places
            ):
                break

            current_hours = sum(
                float(
                    place.get(
                        "duration",
                        1
                    )
                )
                for place
                in day_data["places"]
            )

            candidate = (
                available_indoor_places[
                    indoor_index
                ]
            )

            candidate_duration = float(
                candidate.get(
                    "duration",
                    1
                )
            )

            if (
                current_hours
                +
                candidate_duration
                <=
                DAILY_HOURS_LIMIT
            ):

                replacement = dict(
                    candidate
                )

                replacement[
                    "weather_affected"
                ] = True

                replacement[
                    "weather_adaptation_reason"
                ] = (
                    "Added as an indoor alternative "
                    "because outdoor activities were "
                    "affected by bad weather."
                )

                day_data["places"].append(
                    replacement
                )

                day_data["total_hours"] = round(
                    current_hours
                    +
                    candidate_duration,
                    1
                )

                indoor_index += 1

    # --------------------------------
    # FINAL CLEANUP
    # --------------------------------

    for day_data in adapted_itinerary:

        total_hours = 0.0

        for place in day_data["places"]:

            total_hours += float(
                place.get(
                    "duration",
                    1
                )
            )

        day_data["total_hours"] = round(
            total_hours,
            1
        )
        
    # --------------------------------
    # SAFETY FALLBACK
    # NEVER RETURN AN EMPTY ITINERARY
    # --------------------------------

    old_place_count = sum(
        len(day.get("places", []))
        for day in old_itinerary
    )

    new_place_count = sum(
        len(day.get("places", []))
        for day in adapted_itinerary
    )

    if old_place_count > 0 and new_place_count == 0:

        return old_itinerary

    return adapted_itinerary