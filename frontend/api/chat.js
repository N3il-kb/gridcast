import { openai } from "@ai-sdk/openai";
import { streamText, convertToModelMessages } from "ai";

export const config = { runtime: "edge" };

function hexSummary(props, label) {
  if (!props) return null;
  const region = props.region ?? "unknown region";
  const lines = [
    `${label} — ${region}:`,
    `  GridScore: ${props.dc_score ?? "N/A"}`,
    `  Sustainability: ${props.sustainability ?? "N/A"}`,
    `  Profitability: ${props.profitability ?? "N/A"}`,
    `  Renewable %: ${props.raw_renew != null ? props.raw_renew + "%" : "N/A"}`,
    `  Electricity Price (normalized): ${props.n_price ?? "N/A"}`,
    `  Load (normalized): ${props.n_load ?? "N/A"}`,
    `  Volatility (normalized): ${props.n_volatility ?? "N/A"}`,
    `  Local Temp: ${props.local_temp_c != null ? props.local_temp_c + "°C" : "N/A"}`,
    `  Elevation: ${props.elevation_m != null ? props.elevation_m + "m" : "N/A"}`,
    `  Temp Cooling Score: ${props.temp_cool_score ?? "N/A"}`,
    `  Cooling-Adjusted Score: ${props.dc_score_temp ?? "N/A"}`,
  ];
  return lines.join("\n");
}

export default async function handler(request) {
  const { messages = [], hexA, hexB } = await request.json();

  const hexContext = [hexSummary(hexA, "Hex A"), hexSummary(hexB, "Hex B")]
    .filter(Boolean)
    .join("\n\n");

  const systemPrompt = `You are **GridAsk**, the AI assistant for **GridCast** — a data platform that scores every U.S. electricity grid region for data center suitability. GridCast helps site-selection teams, sustainability analysts, and cloud infrastructure planners find the best locations for new data centers based on live grid conditions.

## How GridCast Works
GridCast runs a daily automated pipeline:
1. **EIA API** — Pulls live data from the U.S. Energy Information Administration for 13 regional electricity markets: hourly demand, fuel mix (solar, wind, nuclear, gas, etc.), and real-time wholesale electricity prices.
2. **Open-Meteo API** — Fetches 60-day mean temperature and elevation for each hex location. Temperature matters because cooling costs rise sharply in hot climates.
3. **AWS Fargate** — A containerized Python pipeline runs daily, triggered by EventBridge. It fetches all data, computes scores, and uploads results to S3.
4. **Scoring Engine** — Normalizes all signals to 0–1 and computes the composite GridScore.
5. **Frontend** — A React + Mapbox interactive hex map on Vercel renders ~6,000 H3 hexagons covering the continental US, each colored by its score.

## Scoring Methodology
**GridScore (0–1)** = 60% Sustainability + 40% Profitability

**Sustainability** (60% of GridScore):
- 70% weight: regional renewable energy percentage (solar + wind + hydro + nuclear as share of total generation)
- 30% weight: temperature/climate suitability (cooler = better for data center cooling)

**Profitability** (40% of GridScore):
- 40% weight: electricity price (lower = better)
- 30% weight: grid load/demand stability
- 30% weight: price volatility (lower = more predictable costs)

**Per-hex adjustments**: Each hex gets a cooling advantage boost: sustainability + 0.15 × temp_cool_score + 0.05 × elevation_factor. Scores are then smoothed using 20-nearest-neighbor KNN averaging.

## 13 US Grid Regions
CAL (California), CAR (Carolinas), CENT (Central), FLA (Florida), MIDA (Mid-Atlantic), MIDW (Midwest), NE (New England), NW (Northwest), NY (New York), SE (Southeast), SW (Southwest), TEN (Tennessee), TEX (Texas)

## Data Fields Available Per Hex
- **dc_score**: composite GridScore (0–1)
- **sustainability**: sustainability sub-score (0–1)
- **profitability**: profitability sub-score (0–1)
- **dc_score_temp**: temperature-adjusted GridScore
- **raw_renew**: raw renewable energy percentage
- **n_price, n_load, n_volatility**: normalized price, load, and volatility (0–1)
- **local_temp_c**: average temperature in °C
- **elevation_m**: elevation in meters
- **temp_cool_score**: cooling advantage factor
- **region**: which of the 13 grid regions this hex belongs to

${hexContext ? `## Currently Selected Hexagons\n${hexContext}` : "No hexagons currently selected."}

## Response Guidelines
- Use **markdown formatting**: bold for emphasis, bullet lists for comparisons, headers for structure.
- Be concise and data-driven. Reference specific scores and metrics when available.
- When comparing two hexes, highlight the key differences in a structured way.
- If no hexagons are selected, give general grid insights or explain how GridCast works.
- Keep responses focused — 2-4 short paragraphs max unless the user asks for detail.
- If a question is unrelated to GridCast, data centers, energy, electricity grids, or site selection, politely decline: "Sorry, I'm GridAsk — I can only help with questions about GridCast and U.S. electricity grid data."`;

  try {
    const modelMessages = await convertToModelMessages(messages);

    const result = streamText({
      model: openai("gpt-4o-mini"),
      system: systemPrompt,
      messages: modelMessages,
    });

    return result.toUIMessageStreamResponse();
  } catch (error) {
    // Fallback: manually map messages if convertToModelMessages fails
    const fallbackMessages = messages.map((m) => ({
      role: m.role,
      content:
        m.parts
          ?.filter((p) => p.type === "text")
          .map((p) => p.text)
          .join("") ||
        (typeof m.content === "string" ? m.content : "") ||
        "",
    }));

    const result = streamText({
      model: openai("gpt-4o-mini"),
      system: systemPrompt,
      messages: fallbackMessages,
    });

    return result.toUIMessageStreamResponse();
  }
}
