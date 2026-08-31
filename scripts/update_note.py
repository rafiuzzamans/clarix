from sqlalchemy import create_engine, text
engine = create_engine('postgresql://csadmin:cspassword123@localhost:5432/csplatform')
with engine.connect() as conn:
    conn.execute(
        text("UPDATE case_notes SET content = :content WHERE content LIKE 'This issue was automatically resolved by the AI system%' AND case_id = '17d88428-956e-44a7-a7d6-d02309198c98'"),
        {"content": "This issue was automatically resolved by the AI system (Category: Student Loan, Confidence: 94%).\n\nReasoning: The AI system classified this case as 'Student Loan' primarily due to the presence of key terms such as 'student loan', 'student', and 'loan'."}
    )
    conn.commit()
