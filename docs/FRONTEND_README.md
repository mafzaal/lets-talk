# Let's Talk Frontend Development Guide

This guide helps you set up and run the Let's Talk frontend for development and testing.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# From the root of the lets-talk repository
./start_frontend_dev.sh
```

This script will:
- Check all dependencies
- Start the mock backend API server
- Install frontend dependencies
- Start the frontend development server
- Display access URLs

### Option 2: Manual Setup

#### 1. Start the Backend API
```bash
# Start the mock backend server
uv run python /tmp/mock_backend.py
```

#### 2. Start the Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

## 📱 Accessing the Application

Once both servers are running:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Available Pages

- **Landing Page**: http://localhost:5173/ (auto-redirects to dashboard)
- **Dashboard**: http://localhost:5173/dashboard
- **Jobs Management**: http://localhost:5173/jobs
- **Analytics**: http://localhost:5173/analytics
- **Activity Feed**: http://localhost:5173/activity

## 🛠️ Development Features

### Mock Backend API
The mock backend provides realistic test data for all frontend features:
- Scheduler statistics
- Job management
- Pipeline reports
- Health monitoring
- CORS enabled for local development

### Frontend Features
- **Modern UI**: Built with Svelte 5 + SvelteKit
- **Dark Theme**: Professional dark theme with consistent styling
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Automatic data refresh
- **Error Handling**: Graceful error display and recovery

## 🧪 Testing

### Manual Testing
1. Visit each page and verify UI components load correctly
2. Check API calls in browser developer tools
3. Test navigation between pages
4. Verify responsive design on different screen sizes

### API Testing
```bash
# Test backend health
curl http://localhost:8000/health

# Test scheduler status
curl http://localhost:8000/scheduler/status

# Test jobs endpoint
curl http://localhost:8000/scheduler/jobs
```

## 🔧 Development Commands

### Frontend Commands
```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview

# Type checking
pnpm check

# Format code
pnpm format
```

### Backend Commands
```bash
# Start mock backend
uv run python /tmp/mock_backend.py

# Start actual backend (requires configuration)
uv run uvicorn backend.lets_talk.main:app --host 0.0.0.0 --port 8000
```

## 🎨 UI Components

The frontend uses a custom UI component library built with:
- **Tailwind CSS 4**: Modern utility-first CSS framework
- **Lucide Icons**: Consistent icon library
- **Custom Components**: Reusable UI components in `src/lib/components/ui/`

### Available Components
- `Card`: Container component for content sections
- `Button`: Styled button with multiple variants
- `Layout`: Main application layout with sidebar navigation

## 📊 Data Flow

1. **Frontend** (SvelteKit) runs on port 5173
2. **Backend API** (FastAPI) runs on port 8000
3. Frontend makes HTTP requests to backend API
4. Backend returns JSON responses with mock data
5. Frontend displays data in the UI

## 🐛 Troubleshooting

### Common Issues

**Blank Page**
- Ensure both backend and frontend servers are running
- Check browser console for JavaScript errors
- Verify API endpoints are accessible

**API Errors**
- Check backend server is running on port 8000
- Verify CORS is properly configured
- Check network tab in browser developer tools

**Build Errors**
- Ensure all dependencies are installed: `pnpm install`
- Check TypeScript errors: `pnpm check`
- Verify Node.js version (18+)

### Log Files
When using the automated setup script, logs are saved to:
- Backend: `/tmp/backend.log`
- Frontend: `/tmp/frontend.log`

## 🔄 Making Changes

### Adding New Pages
1. Create new route in `src/routes/`
2. Update navigation in `src/lib/components/Layout.svelte`
3. Add corresponding backend endpoints if needed

### Styling Changes
- Modify `src/app.css` for global styles
- Update Tailwind configuration if needed
- Use existing utility classes for consistency

### API Changes
- Update `src/lib/api.ts` for new endpoints
- Modify mock backend to match new API structure
- Update TypeScript interfaces as needed

## 📚 Resources

- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Lucide Icons](https://lucide.dev/)

## 🤝 Contributing

1. Make changes to the frontend code
2. Test locally using the development setup
3. Ensure all pages work correctly
4. Submit pull request with description of changes

---

**Note**: This setup uses a mock backend for development. For production deployment, you'll need to configure the actual backend with proper API keys and database connections.