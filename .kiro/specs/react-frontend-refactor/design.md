# Design Document

## Overview

The React Frontend Refactor project transforms the existing Roach Parlor Betting Tracker from a server-rendered FastAPI application into a modern, real-time sports betting tracker with a React frontend, enhanced live data integration, and automated win/loss calculation. The system will maintain all existing functionality while adding significant new capabilities for live sports tracking and automated outcome determination.

The architecture follows a clear separation of concerns with the React frontend handling all user interactions and presentation logic, the FastAPI backend managing business logic and data persistence, and new live tracking services providing real-time sports data integration. WebSocket connections enable real-time updates between components, while the existing Discord bot integration remains fully functional.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React SPA     │    │  FastAPI Backend │    │  Discord Bot    │
│                 │    │                  │    │                 │
│ • Components    │◄──►│ • REST APIs      │◄──►│ • Image OCR     │
│ • State Mgmt    │    │ • WebSocket      │    │ • Wager Creation│
│ • Real-time UI  │    │ • Business Logic │    │ • Reactions     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐              │
         │              │  PostgreSQL DB  │              │
         │              │                 │              │
         │              │ • Wagers        │              │
         │              │ • Users         │              │
         │              │ • Matchups      │              │
         │              │ • Live Data     │              │
         │              └─────────────────┘              │
         │                       │                       │
         │              ┌────────▼────────┐              │
         └──────────────►│ Live Tracking   │◄────────────┘
                        │ Services        │
                        │                 │
                        │ • ESPN API      │
                        │ • Auto Calc     │
                        │ • WebSocket Hub │
                        └─────────────────┘
```

### Component Architecture

**Frontend (React SPA)**
- Modern React 18 with TypeScript for type safety
- React Router for client-side navigation
- React Query for server state management and caching
- Socket.IO client for real-time updates
- Material-UI or Tailwind CSS for consistent styling
- Chart.js or Recharts for data visualization

**Backend (Enhanced FastAPI)**
- Existing FastAPI application with additional endpoints
- Socket.IO server for WebSocket connections
- Background tasks for live data polling
- Enhanced database models for live tracking
- JWT authentication for API security

**Live Tracking Services**
- ESPN API integration service (enhanced existing)
- Automated outcome calculation engine
- WebSocket event broadcasting
- Data synchronization and caching layer

## Components and Interfaces

### React Frontend Components

**Core Layout Components**
```typescript
interface AppLayoutProps {
  children: React.ReactNode;
  user?: AuthenticatedUser;
}

interface NavigationProps {
  currentPath: string;
  userRole: 'user' | 'admin';
}

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}
```

**Wager Management Components**
```typescript
interface WagerCardProps {
  wager: Wager;
  onStatusUpdate: (wagerId: number, status: WagerStatus) => void;
  onArchive: (wagerId: number) => void;
  showActions?: boolean;
}

interface WagerListProps {
  wagers: Wager[];
  loading: boolean;
  onRefresh: () => void;
}

interface WagerFormProps {
  onSubmit: (wager: CreateWagerRequest) => void;
  initialData?: Partial<Wager>;
}
```

**Live Tracking Components**
```typescript
interface LiveMatchupProps {
  matchup: LiveMatchup;
  relatedWagers: Wager[];
}

interface LiveScoreProps {
  gameId: string;
  homeTeam: Team;
  awayTeam: Team;
  currentScore: GameScore;
}

interface OddsComparisonProps {
  originalLine: string;
  currentOdds: LiveOdds;
  movement: OddsMovement;
}
```

### API Interfaces

**Enhanced REST Endpoints**
```typescript
// Existing endpoints remain unchanged
GET /wagers/{user_id}
POST /wagers/
PATCH /wagers/{id}/status

// New live tracking endpoints
GET /live/matchups
GET /live/matchups/{id}/score
GET /live/odds/{matchup_id}
POST /live/calculate/{wager_id}

// Enhanced admin endpoints
GET /admin/system-status
POST /admin/live-tracking/toggle
GET /admin/calculation-logs
```

**WebSocket Events**
```typescript
interface WebSocketEvents {
  // Client to Server
  'join-room': { userId: number };
  'leave-room': { userId: number };
  
