// Application constants
export const APP_NAME = 'Roach Parlor';
export const APP_VERSION = '2.0.0';

// API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
  },
  WAGERS: {
    LIST: '/wagers',
    CREATE: '/wagers',
    UPDATE: (id: number) => `/wagers/${id}`,
    DELETE: (id: number) => `/wagers/${id}`,
    STATUS: (id: number) => `/wagers/${id}/status`,
  },
  LIVE: {
    MATCHUPS: '/live/matchups',
    MATCHUP: (id: number) => `/live/matchups/${id}`,
    SCORE: (id: number) => `/live/matchups/${id}/score`,
    ODDS: (id: number) => `/live/odds/${id}`,
    CALCULATE: (id: number) => `/live/calculate/${id}`,
  },
  ADMIN: {
    SYSTEM_STATUS: '/admin/system-status',
    LIVE_TRACKING_TOGGLE: '/admin/live-tracking/toggle',
    CALCULATION_LOGS: '/admin/calculation-logs',
  },
} as const;

// Local storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'authToken',
  USER_PREFERENCES: 'userPreferences',
  THEME_MODE: 'themeMode',
} as const;

// Wager status options
export const WAGER_STATUSES = {
  PENDING: 'pending',
  WON: 'won',
  LOST: 'lost',
  PUSH: 'push',
  CANCELLED: 'cancelled',
} as const;

// User roles
export const USER_ROLES = {
  USER: 'user',
  ADMIN: 'admin',
} as const;

// WebSocket events
export const SOCKET_EVENTS = {
  JOIN_ROOM: 'join-room',
  LEAVE_ROOM: 'leave-room',
  WAGER_UPDATED: 'wager-updated',
  LIVE_SCORE: 'live-score',
  ODDS_CHANGED: 'odds-changed',
  SYSTEM_ALERT: 'system-alert',
} as const;

// Query keys for React Query
export const QUERY_KEYS = {
  WAGERS: 'wagers',
  WAGER: 'wager',
  LIVE_MATCHUPS: 'live-matchups',
  LIVE_ODDS: 'live-odds',
  USER: 'user',
  SYSTEM_STATUS: 'system-status',
} as const;