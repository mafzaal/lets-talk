# Let's Talk Frontend

Modern web frontend for the Let's Talk AI chat system built with **Svelte 5**, **SvelteKit**, and **TailwindCSS 4**.

## Features

### 🎯 Dashboard
- **Execution History**: View recent pipeline executions with status indicators
- **System Analytics**: Monitor job success rates, execution times, and system health
- **Error Highlighting**: Visual indicators for failed jobs and system issues
- **Real-time Status**: Live system status indicators

### 🔧 Jobs Management
- **Job Listing**: View all configured pipeline jobs with detailed information
- **CRUD Operations**: Create, edit, and delete pipeline jobs
- **Execution Control**: Run pipelines on-demand with real-time status updates
- **History Tracking**: Detailed execution history for each job
- **Job Scheduling**: Support for cron, interval, and one-time job scheduling

### 📊 Analytics
- **Performance Metrics**: Track execution success rates and performance trends
- **Resource Usage**: Monitor CPU, memory, and disk usage
- **Visual Charts**: Interactive charts showing execution patterns over time
- **Trend Analysis**: Identify performance patterns and optimization opportunities

### 📋 Activity Feed
- **Real-time Activity**: Live feed of system activities and user interactions
- **Event Tracking**: Monitor job creations, executions, failures, and user logins
- **Historical Data**: Access to historical activity data with filtering options
- **User Attribution**: Track which users performed specific actions

### 💬 Chat Interface
- **AI Chat Widget**: Interactive chat interface for user queries
- **LangGraph Integration**: Powered by LangGraph for intelligent responses
- **Streaming Responses**: Real-time streaming of AI responses
- **Context Awareness**: Maintains conversation context across interactions

## Tech Stack

- **Frontend Framework**: Svelte 5 with SvelteKit
- **Styling**: TailwindCSS 4 with custom dark theme
- **Icons**: Lucide Svelte for consistent iconography
- **UI Components**: Custom component library with accessibility features
- **API Integration**: RESTful API client for backend communication
- **State Management**: Svelte's reactive state management

## Development

### Prerequisites
- Node.js 18+
- pnpm package manager

### Setup
```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview
```

### Code Quality
```bash
# Type checking
pnpm check

# Format code
pnpm format

# Lint code
pnpm lint
```

## API Integration

The frontend communicates with the FastAPI backend through a type-safe API client:

- **Health Monitoring**: `/health` endpoint for system status
- **Job Management**: `/scheduler/*` endpoints for CRUD operations
- **Pipeline Control**: `/pipeline/*` endpoints for execution control
- **Real-time Updates**: Polling-based updates for live data

## Architecture

### Layout Structure
```
src/
├── lib/
│   ├── components/
│   │   ├── ui/          # Reusable UI components
│   │   └── Layout.svelte # Main navigation layout
│   ├── api.ts           # API client and type definitions
│   └── utils.ts         # Utility functions
├── routes/
│   ├── dashboard/       # Dashboard page
│   ├── jobs/           # Jobs management page
│   ├── analytics/      # Analytics and performance page
│   ├── activity/       # Activity feed page
│   └── +layout.svelte  # Root layout
└── app.css             # Global styles and theme
```

## License

This project is licensed under the MIT License.
