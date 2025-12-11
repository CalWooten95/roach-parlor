// Re-export auth types
export * from './auth';

// Core data types for the application

export type WagerStatus = 'pending' | 'won' | 'lost' | 'push' | 'cancelled';

export interface Wager {
  id: number;
  userId: number;
  description: string;
  amount: number;
  line: string;
  status: WagerStatus;
  isFrePlay: boolean;
  isLiveBet: boolean;
  autoCalculate: boolean;
  liveTrackingEnabled: boolean;
  archived: boolean;
  createdAt: string;
  resultedAt?: string;
  lastCalculationAttempt?: string;
  
  // Relationships
  legs: WagerLeg[];
  matchup?: WagerMatchup;
  calculations: WagerCalculation[];
  
  // Computed properties
  payout?: number;
  currentOdds?: LiveOdds;
  liveScore?: GameScore;
}

export interface WagerLeg {
  id: number;
  wagerId: number;
  description: string;
  status: WagerStatus;
  createdAt: string;
}

export interface WagerMatchup {
  id: number;
  homeTeam: string;
  awayTeam: string;
  league: string;
  scheduledTime: string;
  externalGameId?: string;
  espnEventId?: string;
}

export interface LiveOdds {
  id: number;
  matchupId: number;
  provider: string;
  moneylineHome?: number;
  moneylineAway?: number;
  spreadHome?: number;
  spreadAway?: number;
  totalOver?: number;
  totalUnder?: number;
  timestamp: string;
}

export interface GameScore {
  homeScore: number;
  awayScore: number;
  period?: string;
  gameTime?: string;
  status: 'scheduled' | 'live' | 'final' | 'postponed';
}

export interface WagerCalculation {
  id: number;
  wagerId: number;
  calculationType: 'auto' | 'manual';
  inputData: Record<string, any>;
  result: 'won' | 'lost' | 'push';
  confidenceScore: number;
  calculatedAt: string;
  calculatedBy?: number;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// WebSocket event types
export interface WebSocketEvents {
  'wager-updated': {
    wagerId: number;
    status: WagerStatus;
    calculation?: WagerCalculation;
  };
  'live-score': {
    matchupId: number;
    score: GameScore;
  };
  'odds-changed': {
    matchupId: number;
    odds: LiveOdds;
  };
  'system-alert': {
    message: string;
    severity: 'info' | 'warning' | 'error';
  };
}