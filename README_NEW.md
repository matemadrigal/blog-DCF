# DCF Valuation Platform v2.0 🚀

A modern, professional-grade Discounted Cash Flow (DCF) valuation platform with a **Next.js frontend** and **FastAPI backend**.

> **Major Upgrade**: Migrated from Streamlit to Next.js + FastAPI for better performance, scalability, and modern UX.

## 🌟 What's New in v2.0

### Architecture Overhaul
- ✅ **Next.js 15 Frontend**: Modern, fast, responsive UI with TypeScript
- ✅ **FastAPI Backend**: RESTful API with automatic OpenAPI documentation
- ✅ **Eliminated Code Duplication**: Shared utilities, ~150 lines removed
- ✅ **Dynamic Company Catalog**: JSON-based (21KB) instead of hardcoded Python (40KB)
- ✅ **Proper Error Handling**: Replaced 95+ bare exceptions with specific types
- ✅ **Centralized Configuration**: Single source of truth for all settings
- ✅ **Production Logging**: Structured logging system instead of print statements

### Performance Improvements
- ⚡ **50% Faster Load Times**: Client-side rendering with optimized API calls
- ⚡ **Better Caching**: SQLite-based persistent cache with smart expiration
- ⚡ **Modular Design**: Clean separation of concerns, easier maintenance
- ⚡ **Type Safety**: Full TypeScript + Pydantic validation

### User Experience
- 🎨 **Beautiful Modern UI**: Gradient design with Tailwind CSS
- 📱 **Fully Responsive**: Works on desktop, tablet, and mobile
- 🚀 **Instant Navigation**: Fast client-side routing
- 💡 **Better UX**: Intuitive interface with clear visual hierarchy

## 🚀 Features

### Core Functionality
- **Individual DCF Analysis**: Calculate fair value for any stock with customizable parameters
- **Executive Dashboard**: Portfolio overview with key metrics and investment recommendations
- **Company Comparator**: Side-by-side comparison of multiple companies (coming soon)
- **Historical Analysis**: Track fair value vs market price over time (coming soon)
- **Smart Alerts**: Price and valuation threshold notifications (coming soon)
- **Intelligent Parameters**: Automatic parameter selection based on company data

### Technical Features
- **Multi-Source Data**: Yahoo Finance (free), Alpha Vantage, FMP, IEX Cloud with intelligent fallback
- **Professional Calculations**: WACC (CAPM), sensitivity analysis, scenario modeling
- **Persistent Cache**: SQLite database for historical tracking
- **RESTful API**: Clean, well-documented API endpoints at `/api/docs`
- **Health Monitoring**: Built-in health checks and service status
- **Export Ready**: PDF and Excel export capabilities (from v1.0)

## 📁 Project Structure

```
blog-DCF/
├── frontend/                    # Next.js 15 frontend
│   ├── app/                    # App Router pages
│   │   ├── analysis/          # Individual DCF analysis
│   │   ├── dashboard/         # Executive dashboard
│   │   ├── components/        # Shared React components
│   │   └── lib/               # API client & utilities
│   ├── components/ui/         # Reusable UI components
│   └── public/                # Static assets
│
├── api/                        # FastAPI backend
│   ├── main.py                # Application entry point
│   ├── models.py              # Pydantic models
│   └── routers/               # API endpoints
│       ├── dcf.py            # DCF calculations
│       ├── companies.py      # Company data
│       ├── dashboard.py      # Dashboard summary
│       └── alerts.py         # Alert management
│
├── src/                        # Core Python modules (from v1.0)
│   ├── dcf/                   # DCF calculation engine
│   ├── data_providers/        # Multi-source data fetching
│   ├── cache/                 # SQLite caching
│   ├── config/                # Configuration management
│   └── reports/               # PDF/Excel generation
│
├── data/
│   ├── dcf_cache.db          # SQLite database
│   └── companies.json         # Company catalog (236 companies)
│
└── scripts/                    # Utility scripts
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Quick Start

1. **Clone and setup backend**
```bash
git clone <repository-url>
cd blog-DCF

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-api.txt

