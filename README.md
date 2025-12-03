## Manufacturing Forecasting System

This project is a small end-to-end **agentic manufacturing demand forecasting** system.
It uses:

- **Backend**: FastAPI, SQLAlchemy, SQLite, LangChain, LangGraph, statsmodels ARIMA, Groq (via `langchain-groq`)
- **Frontend**: Vite, React, TypeScript, Axios, Recharts

### Backend

Location: `backend/`

- Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

- (Optional) set Groq key and model:

```bash
export GROQ_API_KEY=your_key_here
export GROQ_MODEL=mixtral-8x7b-32768  # or llama3-70b-8192
```

- Run the API:

```bash
uvicorn app.main:app --reload
```

The main forecasting route is:

- `GET /forecast/{product_id}?days=30`

It executes the LangGraph workflow:

`fetch_data_agent → preprocess_agent → arima_agent → report_agent`

### Frontend

Location: `frontend/`

- Install and run:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` (e.g. `http://localhost:8000`) in an `.env` file if needed.

### Tests

From `backend/`:

```bash
pytest
```


