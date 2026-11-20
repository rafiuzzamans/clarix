import asyncio
import os
import asyncpg
import httpx
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://csadmin:cspassword123@localhost:5432/csplatform")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8004")

async def fix_bad_notes():
    print("Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Find all bad notes
        bad_notes = await conn.fetch(
            "SELECT id, case_id, content FROM case_notes WHERE content LIKE '%Category: Unknown, Confidence: 0%%'"
        )
        
        if not bad_notes:
            print("No bad notes found to fix.")
            await conn.close()
            return

        print(f"Found {len(bad_notes)} bad notes to fix.")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for note in bad_notes:
                note_id = note['id']
                case_id = note['case_id']
                
                # Get the original case message
                case = await conn.fetchrow("SELECT message FROM cases WHERE id = $1", case_id)
                if not case:
                    continue
                    
                message = case['message']
                
                try:
                    # Get correct prediction
                    resp = await client.post(
                        f"{AI_SERVICE_URL}/ai/predict",
                        json={"text": message}
                    )
                    result = resp.json()
                    cat = result.get("label_category", "unknown").replace("_", " ").title()
                    conf = result.get("confidence", 0.0)
                    
                    draft = f"This issue was automatically resolved by the AI system (Category: {cat}, Confidence: {conf:.0%})."
                    
                    explanation = result.get("explanation", {})
                    top_features = explanation.get("top_features", [])
                    if top_features:
                        terms = [f"'{f['feature']}'" for f in top_features[:3]]
                        if len(terms) > 1:
                            terms_str = ", ".join(terms[:-1]) + f", and {terms[-1]}"
                        else:
                            terms_str = terms[0]
                        draft += f"\n\nReasoning: The AI system classified this case as '{cat}' primarily due to the presence of key terms such as {terms_str}."
                        
                    # Update the note in the database
                    await conn.execute("UPDATE case_notes SET content = $1 WHERE id = $2", draft, note_id)
                    print(f"Fixed note {note_id} for case {case_id}")
                    
                except Exception as e:
                    print(f"Failed to fix note {note_id}: {e}")
                    
        await conn.close()
        print("Done fixing notes.")
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_bad_notes())
