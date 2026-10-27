"""Documented Spark SQL analyses executed against the cleaned flight view."""
from __future__ import annotations

SQL_QUERIES = [
    {
        "id": "Q01",
        "title": "Overall flight, delay, cancellation, and diversion statistics",
        "question": (
            "What is the overall scale of the 2024 dataset and how large are "
            "departure delay, arrival delay, cancellation, and diversion?"
        ),
        "export": "overall_flight_statistics.csv",
        "sql": """
SELECT
    COUNT(*) AS total_flights,
    SUM(is_cancelled) AS cancelled_flights,
    SUM(is_diverted) AS diverted_flights,
    SUM(is_flown) AS flown_flights,
    SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END) AS dep_delay_observed_flights,
    SUM(CASE WHEN arr_delay_valid THEN 1 ELSE 0 END) AS arr_delay_observed_flights,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 4) AS cancellation_rate_pct,
    ROUND(100.0 * SUM(is_diverted) / COUNT(*), 4) AS diversion_rate_pct,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 4) AS delayed_departure_rate_pct,
    ROUND(100.0 * SUM(arr_delayed) /
          NULLIF(SUM(CASE WHEN arr_delay_valid THEN 1 ELSE 0 END), 0), 4) AS delayed_arrival_rate_pct,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 4) AS avg_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.5), 2) AS median_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.9), 2) AS p90_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.99), 2) AS p99_dep_delay_min,
    ROUND(AVG(CASE WHEN arr_delay_valid THEN arr_delay END), 4) AS avg_arr_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN arr_delay_valid THEN arr_delay END, 0.5), 2) AS median_arr_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN arr_delay_valid THEN arr_delay END, 0.9), 2) AS p90_arr_delay_min,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN distance END), 2) AS avg_distance_mi
FROM flights_clean
""",
    },
    {
        "id": "Q02",
        "title": "Airline-wise flight volume",
        "question": "Which airlines operate the most flight legs and what share of the market do they represent?",
        "export": "airline_flight_volume.csv",
        "sql": """
SELECT
    op_unique_carrier,
    carrier_name,
    COUNT(*) AS flights,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share_of_flights_pct
FROM flights_clean
GROUP BY op_unique_carrier, carrier_name
ORDER BY flights DESC
""",
    },
    {
        "id": "Q03",
        "title": "Airline performance with minimum sample threshold",
        "question": (
            "After requiring at least 10,000 flights, how do airlines compare on "
            "mean/median departure delay and delayed-flight rates?"
        ),
        "export": "airline_performance.csv",
        "sql": """
SELECT
    op_unique_carrier,
    carrier_name,
    COUNT(*) AS flights,
    SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END) AS dep_delay_observed,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 2) AS avg_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.5), 2) AS median_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.9), 2) AS p90_dep_delay_min,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_departure_rate_pct,
    ROUND(AVG(CASE WHEN arr_delay_valid THEN arr_delay END), 2) AS avg_arr_delay_min,
    ROUND(100.0 * SUM(arr_delayed) /
          NULLIF(SUM(CASE WHEN arr_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_arrival_rate_pct,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 2) AS cancellation_rate_pct,
    ROUND(AVG(distance), 1) AS avg_distance_mi
FROM flights_clean
GROUP BY op_unique_carrier, carrier_name
HAVING COUNT(*) >= 10000
ORDER BY delayed_departure_rate_pct DESC
""",
    },
    {
        "id": "Q04",
        "title": "Monthly flight volume and delay trends",
        "question": "How do flight volume, departure/arrival delay, and cancellation rate change across 2024?",
        "export": "monthly_delay_analysis.csv",
        "sql": """
SELECT
    month,
    month_name,
    COUNT(*) AS flights,
    SUM(is_cancelled) AS cancelled_flights,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 2) AS cancellation_rate_pct,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 2) AS avg_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.5), 2) AS median_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.9), 2) AS p90_dep_delay_min,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_departure_rate_pct,
    ROUND(AVG(CASE WHEN arr_delay_valid THEN arr_delay END), 2) AS avg_arr_delay_min
FROM flights_clean
GROUP BY month, month_name
ORDER BY month
""",
    },
    {
        "id": "Q05",
        "title": "Day-of-week analysis",
        "question": "Are delays and cancellations systematically different by day of week?",
        "export": "day_of_week_analysis.csv",
        "sql": """
SELECT
    day_of_week,
    day_name,
    COUNT(*) AS flights,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 2) AS avg_dep_delay_min,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_departure_rate_pct,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 2) AS cancellation_rate_pct
FROM flights_clean
GROUP BY day_of_week, day_name
ORDER BY day_of_week
""",
    },
    {
        "id": "Q06",
        "title": "Scheduled departure-hour analysis",
        "question": "How does delay risk vary by the scheduled hour of departure?",
        "export": "departure_hour_analysis.csv",
        "sql": """
SELECT
    sched_dep_hour,
    COUNT(*) AS flights,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 2) AS avg_dep_delay_min,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_departure_rate_pct,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 2) AS cancellation_rate_pct
FROM flights_clean
WHERE sched_dep_hour IS NOT NULL
GROUP BY sched_dep_hour
ORDER BY sched_dep_hour
""",
    },
    {
        "id": "Q07",
        "title": "Origin-airport performance with minimum sample threshold",
        "question": (
            "Which origin airports handle the most flights, and how do delay and "
            "cancellation outcomes differ among airports with at least 10,000 flights?"
        ),
        "export": "airport_performance.csv",
        "sql": """
SELECT
    origin,
    origin_city_name,
    origin_state_nm,
    COUNT(*) AS flights,
    COUNT(DISTINCT dest) AS destinations_served,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 2) AS cancellation_rate_pct,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 2) AS avg_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.5), 2) AS median_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.9), 2) AS p90_dep_delay_min,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_departure_rate_pct
FROM flights_clean
GROUP BY origin, origin_city_name, origin_state_nm
HAVING COUNT(*) >= 10000
ORDER BY flights DESC
""",
    },
    {
        "id": "Q08",
        "title": "Route-level delay analysis with minimum sample threshold",
        "question": "Which origin-destination routes are busiest, and what are their delay characteristics?",
        "export": "route_delay_analysis.csv",
        "sql": """
SELECT
    origin,
    dest,
    route,
    ROUND(AVG(distance), 1) AS distance_mi,
    COUNT(*) AS flights,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 2) AS avg_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.5), 2) AS median_dep_delay_min,
    ROUND(PERCENTILE_APPROX(CASE WHEN dep_delay_valid THEN dep_delay END, 0.9), 2) AS p90_dep_delay_min,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_departure_rate_pct,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 2) AS cancellation_rate_pct
FROM flights_clean
GROUP BY origin, dest, route
HAVING COUNT(*) >= 200
ORDER BY flights DESC
""",
    },
    {
        "id": "Q09",
        "title": "Cancellation analysis by airline and reason",
        "question": "Which airlines have the highest cancellation rates, and which cancellation reasons dominate each airline?",
        "export": "cancellation_analysis.csv",
        "sql": """
SELECT
    op_unique_carrier,
    carrier_name,
    COUNT(*) AS flights,
    SUM(is_cancelled) AS cancelled_flights,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 2) AS cancellation_rate_pct,
    SUM(CASE WHEN cancellation_reason = 'Carrier' THEN 1 ELSE 0 END) AS carrier_reason,
    SUM(CASE WHEN cancellation_reason = 'Weather' THEN 1 ELSE 0 END) AS weather_reason,
    SUM(CASE WHEN cancellation_reason = 'National Airspace System' THEN 1 ELSE 0 END) AS nas_reason,
    SUM(CASE WHEN cancellation_reason = 'Security' THEN 1 ELSE 0 END) AS security_reason
FROM flights_clean
GROUP BY op_unique_carrier, carrier_name
ORDER BY cancellation_rate_pct DESC
""",
    },
    {
        "id": "Q10",
        "title": "Overall cancellation-reason distribution",
        "question": "What share of cancellations is attributed to carrier, weather, airspace, and security causes?",
        "export": "cancellation_reason_distribution.csv",
        "sql": """
SELECT
    cancellation_reason,
    COUNT(*) AS cancellations,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_of_cancellations_pct
FROM flights_clean
WHERE is_cancelled = 1
GROUP BY cancellation_reason
ORDER BY cancellations DESC
""",
    },
    {
        "id": "Q11",
        "title": "Delay-cause attribution among delayed departures",
        "question": (
            "Among delayed departures with available cause attribution, how are "
            "attributed delay minutes distributed across the five BTS cause categories?"
        ),
        "export": "delay_cause_analysis.csv",
        "sql": """
WITH causes AS (
    SELECT 'Carrier' AS cause,
           SUM(carrier_delay) AS attributed_minutes,
           SUM(CASE WHEN carrier_delay > 0 THEN 1 ELSE 0 END) AS flights_with_cause
    FROM flights_clean WHERE cause_available
    UNION ALL
    SELECT 'Weather' AS cause,
           SUM(weather_delay),
           SUM(CASE WHEN weather_delay > 0 THEN 1 ELSE 0 END)
    FROM flights_clean WHERE cause_available
    UNION ALL
    SELECT 'National Airspace System' AS cause,
           SUM(nas_delay),
           SUM(CASE WHEN nas_delay > 0 THEN 1 ELSE 0 END)
    FROM flights_clean WHERE cause_available
    UNION ALL
    SELECT 'Security' AS cause,
           SUM(security_delay),
           SUM(CASE WHEN security_delay > 0 THEN 1 ELSE 0 END)
    FROM flights_clean WHERE cause_available
    UNION ALL
    SELECT 'Late Aircraft' AS cause,
           SUM(late_aircraft_delay),
           SUM(CASE WHEN late_aircraft_delay > 0 THEN 1 ELSE 0 END)
    FROM flights_clean WHERE cause_available
)
SELECT
    cause,
    attributed_minutes,
    flights_with_cause,
    ROUND(100.0 * attributed_minutes / SUM(attributed_minutes) OVER (), 2) AS share_of_attributed_minutes_pct
FROM causes
ORDER BY attributed_minutes DESC
""",
    },
    {
        "id": "Q12",
        "title": "Delay-risk category distribution",
        "question": "How are flown flights distributed across documented departure-delay risk categories?",
        "export": "delay_risk_distribution.csv",
        "sql": """
SELECT
    delay_risk,
    COUNT(*) AS flights,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share_pct,
    ROUND(AVG(dep_delay), 2) AS avg_dep_delay_min,
    ROUND(PERCENTILE_APPROX(dep_delay, 0.9), 2) AS p90_dep_delay_min
FROM flights_clean
WHERE is_flown = 1 AND dep_delay_valid
GROUP BY delay_risk
ORDER BY flights DESC
""",
    },
    {
        "id": "Q13",
        "title": "Delay by flight-distance band",
        "question": "Do short-haul and long-haul flights differ in departure-delay outcomes?",
        "export": "distance_band_analysis.csv",
        "sql": """
SELECT
    distance_band,
    COUNT(*) AS flights,
    ROUND(AVG(distance), 1) AS avg_distance_mi,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 2) AS avg_dep_delay_min,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_departure_rate_pct,
    ROUND(100.0 * SUM(is_cancelled) / COUNT(*), 2) AS cancellation_rate_pct
FROM flights_clean
GROUP BY distance_band
ORDER BY avg_distance_mi
""",
    },
    {
        "id": "Q14",
        "title": "Peak scheduled flight periods",
        "question": "Which day-of-week and scheduled-hour combinations carry the largest flight volume?",
        "export": "peak_periods.csv",
        "sql": """
SELECT
    day_of_week,
    day_name,
    sched_dep_hour,
    COUNT(*) AS flights,
    ROUND(AVG(CASE WHEN dep_delay_valid THEN dep_delay END), 2) AS avg_dep_delay_min,
    ROUND(100.0 * SUM(dep_delayed) /
          NULLIF(SUM(CASE WHEN dep_delay_valid THEN 1 ELSE 0 END), 0), 2) AS delayed_departure_rate_pct
FROM flights_clean
WHERE sched_dep_hour IS NOT NULL
GROUP BY day_of_week, day_name, sched_dep_hour
ORDER BY flights DESC
LIMIT 15
""",
    },
]
