// Design tokens — consistent theming across all screens
export const theme = {
  colors: {
    // Backgrounds
    bg: '#030712',
    bgCard: '#0f172a',
    bgCardAlt: '#1e293b',
    bgInput: '#1e293b',
    border: '#334155',
    borderLight: '#475569',

    // Brand
    primary: '#6366f1',
    primaryDark: '#4f46e5',
    primaryLight: '#818cf8',
    secondary: '#8b5cf6',

    // Semantic
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',

    // Text
    textPrimary: '#f1f5f9',
    textSecondary: '#94a3b8',
    textMuted: '#475569',
    textInverse: '#0f172a',

    // Priority
    priorityLow: '#475569',
    priorityMedium: '#3b82f6',
    priorityHigh: '#f97316',
    priorityUrgent: '#ef4444',

    // Status
    statusOpen: '#6366f1',
    statusInProgress: '#f59e0b',
    statusResolved: '#10b981',
    statusClosed: '#475569',
    statusEscalated: '#ef4444',

    // Sentiment
    sentimentPositive: '#10b981',
    sentimentNeutral: '#6366f1',
    sentimentNegative: '#ef4444',
  },

  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },

  radius: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    full: 9999,
  },

  font: {
    xs: 11,
    sm: 13,
    base: 15,
    md: 17,
    lg: 20,
    xl: 24,
    xxl: 30,
  },

  shadow: {
    sm: {
      shadowColor: '#6366f1',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 4,
    },
    md: {
      shadowColor: '#6366f1',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.25,
      shadowRadius: 16,
      elevation: 8,
    },
  },
};

// Priority badge config
export const priorityConfig = {
  low:    { color: theme.colors.priorityLow,    label: 'Low' },
  medium: { color: theme.colors.priorityMedium, label: 'Medium' },
  high:   { color: theme.colors.priorityHigh,   label: 'High' },
  urgent: { color: theme.colors.priorityUrgent, label: 'Urgent' },
};

// Status badge config
export const statusConfig = {
  open:             { color: theme.colors.statusOpen,       label: 'Open' },
  in_progress:      { color: theme.colors.statusInProgress, label: 'In Progress' },
  pending_customer: { color: theme.colors.info,             label: 'Pending' },
  escalated:        { color: theme.colors.statusEscalated,  label: 'Escalated' },
  resolved:         { color: theme.colors.statusResolved,   label: 'Resolved' },
  closed:           { color: theme.colors.statusClosed,     label: 'Closed' },
};
