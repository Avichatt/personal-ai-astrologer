# Personal AI Astrologer — Backend Platform

A high-precision, API-first astrology intelligence backend combining Swiss Ephemeris astronomical calculations with Western and Vedic engines, chart persistence, transit tracking, and event significance ranking.

---

## Architecture & Capabilities

- **Clean Architecture & Separation of Concerns**: Multi-tier architecture cleanly separating API presentation (routers & Pydantic v2 schemas), application services, domain astrological engines, and database repositories.
- **Deterministic Astronomical Core (`pyswisseph`)**:
  - High-precision planetary ephemeris (DE431 precision) across Tropical & Sidereal zodiacs.
  - 40+ Ayanamsas (*Lahiri / Chitrapaksha, Krishnamurti / KP, Raman, Fagan-Bradley, True Chitra*, etc.).
  - House systems: *Placidus, Whole Sign, Equal, Koch, Regiomontanus, Campanus, Porphyry*.
- **Historical Timezone & Geocoding Engine**: Resolves historical daylight saving time (DST) and UTC offsets using `zoneinfo` and `timezonefinder`, coupled with an OpenStreetMap Nominatim geocoding provider.
- **Western Astrology Engine**:
  - House cusps, traditional & modern house rulers, and house occupancy.
  - Major/minor aspect engine with configurable orbs, applying vs. separating velocity vectors.
  - Geometric pattern recognition (*Grand Trine, T-Square, Grand Cross, Yod, Stellium*).
  - Secondary progressions (day-for-a-year) and progressed-to-natal aspect hits.
  - Natal synthesis with elemental and modality balance scoring and chart signatures.
- **Vedic Astrology Engine**:
  - Sidereal Rashis with exaltation, debilitation, moolatrikona, and 5-fold friendships (*Panchadha Maitri*).
  - 27 Nakshatras & 108 Padas with lordships, deities, gunas, nadis, and Navamsha D9 sign calculation.
  - 12 Vedic Bhavas (*Kendras, Trikonas, Dusthanas, Upachayas, Marakas*) and 8 Jaimini Chara Karakas (*Atmakaraka* through *Darakaraka*).
  - Complete Parashara Drishti planetary aspects.
  - 120-year Vimshottari Dasha system (*Mahadasha -> Antardasha -> Pratyantardasha*) with date-based lookups.
  - Classical Yogas & Doshas (*Raja, Dhana, 5 Mahapurusha, Gajakesari, Budhaditya, Vipreet, Guru Chandal, Manglik Dosha*).
  - 8 Divisional Varga charts (*D1, D2, D3, D7, D9 Navamsha, D10 Dashamsha, D12, D60 Shashtiamsha*).
  - Vedic transits (*Gochar*, 7.5-year *Sade Sati* phases, and *Ashtama Shani*).
- **Chart Persistence, Versioning & Snapshots**:
  - User-isolated chart storage supporting calculated snapshots, custom settings, and recalculation pipelines.
- **Transit Engine & Astro Events Framework**:
  - Mundane astronomical events (New/Full Moons, Solar/Lunar Eclipses, Retrograde stations, Ingresses, Cazimi).
  - Real-time transit hit calculation against user natal charts with 0–100 significance scoring (*Pinnacle, High, Moderate, Mild, Background*).
- **Modern Asynchronous Stack**: FastAPI, SQLAlchemy 2.0 (asyncpg / aiosqlite), Pydantic v2, Redis, Celery workers, and JWT authentication.

---

## Directory Layout

```
personal-ai-astrologer/
├── backend/
│   ├── alembic/                 # Database migrations
│   │   └── versions/            # Schema version scripts
│   ├── app/
│   │   ├── api/                 # FastAPI routes & dependencies
│   │   │   └── routes/          # auth, users, birth_profiles, charts, transits, events
│   │   ├── astro_events/        # Event detection, scoring & ranking engine
│   │   ├── astrology/           # Core astronomical & astrological engines
│   │   │   ├── ephemeris.py     # Swiss Ephemeris calculations
│   │   │   ├── timezone.py      # Timezone & DST resolution
│   │   │   ├── geocoding.py     # Geocoding providers
│   │   │   ├── western/         # Houses, aspects, progressions, natal
│   │   │   └── vedic/           # Rashis, nakshatras, bhavas, dashas, yogas, vargas, transits
│   │   ├── config/              # App settings, constants & logging
│   │   ├── database/            # SQLAlchemy async models & repositories
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── services/            # Business application logic
│   │   ├── utils/               # Security, JWT, rate limiting, request tracing
│   │   └── workers/             # Celery app & background tasks
│   ├── tests/                   # Pytest suite with golden reference charts
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── requirements-dev.txt
├── docker-compose.yml           # Multi-container local deployment
├── Dockerfile
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.12+ (or Docker & Docker Compose)
- PostgreSQL (optional for local SQLite testing)
- Redis (for Celery background workers)

### Running Locally

1. Navigate to backend:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment configuration:
   ```bash
   cp ../.env.example .env
   ```
5. Start development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Access interactive API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - Healthcheck: `http://localhost:8000/health`

### Running with Docker Compose

```bash
docker compose up --build
```

---

## Running Tests

Run the complete test suite (55 tests across all engines):

```bash
cd backend
pytest -v
```

To run with coverage reporting:
```bash
pytest --cov=app --cov-report=term-missing
```

---

## API Reference (Phases 1–7)

### Authentication & Users
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user account |
| `POST` | `/api/v1/auth/login` | Login and obtain JWT access & refresh tokens |
| `POST` | `/api/v1/auth/logout` | Invalidate current session |
| `GET` | `/api/v1/users/me` | Fetch authenticated user profile |
| `PATCH` | `/api/v1/users/me` | Update authenticated user profile |
| `POST` | `/api/v1/users/me/change-password` | Update account password |
| `DELETE` | `/api/v1/users/me` | Delete user account |

### Birth Profiles
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/birth-profiles` | Create birth profile with auto-geocoding & timezone resolution |
| `GET` | `/api/v1/birth-profiles` | List authenticated user's birth profiles |
| `GET` | `/api/v1/birth-profiles/{id}` | Get specific birth profile by ID |
| `PATCH` | `/api/v1/birth-profiles/{id}` | Update birth profile |
| `DELETE` | `/api/v1/birth-profiles/{id}` | Delete birth profile |

### Natal Charts (Western & Vedic)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/charts/calculate` | Calculate on-demand ephemeral chart without saving |
| `POST` | `/api/v1/charts` | Calculate and persist a chart linked to a birth profile |
| `GET` | `/api/v1/charts/{chart_id}` | Retrieve a saved chart by ID |
| `GET` | `/api/v1/charts/profile/{profile_id}` | List all saved charts for a birth profile |
| `POST` | `/api/v1/charts/{chart_id}/recalculate` | Recalculate chart with updated system settings |

### Transits, Progressions & Astro Events
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/transits/current` | Real-time snapshot of current planetary sky positions |
| `POST` | `/api/v1/transits/profile` | Real-time Western transits and Vedic Gochar for a profile |
| `POST` | `/api/v1/transits/progressions` | Secondary progressions calculated for a given date |
| `POST` | `/api/v1/events/upcoming` | Global astronomical events ranked by significance (0–100) |
| `POST` | `/api/v1/events/personalized` | Personalized transit hits against a birth profile |
