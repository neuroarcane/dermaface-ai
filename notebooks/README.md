# Notebooks

Exploratory work. Keep production logic in `src/dermaface/`, not in notebooks.

Suggested notebooks for the sprint:

- `01_eda.ipynb` — dataset EDA: class balance, skin-tone distribution, image quality (Owner: Aparna)
- `02_label_harmonization.ipynb` — mapping the 3 datasets to the unified taxonomy + severity method (Owner: Aparna + Iva)
- `03_baseline_training.ipynb` — first transfer-learning run (Owner: Iva + Varsha)
- `04_gradcam_demo.ipynb` — sanity-check Grad-CAM overlays (Owner: Varsha)
- `05_fairness_analysis.ipynb` — metrics by Fitzpatrick type for the report (Owner: Iva)

> Clear notebook outputs before committing (`jupyter nbconvert --clear-output`) to keep diffs clean and avoid committing any images.
