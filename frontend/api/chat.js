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
    `  Renewable Energy: ${props.raw_renew != null ? props.raw_renew + "%" : "N/A"}`,
    `  Local Temp: ${props.local_temp_c != null ? props.local_temp_c + "°C" : "N/A"}`,
    `  Elevation: ${props.elevation_m != null ? props.elevation_m + "m" : "N/A"}`,
  ];
  return lines.join("\n");
}

export default async function handler(request) {
  const { messages, hexA, hexB } = await request.json();

  const hexContext = [hexSummary(hexA, "Hex A"), hexSummary(hexB, "Hex B")]
    .filter(Boolean)
    .join("\n\n");

  const systemPrompt = `You are GridAsk, an AI assistant for GridCast — a platform that scores U.S. electricity grid regions for data center suitability.

GridScore (0–1) combines:
- Sustainability (60%): renewable energy percentage and regional climate
- Profitability (40%): electricity price, demand, and volatility

${hexContext ? `Currently selected hexagons:\n${hexContext}` : "No hexagons currently selected."}

Answer questions about the grid, explain scores, compare regions, and give data center suitability insights. Be concise and factual. If no hexagons are selected, give general grid insights.`;

  const result = await streamText({
    model: openai("gpt-4o-mini"),
    system: systemPrompt,
    messages: convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
