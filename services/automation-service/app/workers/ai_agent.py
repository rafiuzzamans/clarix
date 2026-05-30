import asyncio
import os
import asyncpg
import httpx
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://csadmin:cspassword123@postgres:5432/csplatform")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8004")
CASE_SERVICE_URL = os.getenv("CASE_SERVICE_URL", "http://case-service:8003")
AI_AGENT_ID = "99999999-9999-9999-9999-999999999999"

async def auto_resolve_cases():
    print("[AGENT] Starting autonomous resolution loop...")
    while True:
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            cases = await conn.fetch(
                "SELECT id, message, category, sentiment FROM cases WHERE assigned_to = $1 AND status != 'resolved' AND status != 'closed'",
                AI_AGENT_ID
            )
            
            if cases:
                print(f"[AGENT] Found {len(cases)} cases to auto-resolve.")
                
            async with httpx.AsyncClient(timeout=10.0) as client:
                for case in cases:
                    case_id = str(case["id"])
                    
                    try:
                        resp = await client.post(
                            f"{AI_SERVICE_URL}/predict",
                            json={"text": case["message"]}
                        )
                        draft = "This issue was automatically resolved by the AI system."
                    except Exception as e:
                        print(f"[AGENT] Error generating reply: {e}")
                        draft = "This issue was automatically resolved by the AI system."
                    
                    now = datetime.now(timezone.utc)
                    
                    await conn.execute(
                        "INSERT INTO case_notes (case_id, author_id, content, is_internal, created_at) VALUES ($1, $2, $3, False, $4)",
                        case_id, AI_AGENT_ID, draft, now
                    )
                    
                    await conn.execute(
                        "UPDATE cases SET status = 'resolved', resolved_at = $2 WHERE id = $1",
                        case_id, now
                    )
                    
                    await conn.execute(
                        "INSERT INTO case_timeline (case_id, actor_id, event_type, description, new_value, created_at) VALUES ($1, $2, 'status_change', 'auto-resolved by Agent', 'resolved', $3)",
                        case_id, AI_AGENT_ID, now
                    )
                    
                    print(f"[AGENT] Successfully auto-resolved case {case_id}")
            
            await conn.close()
        except Exception as e:
            print(f"[AGENT] Polling error: {e}")
            
        await asyncio.sleep(10)
