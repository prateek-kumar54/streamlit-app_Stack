# streamlit-app_Stack

## Setup

Install dependencies before running the Streamlit app:

```bash
pip install -r requirements.txt
```

Run the application with:

```bash
streamlit run app.py
```

### Deploying updates to Streamlit Community Cloud

If your project is hosted on [Streamlit Community Cloud](https://streamlit.io/cloud), make sure the updated code reaches the watched repository. After committing locally:

1. Push the commit to the remote (for example, `git push origin main`).
2. In the Streamlit dashboard, open your app and click **Rerun**, or choose **Manage app → Reboot**, to trigger a fresh build. This rebuild installs dependencies from `requirements.txt` and picks up your latest code changes.

Until you push the commit and restart the cloud app, the hosted instance will continue running the older revision and the previous dependency error will persist.

## Modular layout

The Streamlit entry point (`app.py`) renders the shared front-end shell and routes button clicks to dedicated feature modules inside the `features/` package. Each button on the home screen has its own `render(...)` function so you can evolve workflows in isolation without touching the rest of the app.

## Data Reconciliation Module

The data reconciliation workflow relies on OCR and extraction providers. Ensure the required API keys are supplied when prompted in the UI. Missing dependencies will now be installed automatically when a run is triggered inside the module, or up front when `pip install -r requirements.txt` is executed.
