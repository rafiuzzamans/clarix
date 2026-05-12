// ============================================================
// MongoDB Init Script — Collections, Indexes & Schema Validation
// ============================================================

db = db.getSiblingDB('csplatform_nosql');

// ─── Chatbot Transcripts ─────────────────────────────────────
db.createCollection('chatbot_sessions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['session_id', 'started_at', 'status'],
      properties: {
        session_id:    { bsonType: 'string' },
        user_id:       { bsonType: ['string', 'null'] },
        ip_address:    { bsonType: 'string' },
        status:        { enum: ['active', 'resolved', 'escalated', 'abandoned'] },
        case_id:       { bsonType: ['string', 'null'] },
        started_at:    { bsonType: 'date' },
        ended_at:      { bsonType: ['date', 'null'] },
        messages:      { bsonType: 'array' },
        intent_history: { bsonType: 'array' },
        metadata:      { bsonType: 'object' }
      }
    }
  }
});

db.chatbot_sessions.createIndex({ session_id: 1 }, { unique: true });
db.chatbot_sessions.createIndex({ user_id: 1 });
db.chatbot_sessions.createIndex({ started_at: -1 });
db.chatbot_sessions.createIndex({ status: 1 });
db.chatbot_sessions.createIndex({ case_id: 1 });

// ─── AI Prediction Payloads ──────────────────────────────────
db.createCollection('ai_predictions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['case_id', 'predicted_at'],
      properties: {
        case_id:        { bsonType: 'string' },
        input_text:     { bsonType: 'string' },
        category:       { bsonType: 'object' },
        priority:       { bsonType: 'object' },
        sentiment:      { bsonType: 'object' },
        shap_values:    { bsonType: 'object' },
        model_version:  { bsonType: 'string' },
        predicted_at:   { bsonType: 'date' },
        overridden:     { bsonType: 'bool' },
        override_by:    { bsonType: ['string', 'null'] }
      }
    }
  }
});

db.ai_predictions.createIndex({ case_id: 1 });
db.ai_predictions.createIndex({ predicted_at: -1 });

// ─── Event Logs ──────────────────────────────────────────────
db.createCollection('event_logs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['service', 'event_type', 'timestamp'],
      properties: {
        service:      { bsonType: 'string' },
        event_type:   { bsonType: 'string' },
        severity:     { enum: ['debug', 'info', 'warning', 'error', 'critical'] },
        message:      { bsonType: 'string' },
        payload:      { bsonType: 'object' },
        trace_id:     { bsonType: 'string' },
        timestamp:    { bsonType: 'date' }
      }
    }
  }
});

db.event_logs.createIndex({ service: 1, event_type: 1 });
db.event_logs.createIndex({ timestamp: -1 });
db.event_logs.createIndex({ severity: 1 });
db.event_logs.createIndex({ timestamp: 1 }, { expireAfterSeconds: 7776000 }); // 90-day TTL

// ─── Automation Events ───────────────────────────────────────
db.createCollection('automation_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['trigger_type', 'triggered_at'],
      properties: {
        trigger_type:  { bsonType: 'string' },
        reference_id:  { bsonType: 'string' },
        status:        { enum: ['triggered', 'processed', 'failed', 'skipped'] },
        actions_taken: { bsonType: 'array' },
        error:         { bsonType: ['string', 'null'] },
        triggered_at:  { bsonType: 'date' }
      }
    }
  }
});

db.automation_events.createIndex({ trigger_type: 1 });
db.automation_events.createIndex({ triggered_at: -1 });
db.automation_events.createIndex({ reference_id: 1 });

// ─── Chatbot FAQ Knowledge Base ──────────────────────────────
db.createCollection('faq_knowledge');
db.faq_knowledge.createIndex({ tags: 1 });
db.faq_knowledge.createIndex({ '$**': 'text' }); // Full-text search

// ─── Seed FAQ data ───────────────────────────────────────────
db.faq_knowledge.insertMany([
  {
    question: 'How do I reset my password?',
    answer: 'You can reset your password by clicking "Forgot Password" on the login page. A reset link will be sent to your email.',
    tags: ['password', 'account', 'login', 'reset'],
    intent: 'password_reset',
    created_at: new Date()
  },
  {
    question: 'How can I track my order?',
    answer: 'Visit the "My Orders" section in your account dashboard and click on the order you want to track.',
    tags: ['order', 'tracking', 'shipping', 'delivery'],
    intent: 'order_tracking',
    created_at: new Date()
  },
  {
    question: 'How do I request a refund?',
    answer: 'To request a refund, go to My Orders, select the order, and click "Request Refund". Our team will process it within 3-5 business days.',
    tags: ['refund', 'return', 'money', 'billing'],
    intent: 'refund_request',
    created_at: new Date()
  },
  {
    question: 'How do I contact a human agent?',
    answer: 'You can escalate to a human agent at any time by typing "speak to agent" or clicking the "Escalate" button.',
    tags: ['agent', 'human', 'support', 'escalate'],
    intent: 'human_handoff',
    created_at: new Date()
  },
  {
    question: 'What are your support hours?',
    answer: 'Our support team is available Monday to Friday, 9 AM to 6 PM. Emergency support is available 24/7 for urgent cases.',
    tags: ['hours', 'support', 'availability', 'schedule'],
    intent: 'support_hours',
    created_at: new Date()
  },
  {
    question: 'How do I update my billing information?',
    answer: 'Go to Account Settings → Billing → Update Payment Method. Your information is securely stored and encrypted.',
    tags: ['billing', 'payment', 'card', 'update'],
    intent: 'billing_update',
    created_at: new Date()
  },
  {
    question: 'My product is not working. What should I do?',
    answer: 'We are sorry to hear that! Please describe the issue in detail and our technical team will assist you. You can also submit a support ticket.',
    tags: ['product', 'broken', 'technical', 'not working', 'issue'],
    intent: 'technical_issue',
    created_at: new Date()
  },
  {
    question: 'How do I cancel my subscription?',
    answer: 'You can cancel your subscription in Account Settings → Subscription → Cancel Plan. Please note this will take effect at the end of your billing cycle.',
    tags: ['cancel', 'subscription', 'account', 'plan'],
    intent: 'subscription_cancel',
    created_at: new Date()
  }
]);

print('MongoDB collections and indexes created successfully.');
