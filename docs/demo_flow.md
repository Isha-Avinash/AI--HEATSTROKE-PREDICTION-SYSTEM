# Client Demo Flow

Use this flow for a 5-7 minute MVP-style presentation.

Open with the trust-and-safety positioning:

> This is a decision-support demo for heat-stress screening. It is not a medical device or autonomous diagnosis system. High-risk outputs should trigger human review, cooling steps, and emergency response when red-flag symptoms are present.

## 1. Live Screening

Show how an operator enters:

- Worker/person ID
- Ambient temperature and humidity
- Body temperature
- Hydration
- Symptoms

Run the screening and highlight:

- Final risk level
- ML probability breakdown
- Safety-rule override, if triggered
- Explainability panel
- Emergency checklist for high-risk cases

## 2. Monitoring Dashboard

Show the high-risk queue first. This is the strongest client-facing value:

> "Who needs attention right now?"

Then show:

- Filters
- Patient timeline
- Risk distribution
- Symptom/risk heatmap
- Export filtered CSV

## 3. Scenario Simulator

Run a preset heatwave scenario, then switch to custom mode and adjust:

- Temperature range
- Humidity range
- Hydration range
- Symptom probabilities

Explain that this helps teams plan for heatwave events, sports camps, factories, or outdoor workforces.

## 4. Safety Protocols

Close with the safety response page:

- Heat exhaustion signs
- Heat stroke warning signs
- Cooling steps
- Emergency guidance

## Screenshot Checklist

Capture these screens for slides or README assets:

- `screenshots/01-live-screening.png`
- `screenshots/02-high-risk-result.png`
- `screenshots/03-monitoring-queue.png`
- `screenshots/04-risk-pattern-explorer.png`
- `screenshots/05-scenario-builder.png`
- `screenshots/06-safety-protocols.png`
