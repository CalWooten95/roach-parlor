project-root/
├── docker-compose.yml
├── web/ # FastAPI app + templates
│ ├── Dockerfile
│ ├── app/
│ │ ├── __init__.py
│ │ ├── main.py # FastAPI entrypoint
│ │ ├── models.py # SQLAlchemy models
│ │ ├── schemas.py # Pydantic schemas
│ │ ├── database.py # DB session + engine
│ │ ├── crud.py # DB helper functions
│ │ ├── routers/
│ │ │ ├── __init__.py
│ │ │ ├── wagers.py # API routes for wagers
│ │ │ └── users.py # API routes for users
│ │ └── templates/
│ │ ├── base.html # shared layout
│ │ └── index.html # main dashboard
│ └── requirements.txt
│
├── bot/ # Discord bot container
│ ├── Dockerfile
│ ├── requirements.txt
│ └── main.py # Discord bot entrypoint
│
└── migrations/ # Alembic migration scripts



#### Postgres schema
users (
  id SERIAL PRIMARY KEY,
  discord_id TEXT UNIQUE,
  display_name TEXT,
  profile_pic_url TEXT
);

wagers (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  description TEXT,        -- parsed wager text or manual notes
  image_url TEXT,          -- original screenshot if you want to show it
  status TEXT CHECK (status IN ('open','won','lost','removed')) DEFAULT 'open',
  created_at TIMESTAMP DEFAULT now()
);