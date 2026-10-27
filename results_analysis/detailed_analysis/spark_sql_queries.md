# Spark SQL Queries - Executed Results

All queries were executed against the temporary view `flights_clean` over the
cleaned 7,079,081-row Spark DataFrame. Query times are from this notebook run.

| ID | Query | Rows returned | Time (s) | Export |
|---|---|---:|---:|---|
| Q01 | Overall flight, delay, cancellation, and diversion statistics | 1 | 26.334 | `overall_flight_statistics.csv` |
| Q02 | Airline-wise flight volume | 15 | 4.782 | `airline_flight_volume.csv` |
| Q03 | Airline performance with minimum sample threshold | 15 | 23.839 | `airline_performance.csv` |
| Q04 | Monthly flight volume and delay trends | 12 | 11.843 | `monthly_delay_analysis.csv` |
| Q05 | Day-of-week analysis | 7 | 3.098 | `day_of_week_analysis.csv` |
| Q06 | Scheduled departure-hour analysis | 24 | 2.963 | `departure_hour_analysis.csv` |
| Q07 | Origin-airport performance with minimum sample threshold | 101 | 50.071 | `airport_performance.csv` |
| Q08 | Route-level delay analysis with minimum sample threshold | 4,744 | 40.262 | `route_delay_analysis.csv` |
| Q09 | Cancellation analysis by airline and reason | 15 | 3.608 | `cancellation_analysis.csv` |
| Q10 | Overall cancellation-reason distribution | 4 | 1.723 | `cancellation_reason_distribution.csv` |
| Q11 | Delay-cause attribution among delayed departures | 5 | 4.695 | `delay_cause_analysis.csv` |
| Q12 | Delay-risk category distribution | 5 | 7.003 | `delay_risk_distribution.csv` |
| Q13 | Delay by flight-distance band | 5 | 2.789 | `distance_band_analysis.csv` |
| Q14 | Peak scheduled flight periods | 15 | 3.634 | `peak_periods.csv` |

## Q01 - Overall flight, delay, cancellation, and diversion statistics

**Business question:** What is the overall scale of the 2024 dataset and how large are departure delay, arrival delay, cancellation, and diversion?

```sql
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
```

**Rows returned:** 1  
**Execution time:** 26.334 seconds  
**Export:** `results_analysis/analytical_results/overall_flight_statistics.csv`

| total_flights | cancelled_flights | diverted_flights | flown_flights | dep_delay_observed_flights | arr_delay_observed_flights | cancellation_rate_pct | diversion_rate_pct | delayed_departure_rate_pct | delayed_arrival_rate_pct | avg_dep_delay_min | median_dep_delay_min | p90_dep_delay_min | p99_dep_delay_min | avg_arr_delay_min | median_arr_delay_min | p90_arr_delay_min | avg_distance_mi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7079081 | 96315 | 17499 | 6982766 | 6982766 | 6965267 | 1.36 | 0.25 | 20.64 | 20.82 | 12.65 | -2.00 | 44.00 | 216.00 | 7.10 | -6.00 | 43.00 | 834.20 |

## Q02 - Airline-wise flight volume

**Business question:** Which airlines operate the most flight legs and what share of the market do they represent?

```sql
SELECT
    op_unique_carrier,
    carrier_name,
    COUNT(*) AS flights,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS share_of_flights_pct
FROM flights_clean
GROUP BY op_unique_carrier, carrier_name
ORDER BY flights DESC
```

**Rows returned:** 15  
**Execution time:** 4.782 seconds  
**Export:** `results_analysis/analytical_results/airline_flight_volume.csv`

| op_unique_carrier | carrier_name | flights | share_of_flights_pct |
|---|---|---|---|
| WN | Southwest Airlines | 1419419 | 20.05 |
| DL | Delta Air Lines | 1009194 | 14.26 |
| AA | American Airlines | 984306 | 13.90 |
| UA | United Airlines | 760451 | 10.74 |
| OO | SkyWest Airlines | 744658 | 10.52 |
| YX | Republic Airways | 301465 | 4.26 |
| MQ | Envoy Air | 279955 | 3.95 |
| NK | Spirit Airlines | 261103 | 3.69 |
| AS | Alaska Airlines | 245819 | 3.47 |
| B6 | JetBlue Airways | 240282 | 3.39 |
| OH | PSA Airlines | 227971 | 3.22 |
| F9 | Frontier Airlines | 208624 | 2.95 |
| 9E | Endeavor Air | 200094 | 2.83 |
| G4 | Allegiant Air | 117210 | 1.66 |
| HA | Hawaiian Airlines | 78530 | 1.11 |

