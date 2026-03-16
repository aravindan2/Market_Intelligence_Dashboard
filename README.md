# Market Intelligence – Oil & Commodities

HTML/CSS/JS frontend with a Python (Flask) API. Live prices (scraped), RSS news, India supply chain, and a decision framework (thresholds, alerts, recommendations).

## Run the app

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python server.py
```

Open **http://localhost:5000**

- **Command Center** – KPIs, global map, news ticker  
- **Markets** – Price history, heatmap, correlation, latest levels  
- **Supply Chain & Decisions** – India map, supply stages, regional table, alerts and recommendations  

Theme toggle (header) switches light/dark mode.

## API (from Flask)

- `GET /api/prices/latest` – latest commodity quotes  
- `GET /api/prices/history?days=90` – OHLC time series  
- `GET /api/news?limit=30` – RSS news items  
- `GET /api/india-supply-chain` – stages, regional, summary  
- `GET /api/decisions` – alerts and recommendations from thresholds  
- `GET /api/map/prices` – country-level values for global map  

## Config

- **Decision thresholds**: `config/thresholds.json` (WTI/Brent min/max, volatility, refining margin, etc.). The backend reads this on each `/api/decisions` call.

## Legacy (Dash)

The previous Dash app is still under `src/app.py`. To run it: `cd src && python app.py` (port 8052). The new stack uses the same data layer in `src/data/` via the Flask server.
