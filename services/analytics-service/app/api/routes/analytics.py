from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from datetime import date, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", summary="Platform-wide KPI overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE status != 'closed')                           AS open_cases,
            COUNT(*) FILTER (WHERE status = 'resolved' OR status = 'closed')     AS resolved_cases,
            COUNT(*) FILTER (WHERE is_escalated = TRUE)                          AS escalated_cases,
            COUNT(*) FILTER (WHERE priority = 'urgent')                          AS urgent_cases,
            COUNT(*) FILTER (WHERE sentiment = 'negative')                       AS negative_sentiment,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours')    AS cases_today,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days')      AS cases_this_week,
            COUNT(*)                                                              AS total_cases,
            ROUND(AVG(
                EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600
            ) FILTER (WHERE resolved_at IS NOT NULL), 2)                         AS avg_resolution_hours
        FROM cases
    """))
    row = result.mappings().one()
    return dict(row)


@router.get("/case-volume", summary="Daily case volume for last N days")
async def case_volume(days: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT
            DATE(created_at AT TIME ZONE 'UTC') AS day,
            COUNT(*)                             AS total,
            COUNT(*) FILTER (WHERE status IN ('resolved','closed')) AS resolved,
            COUNT(*) FILTER (WHERE is_escalated)                    AS escalated
        FROM cases
        WHERE created_at >= NOW() - :days * INTERVAL '1 day'
        GROUP BY day
        ORDER BY day ASC
    """).bindparams(days=days))
    return {"data": [dict(r) for r in result.mappings().all()]}


@router.get("/sentiment-trend", summary="Sentiment breakdown over last N days")
async def sentiment_trend(days: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT
            DATE(created_at AT TIME ZONE 'UTC')                  AS day,
            COUNT(*) FILTER (WHERE sentiment = 'positive')       AS positive,
            COUNT(*) FILTER (WHERE sentiment = 'neutral')        AS neutral,
            COUNT(*) FILTER (WHERE sentiment = 'negative')       AS negative
        FROM cases
        WHERE created_at >= NOW() - :days * INTERVAL '1 day'
        GROUP BY day
        ORDER BY day ASC
    """).bindparams(days=days))
    return {"data": [dict(r) for r in result.mappings().all()]}


@router.get("/priority-breakdown", summary="Cases grouped by priority")
async def priority_breakdown(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT priority, COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status NOT IN ('resolved','closed')) AS open
        FROM cases
        GROUP BY priority
        ORDER BY CASE priority
            WHEN 'urgent' THEN 1 WHEN 'high' THEN 2
            WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END
    """))
    return {"data": [dict(r) for r in result.mappings().all()]}


@router.get("/category-breakdown", summary="Cases grouped by category")
async def category_breakdown(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT category, COUNT(*) AS total,
               COUNT(*) FILTER (WHERE sentiment = 'negative') AS negative_sentiment
        FROM cases
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY total DESC
    """))
    return {"data": [dict(r) for r in result.mappings().all()]}


@router.get("/agent-performance", summary="Agent performance metrics")
async def agent_performance(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT
            u.id            AS agent_id,
            u.full_name,
            u.department,
            COUNT(c.id)     AS assigned_cases,
            COUNT(c.id) FILTER (WHERE c.status IN ('resolved','closed'))    AS resolved_cases,
            COUNT(c.id) FILTER (WHERE c.is_escalated)                       AS escalated_cases,
            ROUND(AVG(EXTRACT(EPOCH FROM (c.resolved_at - c.created_at)) / 3600)
                  FILTER (WHERE c.resolved_at IS NOT NULL), 2)              AS avg_resolution_hours
        FROM users u
        LEFT JOIN cases c ON c.assigned_to = u.id
        WHERE u.role IN ('agent', 'supervisor')
        GROUP BY u.id, u.full_name, u.department
        ORDER BY resolved_cases DESC
    """))
    return {"data": [dict(r) for r in result.mappings().all()]}


@router.get("/status-breakdown", summary="Cases breakdown by status")
async def status_breakdown(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT status, COUNT(*) AS total
        FROM cases
        GROUP BY status
        ORDER BY total DESC
    """))
    return {"data": [dict(r) for r in result.mappings().all()]}


@router.get("/sla-compliance", summary="SLA compliance rate")
async def sla_compliance(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT
            COUNT(*)                                                           AS total,
            COUNT(*) FILTER (WHERE resolved_at <= sla_deadline)               AS within_sla,
            COUNT(*) FILTER (WHERE resolved_at > sla_deadline
                              OR (resolved_at IS NULL AND NOW() > sla_deadline)) AS breached_sla,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE resolved_at <= sla_deadline)
                / NULLIF(COUNT(*) FILTER (WHERE sla_deadline IS NOT NULL), 0), 2
            )                                                                  AS compliance_pct
        FROM cases
        WHERE sla_deadline IS NOT NULL
    """))
    row = result.mappings().one()
    return dict(row)


@router.post("/reporting/refresh", summary="Refresh daily reporting table")
async def refresh_daily_report(db: AsyncSession = Depends(get_db)):
    today = date.today()
    result = await db.execute(text("""
        INSERT INTO reporting_daily
            (report_date, total_cases, open_cases, resolved_cases, closed_cases,
             escalated_cases, sentiment_positive, sentiment_neutral, sentiment_negative)
        SELECT
            :today,
            COUNT(*),
            COUNT(*) FILTER (WHERE status NOT IN ('resolved','closed')),
            COUNT(*) FILTER (WHERE status = 'resolved'),
            COUNT(*) FILTER (WHERE status = 'closed'),
            COUNT(*) FILTER (WHERE is_escalated),
            COUNT(*) FILTER (WHERE sentiment = 'positive'),
            COUNT(*) FILTER (WHERE sentiment = 'neutral'),
            COUNT(*) FILTER (WHERE sentiment = 'negative')
        FROM cases
        ON CONFLICT (report_date) DO UPDATE SET
            total_cases      = EXCLUDED.total_cases,
            open_cases       = EXCLUDED.open_cases,
            resolved_cases   = EXCLUDED.resolved_cases,
            closed_cases     = EXCLUDED.closed_cases,
            escalated_cases  = EXCLUDED.escalated_cases,
            sentiment_positive = EXCLUDED.sentiment_positive,
            sentiment_neutral  = EXCLUDED.sentiment_neutral,
            sentiment_negative = EXCLUDED.sentiment_negative
    """), {"today": today})
    await db.commit()
    return {"status": "refreshed", "report_date": str(today)}

# Add case volume by day query

# Add avg resolution time metric

# Add agent performance endpoint

# Add SLA breach rate query
