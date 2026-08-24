

flowchart LR

    ENV["📄 .env<br/><br/>POSTGRES_USER<br/>POSTGRES_PASSWORD<br/>POSTGRES_DB<br/>POSTGRES_HOST<br/>POSTGRES_PORT"]

    SETTINGS["⚙️ Settings<br/>Pydantic Settings"]

    USER["POSTGRES_USER"]
    PASS["POSTGRES_PASSWORD"]
    HOST["POSTGRES_HOST"]
    PORT["POSTGRES_PORT"]
    DB["POSTGRES_DB"]

    URL["🔗 DATABASE_URL<br/><br/>Combina la configuración"]

    RESULT["postgresql+psycopg://<br/>user:password@database:5432/aquaguard"]

    NEXT["🗄️ database.py<br/><br/>create_engine(<br/>settings.DATABASE_URL<br/>)"]

    DOCKER["🐳 Nota Docker<br/><br/>Dentro del backend:<br/>POSTGRES_HOST=database<br/><br/>NO localhost"]

    SECURITY["🔐 Seguridad<br/><br/>La contraseña viene del .env<br/>No imprimir DATABASE_URL completa<br/>No subir .env a Git"]

    RESPONSIBILITY["📌 config.py se encarga de:<br/><br/>✓ Leer configuración<br/>✓ Validar tipos<br/>✓ Construir DATABASE_URL<br/>✓ Exponer settings"]

    NOTDO["⛔ config.py NO hace:<br/><br/>✗ Crear Engine<br/>✗ Crear Sessions<br/>✗ Crear modelos<br/>✗ Crear tablas"]

    ENV --> SETTINGS

    SETTINGS --> USER
    SETTINGS --> PASS
    SETTINGS --> HOST
    SETTINGS --> PORT
    SETTINGS --> DB

    USER --> URL
    PASS --> URL
    HOST --> URL
    PORT --> URL
    DB --> URL

    URL --> RESULT
    RESULT --> NEXT

    HOST -.-> DOCKER
    PASS -.-> SECURITY

    SETTINGS -.-> RESPONSIBILITY
    SETTINGS -.-> NOTDO

    %% COLORES
    style ENV fill:#FFF3BF,stroke:#E0A800,stroke-width:2px,color:#222

    style SETTINGS fill:#D7EAFE,stroke:#1971C2,stroke-width:3px,color:#111

    style USER fill:#E5DBFF,stroke:#7048E8,color:#111
    style PASS fill:#E5DBFF,stroke:#7048E8,color:#111
    style HOST fill:#E5DBFF,stroke:#7048E8,color:#111
    style PORT fill:#E5DBFF,stroke:#7048E8,color:#111
    style DB fill:#E5DBFF,stroke:#7048E8,color:#111

    style URL fill:#D0EBFF,stroke:#1C7ED6,stroke-width:3px,color:#111
    style RESULT fill:#E5DBFF,stroke:#7048E8,stroke-width:2px,color:#111

    style NEXT fill:#D3F9D8,stroke:#2F9E44,stroke-width:3px,color:#111

    style DOCKER fill:#E7F5FF,stroke:#228BE6,color:#111
    style SECURITY fill:#FFE3E3,stroke:#E03131,color:#111
    style RESPONSIBILITY fill:#D3F9D8,stroke:#2F9E44,color:#111
    style NOTDO fill:#FFE3E3,stroke:#E03131,color:#111


El backend necesita saber dónde está PostgreSQL y con qué credenciales puede conectarse.

Después sigues visualmente:
El ```.env```  guarda los valores reales, despues en settings los lee y
validamos DATABASE_URL, juntamos estos valores en una dirección estándar, 
despues en  `database.py` se utilizará esa dirección para crear la conexión.

--- 