import asyncio
import httpx
import json
import os
from sqlalchemy import create_engine, text

# Database setup
engine = create_engine('postgresql://csadmin:cspassword123@localhost:5432/csplatform')

async def process_case(client, case):
    case_id, title, message = case
    text_to_predict = f"{title}. {message}"
    try:
        resp = await client.post(
            "http://localhost:8004/ai/predict",
            json={"text": text_to_predict}
        )
        if resp.status_code == 200:
            ai_data = resp.json()
            if "explanation" in ai_data and "top_features" in ai_data["explanation"]:
                ai_exp_obj = {
                    "top_features": ai_data["explanation"]["top_features"],
                    "probabilities": ai_data.get("category", {}).get("probabilities", {})
                }
                ai_exp = json.dumps(ai_exp_obj)
                with engine.connect() as conn:
                    conn.execute(
                        text("UPDATE cases SET ai_explanation = :ai_exp WHERE id = :id"),
                        {"ai_exp": ai_exp, "id": case_id}
                    )
                    conn.commit()
                print(f"Updated case {case_id}")
    except Exception as e:
        print(f"Failed to process case {case_id}: {e}")

async def main():
    with engine.connect() as conn:
        cases = conn.execute(text("SELECT id, title, message FROM cases")).fetchall()
        
    print(f"Found {len(cases)} cases to backfill.")
    
    async with httpx.AsyncClient(timeout=30.0) as session:
        for case in cases:
            await process_case(session, case)

if __name__ == "__main__":
    asyncio.run(main())
