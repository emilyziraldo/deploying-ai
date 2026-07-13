# City Explorer

City Explorer is an AI-powered city livability assistant designed to help users explore and compare cities around the world that they may want to live in! The chatbot helps users by providing information about weather, livability characteristics, and estimated cost of living for their household.

## Services Provided

City Explorer provides three main services:

- Current Weather Lookup: Retrieves current weather information for a selected city using the Open-Meteo API and converts the results into a naturally phrased response.
- City Livability Search: Uses semantic search over a city livability database to identify cities that match user preferences, such as affordability, transportation, climate, healthcare, and quality of life.
- Cost of Living Estimation: Calculates estimated living expenses based on user-provided assumptions, including housing, food, transportation, and miscellaneous costs.

## Implementation Decisions

The chatbot was implemented using tool-calling to allow the model to determine when external services are needed and then combines results into a conversational response.

Key implementation decisions include:

- Each of the 3 services is implemented as a separate function for easier maintenance and trouble-shooting.
- Raw API and JSON outputs are converted into clear, conversational explanations.
- Conversation history is maintained for continuity and user inputs are checked against the guardrails to enforce chatbot boundaries.