## Q03 - Airline performance with minimum sample threshold

**Business question:** After requiring at least 10,000 flights, how do airlines compare on mean/median departure delay and delayed-flight rates?

```sql
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
```

**Rows returned:** 15  
**Execution time:** 23.839 seconds  
**Export:** `results_analysis/analytical_results/airline_performance.csv`

| op_unique_carrier | carrier_name | flights | dep_delay_observed | avg_dep_delay_min | median_dep_delay_min | p90_dep_delay_min | delayed_departure_rate_pct | avg_arr_delay_min | delayed_arrival_rate_pct | cancellation_rate_pct | avg_distance_mi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F9 | Frontier Airlines | 208624 | 203789 | 18.95 | -2.00 | 67.00 | 27.68 | 15.25 | 28.74 | 2.32 | 877.80 |
| B6 | JetBlue Airways | 240282 | 236547 | 17.40 | -2.00 | 65.00 | 25.79 | 10.74 | 25.51 | 1.55 | 1182.60 |
| AA | American Airlines | 984306 | 969054 | 20.65 | -1.00 | 63.00 | 25.59 | 15.31 | 26.13 | 1.55 | 967.40 |
| NK | Spirit Airlines | 261103 | 256105 | 14.92 | -2.00 | 56.00 | 24.96 | 8.42 | 23.93 | 1.91 | 958.80 |
| WN | Southwest Airlines | 1419419 | 1407647 | 11.74 | 0.00 | 39.00 | 23.37 | 5.13 | 20.60 | 0.83 | 756.90 |
| G4 | Allegiant Air | 117210 | 115192 | 14.04 | -5.00 | 49.00 | 21.24 | 9.71 | 21.67 | 1.72 | 901.70 |
| AS | Alaska Airlines | 245819 | 241008 | 7.61 | -2.00 | 35.00 | 20.11 | 4.47 | 22.07 | 1.96 | 1407.50 |
| OH | PSA Airlines | 227971 | 224220 | 13.87 | -4.00 | 50.00 | 19.77 | 10.03 | 21.77 | 1.65 | 427.40 |
| UA | United Airlines | 760451 | 747973 | 11.91 | -3.00 | 44.00 | 19.00 | 5.74 | 19.86 | 1.64 | 1120.40 |
| MQ | Envoy Air | 279955 | 275970 | 10.14 | -2.00 | 38.00 | 18.75 | 6.46 | 20.86 | 1.42 | 517.50 |
| DL | Delta Air Lines | 1009194 | 1000047 | 10.21 | -2.00 | 34.00 | 17.16 | 3.66 | 17.26 | 0.91 | 952.10 |
| OO | SkyWest Airlines | 744658 | 736131 | 11.27 | -4.00 | 41.00 | 17.15 | 7.36 | 19.00 | 1.15 | 456.70 |
| 9E | Endeavor Air | 200094 | 195486 | 8.28 | -5.00 | 32.00 | 14.88 | 1.68 | 15.83 | 2.30 | 456.90 |
| HA | Hawaiian Airlines | 78530 | 77708 | 5.46 | -1.00 | 20.00 | 13.31 | 4.25 | 15.45 | 1.05 | 913.20 |
| YX | Republic Airways | 301465 | 295889 | 3.91 | -5.00 | 21.00 | 11.68 | -1.79 | 14.07 | 1.85 | 494.30 |

## Q04 - Monthly flight volume and delay trends

**Business question:** How do flight volume, departure/arrival delay, and cancellation rate change across 2024?

```sql
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
```

**Rows returned:** 12  
**Execution time:** 11.843 seconds  
**Export:** `results_analysis/analytical_results/monthly_delay_analysis.csv`

