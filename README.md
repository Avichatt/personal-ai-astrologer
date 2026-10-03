# Personal AI Astrologer — Backend & Intelligence Platform

A high-precision, API-first astrology intelligence platform combining Swiss Ephemeris astronomical calculations with Western, Vedic, and Krishnamurti Paddhati (KP) engines, chart persistence, transit tracking, event significance ranking, AI horoscope interpretations, and a full-featured interactive web application.

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
  - Geometric pattern recognition (*Grand Trine, T-Square, Grand Cross, Yod, Stellium, Mystic Rectangle*).
  - Secondary progressions (day-for-a-year) and progressed-to-natal aspect hits.
  - Natal synthesis with elemental and modality balance scoring and chart signatures.
- **Vedic Astrology Engine (Parashari Jyotish)**:
  - Sidereal Rashis with exaltation, debilitation, moolatrikona, and 5-fold friendships (*Panchadha Maitri*).
  - 27 Nakshatras & 108 Padas with lordships, deities, gunas, nadis, and Navamsha D9 sign calculation.
  - 12 Vedic Bhavas (*Kendras, Trikonas, Dusthanas, Upachayas, Marakas*) and 8 Jaimini Chara Karakas (*Atmakaraka* through *Darakaraka*).
  - Complete Parashara Drishti planetary aspects.
  - 120-year Vimshottari Dasha system (*Mahadasha -> Antardasha -> Pratyantardasha*) with date-based lookups.
  - Classical Yogas & Doshas (*Raja, Dhana, 5 Mahapurusha, Gajakesari, Budhaditya, Vipreet, Guru Chandal, Manglik Dosha*).
  - 8 Divisional Varga charts (*D1, D2, D3, D7, D9 Navamsha, D10 Dashamsha, D12, D60 Shashtiamsha*).
  - Vedic transits (*Gochar*, 7.5-year *Sade Sati* phases, and *Ashtama Shani*).
- **Krishnamurti Paddhati (KP System) Engine**:
  - 249 Sub-lord division tables with exact degree-minute boundaries.
  - Cuspal sub-lord analysis using Placidus houses paired with the Krishnamurti Ayanamsa.
  - 4-Fold Planetary & Cuspal Significator matrices (Levels 1 to 4: star lord occupancy, planet occupancy, star lord ownership, planet ownership).
  - Ruling Planets calculation (Ascendant sign & star lord, Moon sign & star lord, Day lord).
  - Cuspal house groupings for specific life events (Career 2,6,10,11; Marriage 2,7,11; Wealth 2,11; Health 1,5,11 vs 6,8,12; Foreign travel 3,9,12, etc.).
- **AI Astrological Interpretation & Life Blueprint Engine**:
  - Professional, structured horoscope analysis with Parashari deductions, house significations, and concrete timelines.
  - Focus areas: *General Life, Career & Ambition, Love & Relationships, Wealth & Finance, Health & Vitality, Spirituality & Moksha, and Life Blueprint*.
  - Full birth-to-death Life Blueprint structured into 5 chronological life stages (*0–18 Foundation, 18–30 Ascent & Discovery, 30–50 Peak Consolidation, 50–65 Mastery & Mentorship, 65+ Transcendent Wisdom*).
  - Authentic Vedic Gemstone prescriptions (gemstone, Sanskrit name, metal, finger, auspicious timing, and consecration mantras).
  - Spiritual remedies (*Vedic mantras, planetary charities, fasting protocols, and spiritual rituals*).
- **Interactive Full-Stack Web Application (SPA)**:
  - Clean, dark-mode glassmorphism interface served directly by FastAPI at `http://localhost:8000`.
  - Dynamic SVG chart renderers for Western 360° Wheel, South Indian Square, and North Indian Diamond charts.
  - Interactive tabs for Planets, Cusps, Dashas, Yogas, KP Sublords, KP Significators, Transits, and AI Life Blueprint.
- **Chart Persistence, Versioning & Snapshots**:
  - User-isolated chart storage supporting calculated snapshots, custom settings, and recalculation pipelines.
  - PostgreSQL / SQLite with SQLAlchemy 2.0 asyncpg/aiosqlite and Alembic migrations.
- **Transit Engine & Astro Events Framework**:
  - Mundane astronomical events (New/Full Moons, Solar/Lunar Eclipses, Retrograde stations, Ingresses, Cazimi).
  - Real-time transit hit calculation against user natal charts with 0–100 significance scoring (*Pinnacle, High, Moderate, Mild, Background*).

---

## Directory Layout

