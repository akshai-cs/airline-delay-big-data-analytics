# Validation Checklist

| Check | Status | Evidence |
|---|---|---|
| `.venv` created or usable environment reused | PASS | Project `.venv` used for all execution. |
| Required dependencies installed inside `.venv` | PASS | PySpark, Jupyter, pandas, NumPy, Matplotlib, scikit-learn. |
| Spark session works | PASS | Spark 4.2.0, local[8]. |
| Actual dataset row count and schema verified | PASS | 7,079,081 rows, 35 columns. |
| Data cleaning and profiling complete | PASS | 7,079,081 rows retained; 0 duplicates removed. |
| Meaningful Spark SQL queries execute successfully | PASS | 14 queries executed. |
| Advanced analyses implemented where supported | PASS | Risk bands, correlations, sensitivity, MLlib prediction. |
| Actual result tables appear inside the notebook | PASS | All SQL and KPI tables displayed. |
| The same result tables are exported | PASS | 23 CSV files exported. |
| Graphs appear inside the notebook | PASS | 11 inline figures. |
| The same graphs are exported as PNG files | PASS | 11 PNG files in results_analysis/graphs/. |
| Detailed interpretations are available separately | PASS | RESULTS_AND_DISCUSSION.md and specialist reports. |
| Report and presentation outline reference real outputs | PASS | Generated from the exported metrics and tables. |
| Notebook executes from top to bottom | PASS | This cell is the final validation cell of a fresh execution. |
| Original dataset is preserved | PASS | SHA-256 unchanged: True; end hash 9456ed0695855469... |
| No fabricated results or unsupported claims | PASS | All numbers computed from the supplied CSV; limitations documented. |