| month | month_name | flights | cancelled_flights | cancellation_rate_pct | avg_dep_delay_min | median_dep_delay_min | p90_dep_delay_min | delayed_departure_rate_pct | avg_arr_delay_min |
|---|---|---|---|---|---|---|---|---|---|
| 1 | January | 547271 | 20389 | 3.73 | 15.62 | -2.00 | 51.00 | 23.14 | 10.35 |
| 2 | February | 519221 | 3002 | 0.58 | 7.44 | -3.00 | 28.00 | 15.49 | 0.59 |
| 3 | March | 591767 | 5120 | 0.87 | 12.43 | -2.00 | 43.00 | 20.83 | 6.50 |
| 4 | April | 582205 | 4035 | 0.69 | 10.79 | -2.00 | 38.00 | 18.89 | 5.36 |
| 5 | May | 609743 | 8244 | 1.35 | 18.06 | -1.00 | 60.00 | 25.64 | 14.05 |
| 6 | June | 611132 | 7876 | 1.29 | 16.90 | -1.00 | 55.00 | 25.31 | 11.81 |
| 7 | July | 634613 | 18372 | 2.89 | 22.30 | 0.00 | 72.00 | 29.49 | 18.09 |
| 8 | August | 619025 | 12714 | 2.05 | 15.25 | -2.00 | 52.00 | 23.03 | 10.59 |
| 9 | September | 582622 | 3499 | 0.60 | 6.64 | -3.00 | 27.00 | 15.07 | 1.00 |
| 10 | October | 615497 | 6284 | 1.02 | 5.44 | -3.00 | 23.00 | 13.60 | -1.28 |
| 11 | November | 575404 | 2629 | 0.46 | 6.21 | -3.00 | 26.00 | 14.41 | -0.32 |
| 12 | December | 590581 | 4151 | 0.70 | 13.53 | -1.00 | 45.00 | 21.63 | 7.12 |

## Q05 - Day-of-week analysis

**Business question:** Are delays and cancellations systematically different by day of week?

```sql
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
```

**Rows returned:** 7  
**Execution time:** 3.098 seconds  
**Export:** `results_analysis/analytical_results/day_of_week_analysis.csv`

| day_of_week | day_name | flights | avg_dep_delay_min | delayed_departure_rate_pct | cancellation_rate_pct |
|---|---|---|---|---|---|
| 1 | Monday | 1073959 | 12.70 | 20.60 | 1.37 |
| 2 | Tuesday | 976073 | 10.43 | 17.70 | 1.28 |
| 3 | Wednesday | 973179 | 10.38 | 18.09 | 1.25 |
| 4 | Thursday | 1041956 | 13.13 | 21.35 | 1.45 |
| 5 | Friday | 1055419 | 14.63 | 22.98 | 1.52 |
| 6 | Saturday | 911515 | 12.56 | 20.63 | 1.20 |
| 7 | Sunday | 1046980 | 14.36 | 22.74 | 1.43 |

## Q06 - Scheduled departure-hour analysis

**Business question:** How does delay risk vary by the scheduled hour of departure?

```sql
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
```

**Rows returned:** 24  
**Execution time:** 2.963 seconds  
**Export:** `results_analysis/analytical_results/departure_hour_analysis.csv`

| sched_dep_hour | flights | avg_dep_delay_min | delayed_departure_rate_pct | cancellation_rate_pct |
|---|---|---|---|---|
| 0 | 12331 | 15.51 | 24.75 | 1.62 |
| 1 | 4077 | 14.66 | 22.04 | 1.74 |
| 2 | 1543 | 11.11 | 25.10 | 1.88 |
| 3 | 1093 | 9.84 | 21.98 | 2.20 |
| 4 | 534 | 16.36 | 22.24 | 1.50 |
| 5 | 200157 | 5.17 | 7.83 | 1.32 |
| 6 | 495017 | 3.99 | 7.68 | 1.27 |
| 7 | 493915 | 4.90 | 9.81 | 1.21 |
| 8 | 482402 | 5.79 | 11.97 | 1.07 |
| 9 | 395739 | 7.20 | 14.17 | 1.07 |
| 10 | 439299 | 8.67 | 16.44 | 1.07 |
| 11 | 442008 | 9.89 | 17.91 | 1.02 |
| 12 | 419882 | 11.43 | 19.58 | 1.15 |
| 13 | 423120 | 12.88 | 21.55 | 1.14 |
| 14 | 406552 | 14.54 | 23.69 | 1.30 |

## Q07 - Origin-airport performance with minimum sample threshold

