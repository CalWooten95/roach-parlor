# Roach Parlor Frontend

Modern React TypeScript frontend for the Roach Parlor Betting Tracker application.

## Features

- **React 18** with TypeScript for type safety
- **Vite** for fast development and building
- **Material-UI** for consistent UI components
- **React Router** for client-side navigation
- **React Query** for server state management
- **Socket.IO** for real-time updates
- **ESLint & Prettier** for code quality

## Getting Started

### Prerequisites

- Node.js 18+ and npm (or yarn)
- The FastAPI backend running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`.

### Available Scripts

- `npm run dev` - Start development server with hot reloading
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues automatically
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
src/
├── components/     # Reusable UI components
├── contexts/       # React contexts for state management
├── hooks/          # Custom React hooks
├── services/       # API and external service integrations
├── types/          # TypeScript type definitions
├── utils/          # Utility functions and constants
├── App.tsx         # Main application component
└── main.tsx        # Application entry point
```

## Development Guidelines

- Use TypeScript strict mode for better type safety
- Follow the established folder structure
- Use Material-UI components for consistency
- Implement proper error handling and loading states
- Write meaningful commit messages
- Test components and functionality thoroughly

## API Integration

The frontend communicates with the FastAPI backend through:

- **REST API** endpoints for CRUD operations
- **WebSocket** connections for real-time updates
- **Authentication** using JWT tokens

## Environment Variables

See `.env.example` for available configuration options.

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory, ready for deployment.