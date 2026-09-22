// ============================================================
// TRAVELBYTES AI - FRONTEND APPLICATION
// Live Tourism Dashboard
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    console.log("TravelBytes AI frontend loaded");

    // --------------------------------------------------------
    // ELEMENTS
    // --------------------------------------------------------

    const form = document.getElementById("travelForm");
    const result = document.getElementById("result");
    const businessResult = document.getElementById("businessResult");

    const destinationInput = document.getElementById("destination");
    const durationInput = document.getElementById("duration");
    const budgetInput = document.getElementById("budget");
    const travellingWithInput = document.getElementById("travellingWith");

    const generateBtn = document.getElementById("generateBtn");

    const dynamicAlert = document.getElementById("dynamicAlert");
    const replanDemoBtn = document.getElementById("replanDemoBtn");

    const businessSection = document.getElementById("businessSection");
    const businessFilters = document.getElementById("businessFilters");

    const interestButtons = document.querySelectorAll(".interest-btn");

    // --------------------------------------------------------
    // STATE
    // --------------------------------------------------------

    let currentItinerary = [];
    let previousItinerary = [];

    let currentDestination = "";
    let currentWeather = null;

    let ecosystemItems = [];
    let currentEcosystemCategory = "all";

    // --------------------------------------------------------
    // INTEREST BUTTONS
    // --------------------------------------------------------

    interestButtons.forEach((button) => {
        button.addEventListener("click", () => {
            button.classList.toggle("active");
            updateInterestsInput();
        });
    });

    function updateInterestsInput() {
        const selected = Array.from(
            document.querySelectorAll(".interest-btn.active")
        ).map((button) => {
            return (
                button.dataset.interest ||
                button.textContent.trim()
            );
        });

        const hiddenInput = document.getElementById("interests");

        if (hiddenInput) {
            hiddenInput.value = selected.join(",");
        }

        return selected;
    }

    // --------------------------------------------------------
    // FORM SUBMIT
    // --------------------------------------------------------

    if (form) {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const destination =
                destinationInput?.value.trim() || "";

            const duration =
                Number(durationInput?.value || 1);

            const budget =
                budgetInput?.value === ""
                    ? null
                    : Number(budgetInput.value);

            const interests = updateInterestsInput();

            const travellingWith =
                travellingWithInput?.value || "";

            if (!destination) {
                showError("Please enter a destination.");
                return;
            }

            currentDestination = destination;

            setGenerateLoading(true);

            hideElement(dynamicAlert);

            if (result) {
                result.innerHTML = `
                    <div class="loading-box">
                        <div class="loading-spinner"></div>
                        <h3>🤖 TravelBytes AI is planning your trip...</h3>
                        <p>
                            Fetching live places, weather, routes
                            and tourism information.
                        </p>
                    </div>
                `;
            }

            try {
                const response = await fetch("/api/plan", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        destination: destination,
                        duration: duration,
                        budget: budget,
                        interests: interests.join(","),
                        travelling_with: travellingWith
                    })
                });

                const data = await safeJson(response);

                if (!response.ok) {
                    throw new Error(
                        data?.error ||
                        data?.message ||
                        `Server error: ${response.status}`
                    );
                }

                if (!data) {
                    throw new Error(
                        "Empty response received from server."
                    );
                }

                processPlanResponse(data);

            } catch (error) {
                console.error("Plan error:", error);

                showError(
                    error.message ||
                    "Something went wrong while creating your trip."
                );

            } finally {
                setGenerateLoading(false);
            }
        });
    }

    // --------------------------------------------------------
    // PROCESS PLAN RESPONSE
    // --------------------------------------------------------

    function processPlanResponse(data) {

        currentItinerary =
            normalizeItinerary(
                data.itinerary ||
                data.plan ||
                []
            );

        previousItinerary =
            deepClone(currentItinerary);

        currentWeather =
            data.weather || null;

        if (result) {
            result.innerHTML = "";
        }

        renderPlanSummary(data);
        renderWeather(data.weather);
        renderRecommendedPlaces(
            data.recommended_places ||
            data.recommendations ||
            data.places ||
            []
        );
        renderItinerary(currentItinerary);

        if (data.weather) {
            updateWeatherStatus(data.weather);
        }

        loadEcosystem(currentDestination, "all");
    }

    // --------------------------------------------------------
    // PLAN SUMMARY
    // --------------------------------------------------------

    function renderPlanSummary(data) {

        if (!result) return;

        const destination =
            data.destination ||
            currentDestination ||
            "Your Destination";

        const duration =
            data.duration ||
            durationInput?.value ||
            "-";

        const budget =
            data.budget ??
            budgetInput?.value ??
            "-";

        const summary = document.createElement("div");

        summary.className = "destination-summary";

        summary.innerHTML = `
            <div class="summary-main">
                <span class="summary-icon">📍</span>

                <div>
                    <h2>${escapeHtml(destination)}</h2>

                    <p>
                        ${escapeHtml(String(duration))}
                        day${Number(duration) === 1 ? "" : "s"}
                        ${budget !== "-" ? ` • ₹${escapeHtml(String(budget))} budget` : ""}
                    </p>
                </div>
            </div>

            <div class="summary-badge">
                <span>●</span>
                AI Plan Ready
            </div>
        `;

        result.appendChild(summary);
    }

    // --------------------------------------------------------
    // WEATHER
    // --------------------------------------------------------

    function renderWeather(weather) {

        if (!result || !weather) {
            return;
        }

        // Backend may return either:
        // 1. weather.current / weather.current_weather
        // 2. Direct flat weather object
        const current =
            weather.current ||
            weather.current_weather ||
            weather;

        const daily =
            weather.daily ||
            null;

        const temperature =
            current.temperature_2m ??
            current.temperature ??
            null;

        const windSpeed =
            current.wind_speed_10m ??
            current.wind_speed ??
            null;

        const weatherCode =
            current.weather_code ??
            current.weathercode ??
            null;

        const description =
            current.description ||
            weatherDescription(weatherCode);

        const weatherCard =
            document.createElement("div");

        weatherCard.className = "weather-card";

        weatherCard.innerHTML = `
        <div class="weather-card-icon">
            ${getWeatherEmoji(description)}
        </div>

        <div class="weather-card-content">

            <span class="weather-label">
                LIVE WEATHER
            </span>

            <strong>
                ${temperature !== null
                ? `${temperature}°C`
                : "Unavailable"
            }
            </strong>

            <p>
                ${escapeHtml(description)}
            </p>

            ${windSpeed !== null
                ? `
                        <small>
                            💨 Wind ${escapeHtml(
                    String(windSpeed)
                )} km/h
                        </small>
                    `
                : ""
            }

        </div>

        ${daily
                ? `
                    <div class="weather-extra">

                        <span>Forecast</span>

                        <strong>
                            ${getRainProbability(daily)}%
                        </strong>

                        <small>
                            rain probability
                        </small>

                    </div>
                `
                : ""
            }

        <div class="weather-live-badge">
            ● LIVE
        </div>
    `;

        result.appendChild(weatherCard);
    }

    function getRainProbability(daily) {

        const values =
            daily.precipitation_probability_max;

        if (
            Array.isArray(values) &&
            values.length
        ) {
            return values[0] ?? 0;
        }

        return 0;
    }

    function weatherDescription(code) {

        if (code === undefined || code === null) {
            return "Live weather";
        }

        const descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Light rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Light snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Rain showers",
            81: "Moderate rain showers",
            82: "Heavy rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Heavy thunderstorm"
        };

        return descriptions[code] || "Live weather";
    }

    function getWeatherEmoji(description) {

        const text =
            String(description).toLowerCase();

        if (
            text.includes("thunder") ||
            text.includes("storm")
        ) {
            return "⛈️";
        }

        if (
            text.includes("rain") ||
            text.includes("drizzle") ||
            text.includes("shower")
        ) {
            return "🌧️";
        }

        if (
            text.includes("fog")
        ) {
            return "🌫️";
        }

        if (
            text.includes("snow")
        ) {
            return "❄️";
        }

        if (
            text.includes("cloud")
        ) {
            return "⛅";
        }

        return "☀️";
    }

    function updateWeatherStatus(weather) {

        const weatherStatus =
            document.getElementById("weatherStatus");

        if (!weatherStatus || !weather) {
            return;
        }

        const current =
            weather.current ||
            weather.current_weather ||
            weather;

        const code =
            current.weather_code ??
            current.weathercode ??
            null;

        const description =
            current.description ||
            weatherDescription(code);

        weatherStatus.textContent =
            `☁️ ${description}`;
    }

    // --------------------------------------------------------
    // RECOMMENDED PLACES
    // --------------------------------------------------------

    function renderRecommendedPlaces(places) {

        if (!result || !Array.isArray(places)) {
            return;
        }

        if (!places.length) {
            return;
        }

        const section =
            document.createElement("section");

        section.className =
            "recommended-section";

        const cards = places
            .slice(0, 8)
            .map((place) => {

                const rating =
                    place.rating ??
                    null;

                const cost =
                    place.cost ??
                    null;

                const distance =
                    place.distance_km ??
                    null;

                const reason =
                    place.recommendation_reason ||
                    place.reason ||
                    "";

                return `
                    <article class="place-card">

                        <div class="place-card-top">

                            <div class="place-icon">
                                ${getCategoryEmoji(place.category)}
                            </div>

                            ${rating !== null
                        ? `
                                    <span class="place-rating">
                                        ⭐ ${escapeHtml(String(rating))}
                                    </span>
                                    `
                        : ""
                    }

                        </div>

                        <h3>
                            ${escapeHtml(
                        place.name ||
                        "Tourist Attraction"
                    )}
                        </h3>

                        <p class="place-category">
                            ${escapeHtml(
                        formatCategory(
                            place.category ||
                            "Tourism"
                        )
                    )}
                        </p>

                        <div class="place-meta">

                            ${distance !== null
                        ? `
                                    <span>
                                        📍
                                        ${Number(distance).toFixed(1)}
                                        km
                                    </span>
                                    `
                        : ""
                    }

                            ${cost !== null
                        ? `
                                    <span>
                                        💰 ₹${escapeHtml(String(cost))}
                                    </span>
                                    `
                        : ""
                    }

                            ${place.duration
                        ? `
                                    <span>
                                        ⏱️
                                        ${escapeHtml(
                            String(place.duration)
                        )}h
                                    </span>
                                    `
                        : ""
                    }

                        </div>

                        ${reason
                        ? `
                                <div class="recommendation-reason">
                                    🤖 ${escapeHtml(reason)}
                                </div>
                                `
                        : ""
                    }

                    </article>
                `;
            })
            .join("");

        section.innerHTML = `
            <div class="section-heading">
                <div>
                    <span class="section-kicker">
                        AI RECOMMENDATIONS
                    </span>

                    <h2>
                        Places selected for you
                    </h2>
                </div>
            </div>

            <div class="places-grid">
                ${cards}
            </div>
        `;

        result.appendChild(section);
    }

    function getCategoryEmoji(category) {

        const text =
            String(category || "")
                .toLowerCase();

        if (
            text.includes("museum")
        ) {
            return "🏛️";
        }

        if (
            text.includes("heritage") ||
            text.includes("historic") ||
            text.includes("monument") ||
            text.includes("castle") ||
            text.includes("palace") ||
            text.includes("fort")
        ) {
            return "🏰";
        }

        if (
            text.includes("park") ||
            text.includes("nature")
        ) {
            return "🌳";
        }

        if (
            text.includes("viewpoint")
        ) {
            return "🌄";
        }

        if (
            text.includes("zoo") ||
            text.includes("aquarium")
        ) {
            return "🦁";
        }

        return "📍";
    }

    // --------------------------------------------------------
    // ITINERARY
    // --------------------------------------------------------

    function renderItinerary(itinerary) {

        if (!result) return;

        const section =
            document.createElement("section");

        section.className =
            "itinerary-section";

        section.innerHTML = `
            <div class="section-heading itinerary-heading">

                <div>
                    <span class="section-kicker">
                        AI DYNAMIC ITINERARY
                    </span>

                    <h2>
                        Your adaptive travel plan
                    </h2>

                    <p>
                        Edit, remove, add or reorder activities.
                        TravelBytes AI recalculates the plan.
                    </p>
                </div>

                <button
                    type="button"
                    class="secondary-action"
                    id="addItineraryBtn"
                >
                    + Add Activity
                </button>

            </div>

            <div id="editableItinerary"></div>
        `;

        result.appendChild(section);

        const container =
            section.querySelector(
                "#editableItinerary"
            );

        renderEditableItinerary(
            container,
            itinerary
        );

        const addButton =
            section.querySelector(
                "#addItineraryBtn"
            );

        if (addButton) {
            addButton.addEventListener(
                "click",
                () => addItineraryItem()
            );
        }
    }

    function renderEditableItinerary(
        container,
        itinerary
    ) {

        if (!container) return;

        if (!itinerary.length) {
            container.innerHTML = `
                <div class="empty-itinerary">
                    <div>🗺️</div>
                    <h3>No itinerary generated</h3>
                    <p>
                        Try another destination or duration.
                    </p>
                </div>
            `;
            return;
        }

        container.innerHTML =
            itinerary.map(
                (dayData, dayIndex) => {

                    const places =
                        Array.isArray(dayData.places)
                            ? dayData.places
                            : [];

                    return `
                        <div
                            class="day-card"
                            data-day-index="${dayIndex}"
                        >

                            <div class="day-card-header">

                                <div>
                                    <span class="day-number">
                                        DAY ${dayData.day || dayIndex + 1}
                                    </span>

                                    <h3>
                                        ${places.length
                            ? `${places.length} activities`
                            : "Flexible day"}
                                    </h3>
                                </div>

                                <div class="day-hours">
                                    ${Number(
                                dayData.total_hours || 0
                            ).toFixed(1)}h / 8h
                                </div>

                            </div>

                            <div class="day-activities">

                                ${places.length
                            ? places.map(
                                (
                                    place,
                                    placeIndex
                                ) =>
                                    renderItineraryPlace(
                                        place,
                                        dayIndex,
                                        placeIndex
                                    )
                            ).join("")
                            : `
                                        <div class="empty-day">
                                            No activities yet.
                                        </div>
                                        `
                        }

                            </div>

                        </div>
                    `;
                }
            ).join("");

        attachItineraryEvents(container);
    }

    function renderItineraryPlace(
        place,
        dayIndex,
        placeIndex
    ) {

        const name =
            place.name ||
            "Activity";

        const duration =
            place.duration ??
            0;

        const weatherAffected =
            place.weather_affected;

        return `
            <div
                class="activity-card ${weatherAffected
                ? "weather-affected"
                : ""
            }"
                data-day-index="${dayIndex}"
                data-place-index="${placeIndex}"
            >

                <div class="activity-icon">
                    ${getCategoryEmoji(place.category)}
                </div>

                <div class="activity-info">

                    <div class="activity-title-row">

                        <h4>
                            ${escapeHtml(name)}
                        </h4>

                        ${weatherAffected
                ? `
                                <span class="weather-change-badge">
                                    🌧️ Changed
                                </span>
                                `
                : ""
            }

                    </div>

                    <div class="activity-meta">

                        <span>
                            ⏱️
                            ${escapeHtml(
                String(duration)
            )}h
                        </span>

                        ${place.distance_km !== undefined
                ? `
                                <span>
                                    📍
                                    ${Number(
                    place.distance_km
                ).toFixed(1)} km
                                </span>
                                `
                : ""
            }

                    </div>

                    ${place.recommendation_reason
                ? `
                            <p class="activity-reason">
                                🤖
                                ${escapeHtml(
                    place.recommendation_reason
                )}
                            </p>
                            `
                : ""
            }

                    ${place.weather_adaptation_reason
                ? `
                            <p class="adaptation-reason">
                                🌦️
                                ${escapeHtml(
                    place.weather_adaptation_reason
                )}
                            </p>
                            `
                : ""
            }

                </div>

                <div class="activity-actions">

                    <button
                        type="button"
                        class="icon-btn move-up"
                        title="Move up"
                    >
                        ↑
                    </button>

                    <button
                        type="button"
                        class="icon-btn move-down"
                        title="Move down"
                    >
                        ↓
                    </button>

                    <button
                        type="button"
                        class="icon-btn edit-item"
                        title="Edit"
                    >
                        ✏️
                    </button>

                    <button
                        type="button"
                        class="icon-btn delete-item danger"
                        title="Remove"
                    >
                        🗑️
                    </button>

                </div>

            </div>
        `;
    }

    function attachItineraryEvents(container) {

        container
            .querySelectorAll(".delete-item")
            .forEach((button) => {

                button.addEventListener(
                    "click",
                    async () => {

                        const card =
                            button.closest(
                                ".activity-card"
                            );

                        if (!card) return;

                        const dayIndex =
                            Number(
                                card.dataset.dayIndex
                            );

                        const placeIndex =
                            Number(
                                card.dataset.placeIndex
                            );

                        await removeItineraryItem(
                            dayIndex,
                            placeIndex
                        );
                    }
                );
            });

        container
            .querySelectorAll(".edit-item")
            .forEach((button) => {

                button.addEventListener(
                    "click",
                    () => {

                        const card =
                            button.closest(
                                ".activity-card"
                            );

                        if (!card) return;

                        editItineraryItem(
                            Number(
                                card.dataset.dayIndex
                            ),
                            Number(
                                card.dataset.placeIndex
                            )
                        );
                    }
                );
            });

        container
            .querySelectorAll(".move-up")
            .forEach((button) => {

                button.addEventListener(
                    "click",
                    () => {

                        const card =
                            button.closest(
                                ".activity-card"
                            );

                        moveItineraryItem(
                            Number(
                                card.dataset.dayIndex
                            ),
                            Number(
                                card.dataset.placeIndex
                            ),
                            "up"
                        );
                    }
                );
            });

        container
            .querySelectorAll(".move-down")
            .forEach((button) => {

                button.addEventListener(
                    "click",
                    () => {

                        const card =
                            button.closest(
                                ".activity-card"
                            );

                        moveItineraryItem(
                            Number(
                                card.dataset.dayIndex
                            ),
                            Number(
                                card.dataset.placeIndex
                            ),
                            "down"
                        );
                    }
                );
            });
    }

    // --------------------------------------------------------
    // DELETE ITINERARY ITEM
    // --------------------------------------------------------

    async function removeItineraryItem(
        dayIndex,
        placeIndex
    ) {

        const day =
            currentItinerary[dayIndex];

        if (!day || !day.places) return;

        const removed =
            day.places[placeIndex];

        if (!removed) return;

        previousItinerary =
            deepClone(currentItinerary);

        day.places.splice(placeIndex, 1);

        recalculateDayHours(day);

        refreshItineraryDisplay();

        showMiniNotice(
            `Removed "${removed.name || "activity"}".`
        );

        await persistItineraryChange(
            "delete",
            removed
        );
    }

    // --------------------------------------------------------
    // EDIT ITINERARY ITEM
    // --------------------------------------------------------

    function editItineraryItem(
        dayIndex,
        placeIndex
    ) {

        const day =
            currentItinerary[dayIndex];

        const place =
            day?.places?.[placeIndex];

        if (!place) return;

        const newName =
            prompt(
                "Activity name:",
                place.name || ""
            );

        if (
            newName === null ||
            !newName.trim()
        ) {
            return;
        }

        const newDuration =
            prompt(
                "Duration in hours:",
                place.duration ?? 2
            );

        if (newDuration === null) {
            return;
        }

        const parsedDuration =
            Number(newDuration);

        if (
            !Number.isFinite(parsedDuration) ||
            parsedDuration <= 0
        ) {
            alert(
                "Please enter a valid duration."
            );
            return;
        }

        previousItinerary =
            deepClone(currentItinerary);

        place.name =
            newName.trim();

        place.duration =
            parsedDuration;

        recalculateDayHours(day);

        refreshItineraryDisplay();

        persistItineraryChange(
            "update",
            place
        );
    }

    // --------------------------------------------------------
    // ADD ITINERARY ITEM
    // --------------------------------------------------------

    function addItineraryItem() {

        if (!currentItinerary.length) {
            currentItinerary.push({
                day: 1,
                places: [],
                total_hours: 0
            });
        }

        const name =
            prompt(
                "New activity name:"
            );

        if (
            name === null ||
            !name.trim()
        ) {
            return;
        }

        const duration =
            Number(
                prompt(
                    "Duration in hours:",
                    "2"
                )
            );

        if (
            !Number.isFinite(duration) ||
            duration <= 0
        ) {
            alert(
                "Please enter a valid duration."
            );
            return;
        }

        let selectedDay =
            currentItinerary.find(
                (day) =>
                    Number(day.total_hours || 0) +
                    duration <= 8
            );

        if (!selectedDay) {
            selectedDay =
                currentItinerary[
                currentItinerary.length - 1
                ];

            if (
                Number(selectedDay.total_hours || 0) +
                duration >
                8
            ) {
                currentItinerary.push({
                    day:
                        currentItinerary.length + 1,
                    places: [],
                    total_hours: 0
                });

                selectedDay =
                    currentItinerary[
                    currentItinerary.length - 1
                    ];
            }
        }

        previousItinerary =
            deepClone(currentItinerary);

        selectedDay.places.push({
            name: name.trim(),
            duration: duration,
            category: "custom",
            user_added: true
        });

        recalculateDayHours(
            selectedDay
        );

        refreshItineraryDisplay();

        persistItineraryChange(
            "add",
            selectedDay.places[
            selectedDay.places.length - 1
            ]
        );
    }

    // --------------------------------------------------------
    // MOVE ITEM
    // --------------------------------------------------------

    function moveItineraryItem(
        dayIndex,
        placeIndex,
        direction
    ) {

        const day =
            currentItinerary[dayIndex];

        if (!day?.places) return;

        const newIndex =
            direction === "up"
                ? placeIndex - 1
                : placeIndex + 1;

        if (
            newIndex < 0 ||
            newIndex >= day.places.length
        ) {
            return;
        }

        previousItinerary =
            deepClone(currentItinerary);

        const temp =
            day.places[placeIndex];

        day.places[placeIndex] =
            day.places[newIndex];

        day.places[newIndex] =
            temp;

        refreshItineraryDisplay();

        persistItineraryChange(
            "reorder",
            temp
        );
    }

    function recalculateDayHours(day) {

        day.total_hours =
            roundNumber(
                (day.places || [])
                    .reduce(
                        (total, place) =>
                            total +
                            Number(
                                place.duration || 0
                            ),
                        0
                    ),
                1
            );
    }

    function refreshItineraryDisplay() {

        const container =
            document.getElementById(
                "editableItinerary"
            );

        if (!container) return;

        renderEditableItinerary(
            container,
            currentItinerary
        );
    }

    // --------------------------------------------------------
    // PERSIST ITINERARY
    // --------------------------------------------------------

    async function persistItineraryChange(
        action,
        item
    ) {

        try {

            let endpoint =
                "/api/itinerary/item";

            let method = "PUT";

            let body = {
                action: action,
                item: item,
                itinerary: currentItinerary
            };

            if (action === "delete") {
                endpoint =
                    "/api/itinerary/item";
                method = "DELETE";
            }

            const response =
                await fetch(
                    endpoint,
                    {
                        method: method,
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body:
                            JSON.stringify(body)
                    }
                );

            if (!response.ok) {
                console.warn(
                    "Itinerary persistence failed:",
                    response.status
                );
            }

        } catch (error) {

            console.warn(
                "Itinerary persistence error:",
                error
            );
        }
    }

    // --------------------------------------------------------
    // REPLAN
    // --------------------------------------------------------

    if (replanDemoBtn) {

        replanDemoBtn.addEventListener(
            "click",
            async () => {

                await runReplan();
            }
        );
    }

    async function runReplan() {

        if (!currentDestination) {

            showMiniNotice(
                "Generate a trip first."
            );

            return;
        }

        if (!currentItinerary.length) {

            showMiniNotice(
                "There is no itinerary to re-plan."
            );

            return;
        }

        const button =
            replanDemoBtn;

        if (button) {
            button.disabled = true;
            button.textContent =
                "🤖 AI Replanning...";
        }

        previousItinerary =
            deepClone(currentItinerary);

        try {

            const response =
                await fetch(
                    "/api/replan",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body:
                            JSON.stringify({
                                destination:
                                    currentDestination,

                                itinerary:
                                    currentItinerary,

                                duration:
                                    Number(
                                        durationInput?.value ||
                                        currentItinerary.length ||
                                        1
                                    ),

                                budget:
                                    budgetInput?.value
                                        ? Number(
                                            budgetInput.value
                                        )
                                        : null,

                                interests:
                                    updateInterestsInput().join(",")
                            })
                    }
                );

            const data =
                await safeJson(response);

            if (!response.ok) {

                throw new Error(
                    data?.error ||
                    data?.message ||
                    `Replan failed: ${response.status}`
                );
            }

            const newItinerary =
                normalizeItinerary(
                    data.itinerary ||
                    data.updated_itinerary ||
                    data.replanned_itinerary ||
                    []
                );

            if (newItinerary.length) {

                currentItinerary =
                    newItinerary;

                refreshItineraryDisplay();
            }

            showAdaptationReport(
                previousItinerary,
                currentItinerary,
                data
            );

        } catch (error) {

            console.error(
                "Replan error:",
                error
            );

            showError(
                error.message ||
                "Unable to replan itinerary."
            );

        } finally {

            if (button) {
                button.disabled = false;
                button.textContent =
                    "⚡ Simulate Real-Time Change";
            }
        }
    }

    // --------------------------------------------------------
    // ADAPTATION REPORT
    // --------------------------------------------------------

    function showAdaptationReport(
        oldItinerary,
        newItinerary,
        data
    ) {

        const removed =
            getDifference(
                oldItinerary,
                newItinerary
            );

        const added =
            getDifference(
                newItinerary,
                oldItinerary
            );

        const weatherText =
            data?.weather_message ||
            data?.adaptation_reason ||
            "Real-world conditions were checked.";

        if (
            removed.length === 0 &&
            added.length === 0
        ) {

            showDynamicAlert(
                "Travel Plan Checked",
                weatherText,
                "success"
            );

            return;
        }

        const removedText =
            removed
                .slice(0, 4)
                .map(
                    (item) =>
                        `<li>❌ ${escapeHtml(item)}</li>`
                )
                .join("");

        const addedText =
            added
                .slice(0, 4)
                .map(
                    (item) =>
                        `<li>✅ ${escapeHtml(item)}</li>`
                )
                .join("");

        showDynamicAlert(
            "🤖 AI Adaptation Detected",
            `
                <p>
                    ${escapeHtml(weatherText)}
                </p>

                ${removed.length
                ? `
                        <strong>Removed / Rescheduled</strong>
                        <ul>
                            ${removedText}
                        </ul>
                        `
                : ""
            }

                ${added.length
                ? `
                        <strong>Added Alternatives</strong>
                        <ul>
                            ${addedText}
                        </ul>
                        `
                : ""
            }
            `,
            "warning",
            true
        );
    }

    function getDifference(
        itineraryA,
        itineraryB
    ) {

        const namesA =
            flattenItinerary(itineraryA)
                .map(normalizeName);

        const namesB =
            new Set(
                flattenItinerary(itineraryB)
                    .map(normalizeName)
            );

        return flattenItinerary(itineraryA)
            .filter(
                (item) =>
                    !namesB.has(
                        normalizeName(item)
                    )
            )
            .map(
                (item) =>
                    item.name ||
                    "Activity"
            );
    }

    // --------------------------------------------------------
    // LIVE ECOSYSTEM
    // --------------------------------------------------------

    async function loadEcosystem(
        city,
        category = "all"
    ) {

        if (!city) return;

        currentEcosystemCategory =
            category;

        showEcosystemLoading();

        try {

            if (category === "hotels") {

                await loadHotels(city);
                return;
            }

            const response =
                await fetch(
                    `/api/ecosystem?city=${encodeURIComponent(city)}&category=${encodeURIComponent(category)}`
                );

            const data =
                await safeJson(response);

            if (!response.ok) {

                throw new Error(
                    data?.error ||
                    data?.message ||
                    `Ecosystem error: ${response.status}`
                );
            }

            ecosystemItems =
                Array.isArray(data.items)
                    ? data.items
                    : [];

            renderEcosystem(
                ecosystemItems,
                category
            );

        } catch (error) {

            console.error(
                "Ecosystem error:",
                error
            );

            renderEcosystemError(
                error.message
            );
        }
    }

    // --------------------------------------------------------
    // HOTELS
    // --------------------------------------------------------

    async function loadHotels(city) {

        showEcosystemLoading(
            "🏨 Loading live hotel availability..."
        );

        try {

            // First resolve Hotelbeds destination.
            const destinationResponse =
                await fetch(
                    `/api/hotel-destination?destination=${encodeURIComponent(city)}`
                );

            const destinationData =
                await safeJson(
                    destinationResponse
                );

            if (!destinationResponse.ok) {

                throw new Error(
                    destinationData?.error ||
                    destinationData?.message ||
                    "Hotel destination lookup failed."
                );
            }

            const destinationCode =
                destinationData?.code ||
                destinationData?.destination_code ||
                destinationData?.destination?.code;

            if (!destinationCode) {

                throw new Error(
                    "No Hotelbeds destination code found."
                );
            }

            // Then request availability.
            const response =
                await fetch(
                    "/api/hotels",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body:
                            JSON.stringify({
                                destination:
                                    city,

                                destination_code:
                                    destinationCode,

                                check_in:
                                    getDefaultCheckIn(),

                                check_out:
                                    getDefaultCheckOut(),

                                adults: 2,

                                rooms: 1
                            })
                    }
                );

            const data =
                await safeJson(response);

            if (!response.ok) {

                throw new Error(
                    data?.error ||
                    data?.message ||
                    `Hotel API error: ${response.status}`
                );
            }

            const hotels =
                Array.isArray(data.hotels)
                    ? data.hotels
                    : Array.isArray(data.items)
                        ? data.items
                        : [];

            renderEcosystem(
                hotels,
                "hotels"
            );

        } catch (error) {

            console.error(
                "Hotel loading error:",
                error
            );

            renderEcosystemError(
                error.message ||
                "Hotel availability is temporarily unavailable."
            );
        }
    }

    function getDefaultCheckIn() {

        const date =
            new Date();

        date.setDate(
            date.getDate() + 1
        );

        return formatDate(
            date
        );
    }

    function getDefaultCheckOut() {

        const date =
            new Date();

        date.setDate(
            date.getDate() + 2
        );

        return formatDate(
            date
        );
    }

    function formatDate(date) {

        return date
            .toISOString()
            .split("T")[0];
    }

    // --------------------------------------------------------
    // ECOSYSTEM FILTERS
    // --------------------------------------------------------

    if (businessFilters) {

        businessFilters.addEventListener(
            "click",
            (event) => {

                const button =
                    event.target.closest(
                        "[data-ecosystem-category]"
                    );

                if (!button) {
                    return;
                }

                // Remove active state from all
                // ecosystem buttons.
                businessFilters
                    .querySelectorAll(
                        "[data-ecosystem-category]"
                    )
                    .forEach((item) => {
                        item.classList.remove(
                            "active"
                        );
                    });

                // Activate clicked button.
                button.classList.add(
                    "active"
                );

                const category =
                    button.dataset
                        .ecosystemCategory ||
                    "all";

                console.log(
                    "Ecosystem category:",
                    category
                );

                if (!currentDestination) {

                    showMiniNotice(
                        "Generate a trip first."
                    );

                    return;
                }

                loadEcosystem(
                    currentDestination,
                    category
                );
            }
        );
    }


    // --------------------------------------------------------
    // BACKWARD COMPATIBILITY
    // --------------------------------------------------------

    window.filterBusinesses =
        function (type) {

            loadEcosystem(
                currentDestination,
                type || "all"
            );
        };


    // --------------------------------------------------------
    // BACKWARD COMPATIBILITY
    // --------------------------------------------------------

    window.filterBusinesses =
        function (type) {

            loadEcosystem(
                currentDestination,
                type || "all"
            );

        };

    // --------------------------------------------------------
    // RENDER ECOSYSTEM
    // --------------------------------------------------------

    function renderEcosystem(
        items,
        category
    ) {

        if (!businessResult) return;

        if (
            businessSection
        ) {
            showElement(
                businessSection
            );
        }

        if (!items.length) {

            businessResult.innerHTML = `
                <div class="ecosystem-empty">

                    <div class="empty-icon">
                        🌍
                    </div>

                    <h3>
                        No live ${escapeHtml(
                category === "all"
                    ? "tourism services"
                    : formatCategory(category)
            )} found
                    </h3>

                    <p>
                        Try another destination or
                        explore another category.
                    </p>

                </div>
            `;

            return;
        }

        businessResult.innerHTML =
            items
                .slice(0, 40)
                .map(
                    (item) =>
                        renderEcosystemCard(
                            item,
                            category
                        )
                )
                .join("");
    }

    function renderEcosystemCard(
        item,
        category
    ) {

        const itemCategory =
            item.type ||
            category ||
            "tourism";

        const rating =
            item.rating ??
            item.stars ??
            null;

        const distance =
            item.distance_km ??
            null;

        const price =
            item.min_rate ??
            item.price_range ??
            item.price ??
            null;

        const source =
            item.data_source ||
            item.source ||
            (
                category === "hotels"
                    ? "Hotelbeds"
                    : "OpenStreetMap"
            );

        return `
            <article class="business-card ecosystem-card">

                <div class="business-card-top">

                    <div class="business-icon">
                        ${getEcosystemEmoji(
            itemCategory
        )}
                    </div>

                    <span class="live-data-badge">
                        ● LIVE
                    </span>

                </div>

                <h3>
                    ${escapeHtml(
            item.name ||
            "Local Tourism Provider"
        )}
                </h3>

                <p class="business-type">
                    ${escapeHtml(
            formatCategory(
                item.subcategory ||
                item.type ||
                item.category ||
                category
            )
        )}
                </p>

                ${item.location
                ? `
                        <p class="business-location">
                            📍
                            ${escapeHtml(
                    item.location
                )}
                        </p>
                        `
                : ""
            }

                <div class="business-meta">

                    ${rating !== null
                ? `
                            <span>
                                ⭐
                                ${escapeHtml(
                    String(rating)
                )}
                            </span>
                            `
                : ""
            }

                    ${distance !== null
                ? `
                            <span>
                                📍
                                ${Number(
                    distance
                ).toFixed(1)} km
                            </span>
                            `
                : ""
            }

                    ${price !== null
                ? `
                            <span>
                                💰
                                ${escapeHtml(
                    String(price)
                )}
                            </span>
                            `
                : ""
            }

                </div>

                ${item.opening_hours
                ? `
                        <div class="business-hours">
                            🕐
                            ${escapeHtml(
                    item.opening_hours
                )}
                        </div>
                        `
                : ""
            }

                ${item.website
                ? `
                        <a
                            class="business-link"
                            href="${safeUrl(
                    item.website
                )}"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Visit website →
                        </a>
                        `
                : ""
            }

                <div class="data-source">
                    Data: ${escapeHtml(
                String(source)
            )}
                </div>

            </article>
        `;
    }

    function getEcosystemEmoji(
        category
    ) {

        const text =
            String(category || "")
                .toLowerCase();

        if (
            text.includes("hotel") ||
            text.includes("accommodation")
        ) {
            return "🏨";
        }

        if (
            text.includes("restaurant") ||
            text.includes("food") ||
            text.includes("cafe") ||
            text.includes("fast")
        ) {
            return "🍽️";
        }

        if (
            text.includes("guide")
        ) {
            return "🧭";
        }

        if (
            text.includes("museum")
        ) {
            return "🏛️";
        }

        if (
            text.includes("park")
        ) {
            return "🌳";
        }

        if (
            text.includes("experience") ||
            text.includes("attraction")
        ) {
            return "🎟️";
        }

        return "🌍";
    }

    function showEcosystemLoading(
        message = "🌍 Loading live tourism data..."
    ) {

        if (!businessResult) return;

        if (businessSection) {
            showElement(
                businessSection
            );
        }

        businessResult.innerHTML = `
            <div class="loading-box ecosystem-loading">

                <div class="loading-spinner"></div>

                <h3>
                    ${escapeHtml(message)}
                </h3>

                <p>
                    Connecting to live tourism services...
                </p>

            </div>
        `;
    }

    function renderEcosystemError(
        message
    ) {

        if (!businessResult) return;

        businessResult.innerHTML = `
            <div class="ecosystem-error">

                <div class="empty-icon">
                    ⚠️
                </div>

                <h3>
                    Live data temporarily unavailable
                </h3>

                <p>
                    ${escapeHtml(
            message ||
            "Please try again."
        )}
                </p>

            </div>
        `;
    }

    // --------------------------------------------------------
    // DYNAMIC ALERT
    // --------------------------------------------------------

    function showDynamicAlert(
        title,
        message,
        type = "warning",
        html = false
    ) {

        if (!dynamicAlert) return;

        dynamicAlert.className =
            `dynamic-alert ${type}`;

        dynamicAlert.innerHTML = `
            <div class="alert-icon">
                ${type === "success"
                ? "✓"
                : "⚡"
            }
            </div>

            <div class="alert-content">

                <strong>
                    ${escapeHtml(title)}
                </strong>

                <div>
                    ${html
                ? message
                : escapeHtml(message)
            }
                </div>

            </div>

            <button
                type="button"
                class="alert-close"
                aria-label="Close"
            >
                ×
            </button>
        `;

        showElement(
            dynamicAlert
        );

        const close =
            dynamicAlert.querySelector(
                ".alert-close"
            );

        if (close) {
            close.addEventListener(
                "click",
                () => hideElement(
                    dynamicAlert
                )
            );
        }
    }

    // --------------------------------------------------------
    // ERROR
    // --------------------------------------------------------

    function showError(message) {

        if (!result) return;

        result.innerHTML = `
            <div class="error-box">

                <div class="error-icon">
                    ⚠️
                </div>

                <h3>
                    Something went wrong
                </h3>

                <p>
                    ${escapeHtml(
            message ||
            "Please try again."
        )}
                </p>

                <button
                    type="button"
                    class="secondary-action"
                    onclick="location.reload()"
                >
                    Try Again
                </button>

            </div>
        `;
    }

    // --------------------------------------------------------
    // LOADING BUTTON
    // --------------------------------------------------------

    function setGenerateLoading(
        loading
    ) {

        if (!generateBtn) return;

        if (loading) {

            generateBtn.disabled =
                true;

            generateBtn.dataset.originalText =
                generateBtn.innerHTML;

            generateBtn.innerHTML =
                `
                <span class="button-spinner"></span>
                AI is Planning...
                `;

        } else {

            generateBtn.disabled =
                false;

            generateBtn.innerHTML =
                generateBtn.dataset.originalText ||
                "Generate My Dynamic Plan";
        }
    }

    // --------------------------------------------------------
    // UTILITY FUNCTIONS
    // --------------------------------------------------------

    async function safeJson(response) {

        const text =
            await response.text();

        if (!text) {
            return {};
        }

        try {
            return JSON.parse(text);
        } catch {
            return {
                error: text
            };
        }
    }

    function normalizeItinerary(
        itinerary
    ) {

        if (!Array.isArray(itinerary)) {
            return [];
        }

        return itinerary.map(
            (day, index) => {

                const normalized = {
                    day:
                        day.day ||
                        index + 1,

                    places:
                        Array.isArray(day.places)
                            ? day.places
                            : [],

                    total_hours:
                        Number(
                            day.total_hours || 0
                        )
                };

                recalculateDayHours(
                    normalized
                );

                return normalized;
            }
        );
    }

    function flattenItinerary(
        itinerary
    ) {

        if (!Array.isArray(itinerary)) {
            return [];
        }

        return itinerary.flatMap(
            (day) =>
                Array.isArray(day.places)
                    ? day.places
                    : []
        );
    }

    function normalizeName(item) {

        return String(
            item?.name ||
            item ||
            ""
        )
            .trim()
            .toLowerCase();
    }

    function deepClone(value) {

        try {
            return JSON.parse(
                JSON.stringify(value)
            );
        } catch {
            return [];
        }
    }

    function roundNumber(
        value,
        decimals = 1
    ) {

        const factor =
            Math.pow(
                10,
                decimals
            );

        return (
            Math.round(
                Number(value) * factor
            ) / factor
        );
    }

    function formatCategory(
        value
    ) {

        return String(
            value || ""
        )
            .replace(/_/g, " ")
            .replace(/\b\w/g, (letter) =>
                letter.toUpperCase()
            );
    }

    function escapeHtml(value) {

        return String(
            value ?? ""
        )
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function safeUrl(url) {

        const value =
            String(url || "").trim();

        if (
            value.startsWith("https://") ||
            value.startsWith("http://")
        ) {
            return escapeHtml(value);
        }

        return "#";
    }

    function showElement(element) {

        if (!element) return;

        element.style.display =
            "";
    }

    function hideElement(element) {

        if (!element) return;

        element.style.display =
            "none";
    }

    function showMiniNotice(
        message
    ) {

        const notice =
            document.createElement(
                "div"
            );

        notice.className =
            "mini-notice";

        notice.textContent =
            message;

        document.body.appendChild(
            notice
        );

        setTimeout(
            () => {
                notice.remove();
            },
            2500
        );
    }

    // --------------------------------------------------------
    // INITIAL UI
    // --------------------------------------------------------

    hideElement(
        dynamicAlert
    );

    console.log(
        "TravelBytes AI frontend ready."
    );
});