**Business question:** Which origin airports handle the most flights, and how do delay and cancellation outcomes differ among airports with at least 10,000 flights?

```sql
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
```

**Rows returned:** 101  
**Execution time:** 50.071 seconds  
**Export:** `results_analysis/analytical_results/airport_performance.csv`

| origin | origin_city_name | origin_state_nm | flights | destinations_served | cancellation_rate_pct | avg_dep_delay_min | median_dep_delay_min | p90_dep_delay_min | delayed_departure_rate_pct |
|---|---|---|---|---|---|---|---|---|---|
| ATL | Atlanta, GA | Georgia | 341910 | 157 | 1.00 | 11.08 | -2.00 | 38.00 | 19.74 |
| DFW | Dallas/Fort Worth, TX | Texas | 313582 | 186 | 1.86 | 18.89 | -1.00 | 62.00 | 27.50 |
| DEN | Denver, CO | Colorado | 308645 | 180 | 1.13 | 13.24 | -1.00 | 46.00 | 23.17 |
| ORD | Chicago, IL | Illinois | 280052 | 163 | 1.35 | 15.20 | -2.00 | 53.00 | 22.15 |
| CLT | Charlotte, NC | North Carolina | 217574 | 132 | 1.37 | 18.39 | -1.00 | 61.00 | 26.44 |
| LAX | Los Angeles, CA | California | 194053 | 112 | 0.81 | 10.25 | -2.00 | 36.00 | 18.03 |
| PHX | Phoenix, AZ | Arizona | 193551 | 110 | 0.61 | 10.94 | -1.00 | 39.00 | 20.07 |
| LAS | Las Vegas, NV | Nevada | 189252 | 132 | 0.88 | 12.86 | -1.00 | 45.00 | 23.54 |
| SEA | Seattle, WA | Washington | 163725 | 92 | 1.11 | 9.53 | -1.00 | 35.00 | 20.55 |
| LGA | New York, NY | New York | 162432 | 86 | 2.37 | 10.61 | -4.00 | 42.00 | 17.96 |
| MCO | Orlando, FL | Florida | 159553 | 91 | 1.82 | 15.92 | -1.00 | 54.00 | 24.55 |
| BOS | Boston, MA | Massachusetts | 143490 | 77 | 1.45 | 11.98 | -3.00 | 46.00 | 20.13 |
| DCA | Washington, DC | Virginia | 140016 | 103 | 1.59 | 12.08 | -3.00 | 44.00 | 19.56 |
| SFO | San Francisco, CA | California | 134978 | 82 | 1.33 | 14.49 | -1.00 | 49.00 | 23.35 |
| DTW | Detroit, MI | Michigan | 131367 | 101 | 1.03 | 11.20 | -3.00 | 40.00 | 18.36 |

## Q08 - Route-level delay analysis with minimum sample threshold

**Business question:** Which origin-destination routes are busiest, and what are their delay characteristics?

```sql
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
```

**Rows returned:** 4,744  
**Execution time:** 40.262 seconds  
**Export:** `results_analysis/analytical_results/route_delay_analysis.csv`

| origin | dest | route | distance_mi | flights | avg_dep_delay_min | median_dep_delay_min | p90_dep_delay_min | delayed_departure_rate_pct | cancellation_rate_pct |
|---|---|---|---|---|---|---|---|---|---|
| OGG | HNL | OGG-HNL | 100.00 | 11642 | 1.72 | -3.00 | 14.00 | 9.91 | 1.10 |
| HNL | OGG | HNL-OGG | 100.00 | 11634 | 2.27 | -2.00 | 14.00 | 9.66 | 0.95 |
| LAX | SFO | LAX-SFO | 337.00 | 11526 | 14.48 | -2.00 | 56.00 | 25.91 | 0.90 |
| SFO | LAX | SFO-LAX | 337.00 | 11499 | 14.75 | -1.00 | 53.00 | 25.78 | 1.01 |
| LGA | ORD | LGA-ORD | 733.00 | 10971 | 13.16 | -4.00 | 48.00 | 17.65 | 2.22 |
| ORD | LGA | ORD-LGA | 733.00 | 10969 | 15.52 | -3.00 | 57.00 | 22.30 | 2.06 |
| LAX | JFK | LAX-JFK | 2475.00 | 9915 | 13.56 | -3.00 | 38.00 | 17.00 | 0.44 |
| JFK | LAX | JFK-LAX | 2475.00 | 9915 | 9.11 | -3.00 | 29.00 | 15.04 | 0.39 |
| DCA | BOS | DCA-BOS | 399.00 | 9658 | 12.64 | -5.00 | 53.00 | 20.45 | 1.65 |
| BOS | DCA | BOS-DCA | 399.00 | 9657 | 9.50 | -5.00 | 40.00 | 16.88 | 1.58 |
| LAX | LAS | LAX-LAS | 236.00 | 9603 | 13.04 | -2.00 | 51.00 | 23.34 | 0.91 |
| LAS | LAX | LAS-LAX | 236.00 | 9559 | 12.51 | -1.00 | 46.00 | 23.55 | 0.77 |
| PHX | DEN | PHX-DEN | 602.00 | 9479 | 11.48 | -1.00 | 40.00 | 20.55 | 1.17 |
| DEN | PHX | DEN-PHX | 602.00 | 9446 | 12.85 | 0.00 | 46.00 | 24.09 | 1.07 |
| MCO | ATL | MCO-ATL | 404.00 | 8967 | 16.87 | -1.00 | 54.00 | 24.24 | 1.53 |

