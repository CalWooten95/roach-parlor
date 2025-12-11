# Getting Started with Roach Parlor

This guide will help you set up and run the Roach Parlor Betting Tracker locally using Docker.

## Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git**

### Installing Docker

#### Windows
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Run the installer and follow the setup wizard
3. Restart your computer when prompted

#### macOS
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Drag Docker to Applications folder
3. Launch Docker from Applications

#### Linux (Ubuntu/Debian)
```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install docker.io docker-compose

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
```

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd roach-parlor
```

### 2. Run Setup Script
```bash
# On Linux/macOS
./setup.sh

# On Windows (Git Bash or WSL)
bash setup.sh
```

The setup script will:
- Check for Docker installation
- Create environment files from templates
- Build Docker containers
- Provide next steps

### 3. Configure Environment Variables

Edit the `.env` file created by the setup script:

```bash
# Required: Set a secure database password
POSTGRES_PASSWORD=your_secure_password_here

# Required: Generate a random session secret
SESSION_SECRET=your_random_session_secret_here

# Required: Set admin credentials
ADMIN_PASSWORD=your_admin_password_here
ADMIN_ACCESS_KEY=your_random_access_key_here

# Optional: Discord bot configuration (if using Discord integration)
DISCORD_TOKEN=your_discord_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
TARGET_CHANNEL=your_discord_channel_id_here
```

### 4. Start Development Environment
```bash
# Start all services with hot reloading
./start-dev.sh
```

### 5. Access the Application

Once started, you can access:

- **Frontend (React)**: http://localhost:3000
- **Backend (FastAPI)**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (PostgreSQL)

## Development Workflow

### Starting Services
```bash
# Development mode (with hot reloading)
./start-dev.sh

# Production mode
./start-prod.sh
```

### Stopping Services
```bash
./stop.sh
```

### Viewing Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f frontend-dev
docker-compose -f docker-compose.dev.yml logs -f web
docker-compose -f docker-compose.dev.yml logs -f bot
```

### Rebuilding Containers
```bash
# Rebuild all containers
docker-compose -f docker-compose.dev.yml build

# Rebuild specific service
docker-compose -f docker-compose.dev.yml build frontend-dev
```

## Project Structure

```
roach-parlor/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── hooks/          # Custom React hooks
│   │   └── types/          # TypeScript types
│   ├── Dockerfile          # Production build
│   └── Dockerfile.dev      # Development build
├── web/                     # FastAPI backend
├── bot/                     # Discord bot
├── docker-compose.yml       # Production compose
├── docker-compose.dev.yml   # Development compose
└── .env                     # Environment variables
```

## Available Features

### ✅ Completed (Task 4)
- **Wager Display**: Modern React components for displaying wagers
- **Wager Management**: Create, update, archive, and delete wagers
- **Filtering & Search**: Advanced filtering and search capabilities
- **Bulk Operations**: Select and manage multiple wagers at once
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: WebSocket integration for live updates

### 🚧 In Progress (Future Tasks)
- Live sports data integration
- Automated win/loss calculation
- Progressive Web App features
- Push notifications
- Advanced analytics and charts

## Testing the Wager Functionality

1. **Navigate to Wagers Page**: http://localhost:3000/wagers
2. **Create Test Wagers**: Use the "New Wager" button (placeholder for now)
3. **Filter Wagers**: Use the search and filter controls
4. **Update Status**: Click "Update Status" on any wager card
5. **Bulk Operations**: Enable bulk actions and select multiple wagers

## Troubleshooting

### Port Conflicts
If you get port conflicts, you can modify the ports in `docker-compose.dev.yml`:
```yaml
ports:
  - "3001:3000"  # Change 3000 to 3001
```

### Database Connection Issues
1. Ensure PostgreSQL container is running:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```
2. Check database logs:
   ```bash
   docker-compose -f docker-compose.dev.yml logs db
   ```

### Frontend Build Issues
1. Clear Docker cache:
   ```bash
   docker system prune -a
   ```
2. Rebuild frontend:
   ```bash
   docker-compose -f docker-compose.dev.yml build frontend-dev
   ```

### Permission Issues (Linux/macOS)
```bash
# Make scripts executable
chmod +x *.sh

# Fix Docker permissions
sudo chown -R $USER:$USER .
```

## Next Steps

1. **Explore the Wagers Page**: Test the new wager management interface
2. **Review the Code**: Check out the React components in `frontend/src/components/wagers/`
3. **Run Tests**: Execute the test suite to verify functionality
4. **Continue Development**: Move on to the next tasks in the implementation plan

## Getting Help

- **Documentation**: Check the README files in each component directory
- **API Docs**: Visit http://localhost:8000/docs for backend API documentation
- **Logs**: Use `docker-compose logs` to debug issues
- **Issues**: Create GitHub issues for bugs or feature requests

## Development Tips

- **Hot Reloading**: The development setup includes hot reloading for both frontend and backend
- **Database Persistence**: Database data persists between container restarts
- **Environment Variables**: Changes to `.env` require container restart
- **Code Changes**: Frontend changes are reflected immediately, backend changes may require restart

Happy coding! 🚀