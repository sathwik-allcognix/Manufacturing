from langchain_core.prompts import ChatPromptTemplate


fotecasting_extract_params_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Extract forecasting parameters from the user query.\n\n"
            "GRANULARITY DETECTION:\n"
            "- Set granularity='monthly' for: 'all months', 'each month', 'monthly', 'month-by-month', specific month names\n"
            "- Set granularity='yearly' for: 'annual', 'yearly', 'year-by-year', 'per year'\n"
            "- Set granularity='daily' for everything else (default)\n\n"
            "HORIZON CALCULATION FOR MONTHLY:\n"
            "- Last date in dataset: {last_date}\n"
            "- If user asks 'next month' → start_horizon=1, end_horizon=1\n"
            "- If user asks 'February 2025' and last_date is Dec 2024 → start_horizon=2, end_horizon=2, single_day=True\n"
            "- If user asks 'next 3 months' → start_horizon=1, end_horizon=3\n"
            "- If user asks 'all months of 2026' and last_date is Dec 2024 → start_horizon=1, end_horizon=12 (next year)\n"
            "- If user asks 'March to June 2025' and last_date is Dec 2024 → start_horizon=3, end_horizon=6\n\n"
            "HORIZON CALCULATION FOR YEARLY:\n"
            "- If user asks 'next year' → start_horizon=1, end_horizon=1\n"
            "- If user asks '2025' and last_date year is 2023 → start_horizon=2, end_horizon=2, single_day=True\n"
            "- If user asks 'next 4 years' → start_horizon=1, end_horizon=4\n"
            "- If user asks '2025 to 2027' and last_date year is 2024 → start_horizon=1, end_horizon=3\n\n"
            "IMPORTANT:\n"
            "- start_horizon: Number of periods FROM the last date in dataset\n"
            "- end_horizon: Number of periods FROM the last date in dataset\n"
            "- For a range: end_horizon - start_horizon + 1 = number of periods to forecast\n"
            "- For single period: start_horizon = end_horizon, single_day=True\n\n"
            "Context:\n"
            "- Last date in dataset: {last_date}\n"
            "- Today's date: {today}\n\n"
        ),
        ("system", "{format_instructions}"),
        ("user", "User query: \"{user_query}\""),
        ("user", "Today's date: {today}"),
        ("user", "Last date in dataset: {last_date}")
    ])


fotecasting_classify_query_prompt = ChatPromptTemplate.from_messages([
        ("system", "Classify the user's query."),
        ("system", "{format_instructions}"),
        ("user", "User query: \"{user_query}\"")
    ])


fotecasting_conversational_response_prompt = ChatPromptTemplate.from_messages([
        ("system", "Provide a friendly conversational response in 2–3 sentences."),
        ("user", "{user_query}")
    ])