## Q09 - Cancellation analysis by airline and reason

**Business question:** Which airlines have the highest cancellation rates, and which cancellation reasons dominate each airline?

```sql
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
```

**Rows returned:** 15  
**Execution time:** 3.608 seconds  
**Export:** `results_analysis/analytical_results/cancellation_analysis.csv`

| op_unique_carrier | carrier_name | flights | cancelled_flights | cancellation_rate_pct | carrier_reason | weather_reason | nas_reason | security_reason |
|---|---|---|---|---|---|---|---|---|
| F9 | Frontier Airlines | 208624 | 4835 | 2.32 | 2234 | 2601 | 0 | 0 |
| 9E | Endeavor Air | 200094 | 4608 | 2.30 | 1209 | 1085 | 2314 | 0 |
| AS | Alaska Airlines | 245819 | 4811 | 1.96 | 4016 | 785 | 10 | 0 |
| NK | Spirit Airlines | 261103 | 4998 | 1.91 | 872 | 3801 | 323 | 2 |
| YX | Republic Airways | 301465 | 5576 | 1.85 | 609 | 2862 | 2105 | 0 |
| G4 | Allegiant Air | 117210 | 2018 | 1.72 | 751 | 964 | 303 | 0 |
| OH | PSA Airlines | 227971 | 3751 | 1.65 | 383 | 3250 | 118 | 0 |
| UA | United Airlines | 760451 | 12478 | 1.64 | 8159 | 2794 | 1525 | 0 |
| AA | American Airlines | 984306 | 15252 | 1.55 | 1986 | 12899 | 367 | 0 |
| B6 | JetBlue Airways | 240282 | 3735 | 1.55 | 774 | 1217 | 1744 | 0 |
| MQ | Envoy Air | 279955 | 3985 | 1.42 | 341 | 2692 | 952 | 0 |
| OO | SkyWest Airlines | 744658 | 8527 | 1.15 | 122 | 7707 | 696 | 2 |
| HA | Hawaiian Airlines | 78530 | 822 | 1.05 | 727 | 95 | 0 | 0 |
| DL | Delta Air Lines | 1009194 | 9147 | 0.91 | 6559 | 2451 | 137 | 0 |
| WN | Southwest Airlines | 1419419 | 11772 | 0.83 | 2184 | 8402 | 1186 | 0 |

## Q10 - Overall cancellation-reason distribution

**Business question:** What share of cancellations is attributed to carrier, weather, airspace, and security causes?

```sql
SELECT
    cancellation_reason,
    COUNT(*) AS cancellations,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_of_cancellations_pct
FROM flights_clean
WHERE is_cancelled = 1
GROUP BY cancellation_reason
ORDER BY cancellations DESC
```

**Rows returned:** 4  
**Execution time:** 1.723 seconds  
**Export:** `results_analysis/analytical_results/cancellation_reason_distribution.csv`

| cancellation_reason | cancellations | share_of_cancellations_pct |
|---|---|---|
| Weather | 53605 | 55.66 |
| Carrier | 30926 | 32.11 |
| National Airspace System | 11780 | 12.23 |
| Security | 4 | 0.00 |

