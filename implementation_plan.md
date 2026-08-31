# Goal Description
The goal is to provide human agents with more insight into how the AI's confidence score (e.g., 94%) is determined. We will accomplish this by extracting the category probabilities (how the AI distributed its confidence across competing categories like 'student loan' vs 'bank account') and displaying them in the frontend UI.

## Proposed Changes

### Frontend (web-app)
- **MODIFY** [`web-app/app/dashboard/cases/[id]/page.tsx`](file:///c:/Project/web-app/app/dashboard/cases/[id]/page.tsx)
  - Safely parse the `ai_explanation` JSON field to support both the legacy array format (just top features) and the new object format (features + probabilities).
  - Add a new "Confidence Breakdown" section or tooltip near the "Confidence: XX%" badge. This will visually display a list or small progress bars for the top 3 category probabilities, allowing agents to see what other categories the AI considered.

### Backend (case-service)
- **MODIFY** [`services/case-service/app/services/case_service.py`](file:///c:/Project/services/case-service/app/services/case_service.py)
  - Update the case creation logic so that when the AI returns its prediction, both the `top_features` and the `probabilities` dictionary are stored together as a JSON object inside the `ai_explanation` database column. This avoids the need for a complex database migration while keeping all AI reasoning data in one place.

### Data Backfill
- **MODIFY** [`scripts/backfill_ai_explanation.py`](file:///c:/Project/scripts/backfill_ai_explanation.py)
  - Update the script to store the new `{"top_features": [...], "probabilities": {...}}` JSON structure instead of just the features list.
- **EXECUTE** Run the backfill script sequentially to update all 86 existing cases in the database so the probabilities are immediately visible for historical cases.

## Verification Plan
1. Ensure the frontend handles both legacy and new data structures without crashing.
2. Validate that the confidence breakdown renders beautifully in the case details page.
3. Verify that running the backfill script successfully updates all cases without causing timeouts in the AI service.