```
personal-ai-astrologer/
├── backend/
│   ├── alembic/                 # Database migrations
│   │   └── versions/            # Schema version scripts
│   ├── app/
│   │   ├── api/                 # FastAPI routes & dependencies
│   │   │   └── routes/          # auth, users, birth_profiles, charts, transits, events, analysis
│   │   ├── astro_events/        # Event detection, scoring & ranking engine
│   │   ├── astrology/           # Core astronomical & astrological engines
│   │   │   ├── ephemeris.py     # Swiss Ephemeris calculations
│   │   │   ├── timezone.py      # Timezone & DST resolution
│   │   │   ├── geocoding.py     # Geocoding providers
│   │   │   ├── kp/              # KP System: sublords, cusps, significators, natal
│   │   │   ├── vedic/           # Rashis, nakshatras, bhavas, dashas, yogas, vargas, transits
│   │   │   └── western/         # Houses, aspects, progressions, natal
│   │   ├── config/              # App settings, constants & logging
│   │   ├── database/            # SQLAlchemy async models & repositories
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── services/            # Business logic (AI interpretation, charts, geocoding, auth)
│   │   ├── utils/               # Security, JWT, rate limiting, request tracing
│   │   └── workers/             # Celery app & background tasks
│   ├── frontend/                # Interactive SPA frontend (HTML/CSS/JS, SVG charts)
│   │   ├── index.html           # Main application interface
│   │   ├── style.css            # Dark mode glassmorphic styling
│   │   ├── app.js               # Application logic, tabs, and API integration
│   │   └── chart-renderer.js    # SVG Western Wheel, South Indian & North Indian renderers
│   ├── tests/                   # Pytest suite with golden charts & random birth fuzzing
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── requirements-dev.txt
├── docker-compose.yml           # Multi-container local deployment
├── Dockerfile
├── .env.example
├── WALKTHROUGH.md               # Detailed architectural & operational guide
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+ (or Docker & Docker Compose)
- PostgreSQL (optional, SQLite supported for development out of the box)
- Redis (optional, for Celery background workers)

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
5. Start the local server:
   - **Using python module (Windows / macOS / Linux):**
     ```bash
     python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
     ```
   - **Or directly via uvicorn CLI:**
     ```bash
     uvicorn app.main:app --reload --port 8000
     ```

### Local Server Endpoints & Services

Once the server is running, the following local services and endpoints are available:

| Service / Interface | Localhost URL | Description |
| :--- | :--- | :--- |
| **Web UI Application (SPA)** | [http://localhost:8000](http://localhost:8000) | Interactive frontend for birth chart calculations, Western/Vedic wheels, KP analysis & transit timelines |
| **Interactive API Docs (Swagger UI)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger documentation to test and inspect all API endpoints |
| **ReDoc API Documentation** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Clean, readable OpenAPI specifications and schema models |
| **OpenAPI Specification** | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) | Raw OpenAPI 3.1 JSON schema |
| **Liveness Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Quick status check confirming application is running (`{"status":"ok"}`) |
| **Readiness Health Check** | [http://localhost:8000/health/ready](http://localhost:8000/health/ready) | Status probe confirming system is ready to accept traffic |

### Running with Docker Compose

```bash
docker compose up --build
```
Once started via Docker, the services are accessible on [http://localhost:8000](http://localhost:8000).

---

## Running Tests

Run the complete test suite (146 tests across all engines):

```bash
cd backend
python -m pytest -v
```

To run with coverage reporting:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

---

## API Reference

### Authentication & Users

| Method     | Endpoint                             | Description                                  |
| ---------- | ------------------------------------ | -------------------------------------------- |
| `POST`   | `/api/v1/auth/register`            | Register a new user account                  |
| `POST`   | `/api/v1/auth/login`               | Login and obtain JWT access & refresh tokens |
| `POST`   | `/api/v1/auth/logout`              | Invalidate current session                   |
| `GET`    | `/api/v1/users/me`                 | Fetch authenticated user profile             |
| `PATCH`  | `/api/v1/users/me`                 | Update authenticated user profile            |
| `POST`   | `/api/v1/users/me/change-password` | Update account password                      |
| `DELETE` | `/api/v1/users/me`                 | Delete user account                          |

### Birth Profiles

| Method     | Endpoint                        | Description                                                    |
| ---------- | ------------------------------- | -------------------------------------------------------------- |
| `POST`   | `/api/v1/birth-profiles`      | Create birth profile with auto-geocoding & timezone resolution |
| `GET`    | `/api/v1/birth-profiles`      | List authenticated user's birth profiles                       |
| `GET`    | `/api/v1/birth-profiles/{id}` | Get specific birth profile by ID                               |
| `PATCH`  | `/api/v1/birth-profiles/{id}` | Update birth profile                                           |
| `DELETE` | `/api/v1/birth-profiles/{id}` | Delete birth profile                                           |

### Natal Charts (Western, Vedic & KP)

| Method   | Endpoint                                  | Description                                             |
| -------- | ----------------------------------------- | ------------------------------------------------------- |
| `POST` | `/api/v1/charts/calculate`              | Calculate on-demand ephemeral chart without saving      |
| `POST` | `/api/v1/charts`                        | Calculate and persist a chart linked to a birth profile |
| `GET`  | `/api/v1/charts/{chart_id}`             | Retrieve a saved chart by ID                            |
| `GET`  | `/api/v1/charts/profile/{profile_id}`   | List all saved charts for a birth profile               |
| `POST` | `/api/v1/charts/{chart_id}/recalculate` | Recalculate chart with updated system settings          |

### Transits, Progressions & Astro Events

| Method   | Endpoint                          | Description                                                |
| -------- | --------------------------------- | ---------------------------------------------------------- |
| `POST` | `/api/v1/transits/current`      | Real-time snapshot of current planetary sky positions      |
| `POST` | `/api/v1/transits/profile`      | Real-time Western transits and Vedic Gochar for a profile  |
| `POST` | `/api/v1/transits/progressions` | Secondary progressions calculated for a given date         |
| `POST` | `/api/v1/events/upcoming`       | Global astronomical events ranked by significance (0–100) |
| `POST` | `/api/v1/events/personalized`   | Personalized transit hits against a birth profile          |

### AI Horoscope Interpretation & Life Blueprint

| Method   | Endpoint                          | Description                                                                              |
| -------- | --------------------------------- | ---------------------------------------------------------------------------------------- |
| `POST` | `/api/v1/analysis/horoscope`      | On-demand comprehensive horoscope interpretation with Parashari deductions & timelines   |
| `POST` | `/api/v1/analysis/profile`        | Horoscope analysis for a saved user birth profile                                        |
| `POST` | `/api/v1/analysis/life-blueprint` | Full Birth-to-Death Life Blueprint (5 life stages, yogas, gemstones, and remedies)       |
