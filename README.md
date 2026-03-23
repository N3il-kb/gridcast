# [GridCast](https://gridcast-v2.vercel.app/)
 
**AI-powered datacenter suitability platform using real-time energy grid data.**
 
GridCast scores and maps optimal locations for datacenter deployment across the United States by analyzing renewable energy availability, grid stability, cooling advantages, and operational costs — combining ESG performance with profitability into a single composite metric.
 
---
 
## What It Does
 
GridCast pulls live data from the U.S. Energy Information Administration (EIA) and Open-Meteo, runs it through a multi-stage scoring pipeline, and renders the results as an interactive hex-grid map. Each hexagonal cell across the continental US gets a **GridScore** — a weighted composite of sustainability and profitability factors.
 
An embedded AI assistant (**GridAsk**) lets users ask natural language questions about selected regions, energy mix, pricing, and grid conditions.
 
---
 
## Demo
 
The frontend is deployed on Vercel. The data pipeline runs daily on AWS Fargate, updating scores and uploading results to S3.