## Q11 - Delay-cause attribution among delayed departures

**Business question:** Among delayed departures with available cause attribution, how are attributed delay minutes distributed across the five BTS cause categories?

```sql
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
```

**Rows returned:** 5  
**Execution time:** 4.695 seconds  
**Export:** `results_analysis/analytical_results/delay_cause_analysis.csv`

| cause | attributed_minutes | flights_with_cause | share_of_attributed_minutes_pct |
|---|---|---|---|
| Late Aircraft | 41663879 | 703105 | 43.61 |
| Carrier | 34760328 | 695667 | 36.38 |
| National Airspace System | 12822056 | 449956 | 13.42 |
| Weather | 6128867 | 81418 | 6.41 |
| Security | 172419 | 6478 | 0.18 |

## Q12 - Delay-risk category distribution

**Business question:** How are flown flights distributed across documented departure-delay risk categories?

```sql
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
```

**Rows returned:** 5  
**Execution time:** 7.003 seconds  
**Export:** `results_analysis/analytical_results/delay_risk_distribution.csv`

| delay_risk | flights | share_pct | avg_dep_delay_min | p90_dep_delay_min |
|---|---|---|---|---|
| On-time / early (<15 min) | 5541627 | 79.36 | -2.87 | 6.00 |
| Minor (15-29 min) | 489989 | 7.02 | 21.12 | 27.00 |
| Moderate (30-59 min) | 434972 | 6.23 | 42.23 | 55.00 |
| Severe (60-119 min) | 307679 | 4.41 | 83.67 | 109.00 |
| Extreme (120+ min) | 208499 | 2.99 | 238.62 | 389.00 |

## Q13 - Delay by flight-distance band

**Business question:** Do short-haul and long-haul flights differ in departure-delay outcomes?

```sql
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
```

**Rows returned:** 5  
**Execution time:** 2.789 seconds  
**Export:** `results_analysis/analytical_results/distance_band_analysis.csv`

| distance_band | flights | avg_distance_mi | avg_dep_delay_min | delayed_departure_rate_pct | cancellation_rate_pct |
|---|---|---|---|---|---|
| <250 mi | 802935 | 175.90 | 10.96 | 18.21 | 1.53 |
| 250-499 mi | 1614684 | 373.40 | 11.19 | 19.42 | 1.27 |
| 500-999 mi | 2595767 | 734.90 | 12.94 | 21.03 | 1.41 |
| 1000-1499 mi | 1150993 | 1188.30 | 14.50 | 22.57 | 1.42 |
| 1500+ mi | 914702 | 2059.50 | 13.52 | 21.37 | 1.18 |

## Q14 - Peak scheduled flight periods

**Business question:** Which day-of-week and scheduled-hour combinations carry the largest flight volume?

```sql
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
```

**Rows returned:** 15  
**Execution time:** 3.634 seconds  
**Export:** `results_analysis/analytical_results/peak_periods.csv`

| day_of_week | day_name | sched_dep_hour | flights | avg_dep_delay_min | delayed_departure_rate_pct |
|---|---|---|---|---|---|
| 1 | Monday | 6 | 75169 | 4.13 | 7.81 |
| 5 | Friday | 6 | 73894 | 5.50 | 8.61 |
| 1 | Monday | 7 | 73654 | 5.11 | 10.14 |
| 4 | Thursday | 6 | 73140 | 2.82 | 6.86 |
| 4 | Thursday | 7 | 72351 | 4.07 | 9.16 |
| 5 | Friday | 7 | 72312 | 6.58 | 10.97 |
| 1 | Monday | 8 | 72105 | 6.36 | 12.63 |
| 7 | Sunday | 7 | 71345 | 5.40 | 10.32 |
| 5 | Friday | 8 | 70801 | 7.13 | 13.25 |
| 4 | Thursday | 8 | 70352 | 5.16 | 11.19 |
| 2 | Tuesday | 6 | 70102 | 3.81 | 7.35 |
| 2 | Tuesday | 7 | 69500 | 4.60 | 9.44 |
| 7 | Sunday | 6 | 68880 | 4.67 | 8.28 |
| 3 | Wednesday | 6 | 68786 | 2.33 | 6.61 |
| 7 | Sunday | 8 | 68727 | 6.22 | 12.67 |