  // Server to Client
  'wager-updated': { wagerId: number; status: WagerStatus; calculation?: CalculationResult };
  'live-score': { matchupId: number; score: GameScore };
  'odds-changed': { matchupId: number; odds: LiveOdds };
  'system-alert': { message: string; severity: 'info' | 'warning' | 'error' };
}
```

### Database Schema Enhancements

**New Tables**
```sql
-- Live game data
CREATE TABLE live_games (
    id SERIAL PRIMARY KEY,
    external_game_id VARCHAR UNIQUE NOT NULL,
    matchup_id INTEGER REFERENCES wager_matchups(id),
    status VARCHAR NOT NULL, -- 'scheduled', 'live', 'final'
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    game_time VARCHAR, -- Current game time/period
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Live odds tracking
CREATE TABLE live_odds (
    id SERIAL PRIMARY KEY,
    matchup_id INTEGER REFERENCES wager_matchups(id),
    provider VARCHAR NOT NULL,
    moneyline_home DECIMAL,
    moneyline_away DECIMAL,
    spread_home DECIMAL,
    spread_away DECIMAL,
    total_over DECIMAL,
    total_under DECIMAL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calculation audit trail
CREATE TABLE wager_calculations (
    id SERIAL PRIMARY KEY,
    wager_id INTEGER REFERENCES wagers(id),
    calculation_type VARCHAR NOT NULL, -- 'auto', 'manual'
    input_data JSONB, -- Game data used for calculation
    result VARCHAR NOT NULL, -- 'won', 'lost', 'push'
    confidence_score DECIMAL, -- 0.0 to 1.0
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calculated_by INTEGER REFERENCES auth_users(id)
);
```

**Enhanced Existing Tables**
```sql
-- Add live tracking flags to wagers
ALTER TABLE wagers ADD COLUMN auto_calculate BOOLEAN DEFAULT TRUE;
ALTER TABLE wagers ADD COLUMN live_tracking_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE wagers ADD COLUMN last_calculation_attempt TIMESTAMP WITH TIME ZONE;

-- Add external IDs for API integration
ALTER TABLE wager_matchups ADD COLUMN external_game_id VARCHAR;
ALTER TABLE wager_matchups ADD COLUMN espn_event_id VARCHAR;
```

## Data Models

### Core Data Models

**Enhanced Wager Model**
```typescript
interface Wager {
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
```

**Live Tracking Models**
```typescript
interface LiveMatchup {
  id: number;
  externalGameId: string;
  espnEventId?: string;
  status: 'scheduled' | 'live' | 'final' | 'postponed';
  homeScore: number;
  awayScore: number;
  gameTime?: string;
  period?: string;
  lastUpdated: string;
  
  // Relationships
  matchup: WagerMatchup;
  currentOdds: LiveOdds[];
  relatedWagers: Wager[];
}

interface LiveOdds {
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

interface WagerCalculation {
  id: number;
  wagerId: number;
  calculationType: 'auto' | 'manual';
  inputData: Record<string, any>;
  result: 'won' | 'lost' | 'push';
  confidenceScore: number;
  calculatedAt: string;
  calculatedBy?: number;
}
```

**State Management Models**
```typescript
interface AppState {
  auth: AuthState;
  wagers: WagerState;
  live: LiveState;
  ui: UIState;
}

interface AuthState {
  user?: AuthenticatedUser;
  token?: string;
  isAuthenticated: boolean;
  loading: boolean;
}

interface WagerState {
  active: Wager[];
  archived: Wager[];
  loading: boolean;
  error?: string;
  filters: WagerFilters;
}

interface LiveState {
  matchups: LiveMatchup[];
  connected: boolean;
  lastUpdate?: string;
  systemStatus: SystemStatus;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

**Property 1: Frontend data consistency**
*For any* wager data retrieved from the backend, the React frontend should display all required fields (description, amount, line, status, legs, matchup) with the same information as the original system
**Validates: Requirements 1.1, 1.2**

**Property 2: API communication integrity**
*For any* user action that modifies wager state, the React frontend should communicate exclusively through designated REST API endpoints and update the UI state correctly
**Validates: Requirements 1.3, 4.1**

**Property 3: Client-side navigation consistency**
*For any* navigation action within the React application, the URL should change and components should update without triggering full page reloads
**Validates: Requirements 1.4**

**Property 4: Administrative function preservation**
*For any* administrative operation available in the current system, the React frontend should provide equivalent functionality with the same access controls
**Validates: Requirements 1.5, 6.1**

**Property 5: Automatic wager calculation accuracy**
*For any* completed sports game with related wagers, the Auto_Calculator should determine win/loss outcomes that match the betting line and actual game results
**Validates: Requirements 2.1, 2.2**

**Property 6: Real-time update propagation**
*For any* live sports data change, all connected React frontend clients should receive WebSocket updates within acceptable latency bounds
**Validates: Requirements 2.3, 3.3**

**Property 7: Statistical calculation correctness**
*For any* wager involving player props or statistics, the Auto_Calculator should evaluate outcomes against live statistical data and produce verifiable results
**Validates: Requirements 2.4**

**Property 8: Audit trail completeness**
*For any* automatic wager calculation, the system should create audit records containing calculation logic, input data, and confidence scores
**Validates: Requirements 2.5**

**Property 9: Live odds display accuracy**
*For any* active wager with available live odds, the React frontend should display both original betting lines and current odds side by side
**Validates: Requirements 3.1**

**Property 10: Odds movement notification reliability**
*For any* significant odds change exceeding configured thresholds, the system should notify users of material changes to their active wagers
**Validates: Requirements 3.2**

**Property 11: Multi-game performance consistency**
*For any* number of simultaneously active games, the system should maintain consistent performance and data accuracy across all live matchups
**Validates: Requirements 3.5**

**Property 12: WebSocket authentication and error handling**
*For any* real-time connection, the system should properly authenticate WebSocket connections and handle disconnections with automatic reconnection
**Validates: Requirements 4.2, 8.4**

**Property 13: Interactive visualization functionality**
*For any* statistics data, the React frontend should render interactive charts and graphs using modern visualization libraries
**Validates: Requirements 5.1**

**Property 14: Performance metrics calculation accuracy**
*For any* user's betting history, the system should calculate correct ROI, win rates by bet type, and profit trends
**Validates: Requirements 5.2**

**Property 15: Client-side filtering efficiency**
*For any* data filtering or sorting operation, the React frontend should perform operations without server round trips while maintaining data consistency
**Validates: Requirements 5.3**

**Property 16: Pagination and data loading efficiency**
*For any* large dataset request, the system should support efficient pagination and loading without performance degradation
**Validates: Requirements 5.4**

**Property 17: Data export functionality**
*For any* user's betting history and analytics, the React frontend should provide export options in common formats (CSV, JSON, PDF)
**Validates: Requirements 5.5**

**Property 18: Bulk operation consistency**
*For any* batch operation on multiple wagers, the system should update all selected wagers atomically or provide clear error reporting
**Validates: Requirements 6.2**

**Property 19: Configuration persistence**
*For any* live tracking configuration change, the system should persist settings and apply them consistently across user sessions
**Validates: Requirements 6.3**

**Property 20: System status monitoring accuracy**
*For any* system component (Discord Bot, Live Tracker, external APIs), the React frontend should display accurate real-time status information
**Validates: Requirements 6.4**

**Property 21: Role-based access control enforcement**
*For any* user with specific role permissions, the system should only allow access to functions appropriate to their role level
**Validates: Requirements 6.5**

**Property 22: Discord integration preservation**
*For any* betting slip submitted via Discord, the Discord Bot should continue processing images and creating wagers with the same functionality as before
**Validates: Requirements 7.1**

**Property 23: Real-time Discord synchronization**
*For any* wager created via Discord, the React frontend should immediately reflect the new wager without requiring page refresh
**Validates: Requirements 7.2**

**Property 24: Discord matchup data extraction**
*For any* betting slip processed by the Discord Bot, sufficient matchup data should be extracted to enable automatic live tracking
**Validates: Requirements 7.3**

**Property 25: Discord reaction synchronization**
*For any* Discord reaction added to a wager message, the React frontend should reflect the reaction status accurately
**Validates: Requirements 7.4**

**Property 26: Error communication consistency**
*For any* Discord bot error, the React frontend should display appropriate error messages and provide retry options where applicable
**Validates: Requirements 7.5**

**Property 27: Offline functionality graceful degradation**
*For any* network connectivity loss, the React frontend should gracefully handle offline states and queue actions for retry when connectivity returns
**Validates: Requirements 8.1**

**Property 28: API error handling and retry reliability**
*For any* API call failure, the system should provide meaningful error messages and implement automatic retry mechanisms with exponential backoff
**Validates: Requirements 8.2**

**Property 29: Data feed fallback reliability**
*For any* live data feed unavailability, the system should fall back to cached data and notify users of the degraded state
**Validates: Requirements 8.3**

**Property 30: Error logging and user messaging separation**
*For any* critical error, the system should log detailed debugging information while displaying user-friendly messages to end users
**Validates: Requirements 8.5**

**Property 31: Responsive design adaptation**
*For any* mobile device access, the React frontend should provide optimized layouts and touch-friendly interactions appropriate to the screen size
**Validates: Requirements 9.1**

**Property 32: PWA offline functionality**
*For any* offline usage scenario, the React frontend should cache essential data and provide core functionality without network connectivity
**Validates: Requirements 9.2**

**Property 33: PWA installation capability**
*For any* supported device (mobile or desktop), the React frontend should support installation as a Progressive Web App
**Validates: Requirements 9.3**

**Property 34: Push notification delivery**
*For any* important wager update or live event, the system should deliver push notifications to subscribed users
**Validates: Requirements 9.4**

**Property 35: Cross-device state consistency**
*For any* user switching between devices, the system should maintain consistent state and user preferences across all platforms
**Validates: Requirements 9.5**

**Property 36: API documentation completeness**
*For any* API endpoint, comprehensive OpenAPI documentation should be available with examples and proper schema definitions
**Validates: Requirements 10.1**

**Property 37: Test coverage completeness**
*For any* REST endpoint and WebSocket functionality, automated test suites should exist and provide adequate coverage
**Validates: Requirements 10.2**

**Property 38: Performance monitoring availability**
*For any* API operation, metrics and logging should be available for monitoring response times and error rates
**Validates: Requirements 10.3**

**Property 39: Debugging capability sufficiency**
*For any* system issue, detailed logging and tracing capabilities should be available to support effective debugging
**Validates: Requirements 10.4**

**Property 40: API versioning support**
*For any* API extension or modification, the system should support versioning mechanisms and maintain backward compatibility
**Validates: Requirements 10.5**

<function_calls>
<invoke name="prework">
<parameter name="featureName">react-frontend-refactor

## Error Handling

### Frontend Error Handling Strategy

**Network and API Errors**
- Implement retry logic with exponential backoff for transient failures
- Display user-friendly error messages while logging technical details
- Provide manual retry options for failed operations
- Cache successful responses to enable graceful degradation

**WebSocket Connection Management**
- Automatic reconnection with connection state indicators
- Graceful handling of connection drops during critical operations
- Fallback to polling for essential updates when WebSocket fails
- User notification of connection status changes

**Form Validation and User Input**
- Client-side validation with immediate feedback
- Server-side validation with detailed error responses
- Prevention of duplicate submissions during processing
- Clear indication of required fields and format requirements

### Backend Error Handling Enhancements

**Live Data Integration Errors**
- Fallback to cached data when external APIs are unavailable
- Configurable timeout and retry policies for external services
- Error classification (temporary vs permanent failures)
- Automated alerting for sustained service degradation

**Calculation Engine Error Handling**
- Confidence scoring for automated calculations
- Manual review queue for low-confidence results
- Rollback capability for incorrect automated decisions
- Comprehensive audit logging for all calculation attempts

**Database and Persistence Errors**
- Transaction rollback for failed multi-step operations
- Data consistency checks and repair mechanisms
- Backup and recovery procedures for critical data
- Performance monitoring and optimization alerts

## Testing Strategy

### Dual Testing Approach

The system will employ both unit testing and property-based testing to ensure comprehensive coverage and correctness validation.

**Unit Testing Framework**
- **Frontend**: Jest and React Testing Library for component testing
- **Backend**: pytest for FastAPI endpoint and service testing
- **Integration**: Cypress for end-to-end user workflow testing
- **WebSocket**: Custom test harnesses for real-time communication testing

**Property-Based Testing Framework**
- **Frontend**: fast-check for JavaScript/TypeScript property testing
- **Backend**: Hypothesis for Python property testing
- **Configuration**: Minimum 100 iterations per property test
- **Coverage**: Each correctness property implemented as a single property-based test

**Testing Requirements**
- All property-based tests must reference their corresponding design document property using the format: `**Feature: react-frontend-refactor, Property {number}: {property_text}**`
- Unit tests focus on specific examples, edge cases, and integration points
- Property tests verify universal properties across all valid inputs
- Both test types are complementary and required for comprehensive validation

**Live Data Testing Strategy**
- Mock external API responses for consistent testing
- Simulate various game states and outcomes
- Test calculation accuracy with known scenarios
- Validate WebSocket event handling under load

**Cross-Browser and Device Testing**
- Automated testing across major browsers (Chrome, Firefox, Safari, Edge)
- Mobile device testing on iOS and Safari
- Progressive Web App functionality validation
- Accessibility compliance testing (WCAG 2.1 AA)

### Performance Testing

**Load Testing**
- Concurrent user simulation for WebSocket connections
- Database performance under high wager volume
- API response time validation under load
- Memory usage monitoring for long-running sessions

**Real-Time Performance**
- WebSocket message delivery latency measurement
- Live data update propagation timing
- UI responsiveness during high-frequency updates
- Battery usage optimization for mobile PWA

## Implementation Phases

### Phase 1: Foundation and Core Migration (Weeks 1-4)
- Set up React application with TypeScript and build tooling
- Implement authentication and routing infrastructure
- Create core component library and design system
- Migrate basic wager display and management functionality
- Establish WebSocket connection framework

### Phase 2: Enhanced Backend and Live Integration (Weeks 5-8)
- Extend FastAPI with new live tracking endpoints
- Implement WebSocket server and event broadcasting
- Create live data polling and caching services
- Develop automated calculation engine
- Add comprehensive API documentation

### Phase 3: Advanced Features and Real-Time Capabilities (Weeks 9-12)
- Implement live odds tracking and display
- Add real-time score updates and game monitoring
- Create advanced analytics and visualization components
- Develop push notification system
- Implement Progressive Web App features

### Phase 4: Admin Tools and System Management (Weeks 13-16)
- Build comprehensive admin interface in React
- Implement bulk operations and batch processing
- Create system monitoring and health dashboards
- Add configuration management interfaces
- Develop audit trail and reporting features

### Phase 5: Testing, Optimization, and Deployment (Weeks 17-20)
- Comprehensive testing across all components
- Performance optimization and load testing
- Security audit and penetration testing
- Documentation completion and user training
- Production deployment and monitoring setup

## Technology Stack

### Frontend Technologies
- **React 18** with TypeScript for type safety and modern features
- **React Router v6** for client-side routing and navigation
- **React Query (TanStack Query)** for server state management and caching
- **Socket.IO Client** for WebSocket communication
- **Material-UI (MUI)** or **Tailwind CSS** for consistent styling
- **Chart.js** or **Recharts** for data visualization
- **React Hook Form** for form management and validation

### Backend Enhancements
- **FastAPI** (existing) with additional endpoints and WebSocket support
- **Socket.IO** for WebSocket server implementation
- **Celery** for background task processing
- **Redis** for caching and session management
- **SQLAlchemy** (existing) with enhanced models for live tracking
- **Alembic** (existing) for database migrations

### Infrastructure and Deployment
- **Docker** containers for consistent deployment
- **Docker Compose** for local development orchestration
- **Nginx** for reverse proxy and static file serving
- **PostgreSQL** (existing) with performance optimizations
- **GitHub Actions** for CI/CD pipeline
- **Monitoring**: Prometheus and Grafana for metrics collection

### External Integrations
- **ESPN API** (existing) with enhanced real-time capabilities
- **OpenAI API** (existing) for Discord bot image processing
- **Discord API** (existing) for bot functionality
- **Push Notification Services** for mobile and desktop notifications

## Security Considerations

### Authentication and Authorization
- JWT tokens for API authentication with refresh token rotation
- Role-based access control with granular permissions
- Session management with secure cookie handling
- Multi-factor authentication support for admin accounts

### Data Protection
- Input validation and sanitization on all user inputs
- SQL injection prevention through parameterized queries
- XSS protection through proper output encoding
- CSRF protection for state-changing operations

### API Security
- Rate limiting on all public endpoints
- API key management for external service access
- Request/response logging for audit trails
- Secure WebSocket authentication and authorization

### Infrastructure Security
- HTTPS enforcement for all communications
- Database encryption at rest and in transit
- Secure environment variable management
- Regular security updates and vulnerability scanning

This design provides a comprehensive foundation for transforming the existing betting tracker into a modern, real-time application while maintaining all current functionality and adding significant new capabilities for live sports tracking and automated outcome calculation.