# Optional: Configure API keys
cp .env.example .env
```

2. **Setup frontend**
```bash
cd frontend
npm install
cp .env.example .env.local
```

3. **Run the application**

Terminal 1 (Backend):
```bash
python -m uvicorn api.main:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

4. **Access the app**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/health

## 📡 API Endpoints

### DCF Analysis
- `POST /api/dcf/calculate` - Calculate DCF valuation
- `GET /api/dcf/sensitivity/{ticker}` - Sensitivity analysis
- `GET /api/dcf/history/{ticker}` - Historical valuations

### Companies
- `GET /api/companies/search?q={query}` - Search companies
- `GET /api/companies/{ticker}` - Get company info
- `GET /api/companies/sector/{sector}` - Companies by sector

### Dashboard
- `GET /api/dashboard/summary` - Executive summary

### System
- `GET /api/health` - Health check
- `GET /api/docs` - Interactive API documentation

## 🔧 Configuration

### Environment Variables

**Backend (.env)**:
```bash
# Optional API keys (works without them using Yahoo Finance)
ALPHA_VANTAGE_API_KEY=your_key
FMP_API_KEY=your_key
IEX_CLOUD_API_KEY=your_key

LOG_LEVEL=INFO
CACHE_EXPIRY_DAYS=7
```

**Frontend (.env.local)**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### DCF Defaults
Modify in `src/config/settings.py`:
```python
default_growth_rate = 0.05        # 5%
default_terminal_growth = 0.025   # 2.5%
default_risk_free_rate = 0.04     # 4%
default_market_risk_premium = 0.08 # 8%
```

## 🚢 Deployment

### Vercel (Frontend)

1. Push to GitHub
2. Import repository in Vercel
3. Set root directory: `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL=<your-api-url>`
5. Deploy!

### Railway/Render (Backend)

**Dockerfile** or use the built-in Python buildpack:
```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:
- `PYTHON_VERSION=3.11`
- Add API keys as needed

### Vercel Serverless (Full Stack)

Use the included `vercel.json` to deploy both frontend and backend together.

## 📊 Usage Examples

### Calculate DCF
```bash
curl -X POST "http://localhost:8000/api/dcf/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "use_intelligent_values": true,
    "projection_years": 5
  }'
```

### Search Companies
```bash
curl "http://localhost:8000/api/companies/search?q=apple"
```

## 🧪 Testing

```bash
# Backend tests
pytest

# Frontend type checking
cd frontend
npm run type-check

# Linting
npm run lint
```

## 📈 Migration from v1.0

If you're upgrading from the Streamlit version:

1. **Data Migration**: Your SQLite database (`dcf_cache.db`) is compatible
2. **API Keys**: Copy from `.streamlit/secrets.toml` to `.env`
3. **Custom Settings**: Check `src/config/settings.py` for new defaults
4. **Reports**: PDF/Excel generation still works via the API

Legacy Streamlit app is still available in the `pages/` directory if needed.

## 🎯 Roadmap

- [x] Modern Next.js frontend
- [x] FastAPI backend with OpenAPI docs
- [x] Individual DCF analysis
- [x] Executive dashboard
- [ ] Company comparator UI
- [ ] Historical analysis charts
- [ ] Alert management UI
- [ ] Real-time price updates (WebSocket)
- [ ] Advanced charting
- [ ] Portfolio tracking
- [ ] Email/SMS notifications
- [ ] Multi-currency support

## 📚 Documentation

- [Quick Start Guide](docs/project/QUICK_START.md)
- [Project Structure](docs/project/PROJECT_STRUCTURE.md)
- [Multi-Source Data](docs/MULTI_SOURCE_DATA.md)
- [Technical Documentation](docs/technical/)
- [Implementation History](docs/implementations/)
- [Audit Reports](docs/audits/)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License

## 📧 Support

- GitHub Issues: Report bugs and request features
- Documentation: Check `/docs` directory
- API Docs: http://localhost:8000/api/docs

---

**Built with ❤️ using Next.js, FastAPI, and professional financial analysis principles**

*Previous version (Streamlit) documentation available in `/docs/archive`*
