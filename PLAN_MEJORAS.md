# Plan de Mejoras - BimBamIA v2

## Visión General

Transformar el proyecto actual (Streamlit monolítico) en una arquitectura modular profesional separada en 3 capas: Frontend (Astro), Backend API (FastAPI + LangGraph), y Base de Datos (Supabase). El objetivo es crear una **base reutilizable** donde solo cambien documentos, prompts y modelo de LLM para adaptarlo a cualquier negocio.

---

## Viabilidad en Capas Gratuitas

### Stack Completo - Análisis de Free Tiers (2026)

| Servicio | Free Tier | Limitación Principal | ¿Sirve? |
|----------|-----------|---------------------|---------|
| **Netlify** (Frontend) | 300 créditos/mes, ~15 GB bandwidth | ~20 deploys/mes | ✅ Sí |
| **Supabase** (DB + Auth) | 500 MB DB, 50K MAUs, 1 GB storage | Pausa tras 1 semana sin actividad | ✅ Con workaround |
| **Cohere** (LLM + Embeddings) | Free tier disponible | Rate limits | ✅ Sí |
| **Backend** (ver abajo) | Varia según plataforma | Varia | ✅ Múltiples opciones |

### Veredicto: **Sí es viable en capas gratuitas**

El stack completo funciona gratis. La clave es elegir la plataforma de backend correcta según el caso de uso (portfolio vs producción).

### Workaround para Supabase (pausa por inactividad)

Crear un GitHub Action que haga ping cada 3 días:

```yaml
# .github/workflows/keep-alive.yml
name: Keep Supabase Alive
on:
  schedule:
    - cron: "0 8 */3 * *"
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Supabase
        run: |
          curl -s "${{ secrets.SUPABASE_URL }}/rest/v1/" \
            -H "apikey: ${{ secrets.SUPABASE_ANON_KEY }}" \
            -o /dev/null
```

---

## Arquitectura Objetivo

```
┌──────────────────────────────────────────────────────────┐
│                     FRONTEND (Astro)                     │
│                  Netlify + TypeScript                    │
│                   CSS Modules + pnpm                     │
├──────────────────────────────────────────────────────────┤
│                    ↓ API REST (HTTPS) ↓                  │
├──────────────────────────────────────────────────────────┤
│               BACKEND (FastAPI + Docker)                  │
│         Google Cloud Run / Render / VPS                  │
│         LangGraph + Cohere + ChromaDB                    │
├──────────────────────────────────────────────────────────┤
│                    ↓ Supabase SDK ↓                      │
├──────────────────────────────────────────────────────────┤
│              BASE DE DATOS (Supabase)                    │
│         PostgreSQL + Auth + Row Level Security           │
└──────────────────────────────────────────────────────────┘
```

### Flujo de una conversación

1. Usuario escribe pregunta en el chat (Astro)
2. Astro envía `POST /api/chat` a FastAPI con el JWT de Supabase
3. FastAPI valida el JWT, clasifica intención (LangGraph)
4. Si DOCUMENT → busca en ChromaDB → genera respuesta con Cohere
5. FastAPI guarda la conversación en Supabase (con user_id)
6. FastAPI retorna la respuesta al frontend
7. Astro muestra la respuesta y actualiza el historial

---

## Fases de Implementación

### Fase 1: Backend API con FastAPI (3-4 horas)

Crear una API REST que envuelva el grafo LangGraph actual.

**Archivos a crear:**

```
backend/
├── main.py                 # FastAPI app
├── config.py               # Configuración (ya existe, adaptar)
├── requirements.txt        # Dependencias backend
├── Dockerfile              # Para despliegue en Render
├── .dockerignore
├── api/
│   ├── __init__.py
│   ├── routes.py           # Endpoints /api/chat, /api/history
│   └── deps.py             # Dependencias (auth, DB)
├── graph/                  # Mover del proyecto actual
│   ├── __init__.py
│   ├── builder.py
│   ├── state.py
│   ├── nodes.py
│   └── edges.py
├── agents/                 # Mover del proyecto actual
│   ├── __init__.py
│   ├── document_agent.py
│   └── prompts.py
├── rag/                    # Mover del proyecto actual
│   ├── __init__.py
│   ├── loader.py
│   ├── embeddings.py
│   └── vectorstore.py
├── tools/
│   ├── __init__.py
│   └── search_tools.py
└── docs/                   # PDFs
```

**Endpoints:**

```python
# POST /api/chat
# Body: { "message": "¿Cuál es el plazo para devolver?" }
# Headers: Authorization: Bearer <supabase_jwt>
# Response: { "response": "...", "intent": "DOCUMENT", "conversation_id": "..." }

# GET /api/history
# Headers: Authorization: Bearer <supabase_jwt>
# Response: { "conversations": [...] }

# GET /api/health
# Response: { "status": "ok", "vectorstore_chunks": 108 }
```

**Dependencias:**

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
langchain==0.3.0
langchain-cohere==0.3.0
langgraph==0.2.0
chromadb==0.5.0
python-dotenv==1.0.0
supabase==2.0.0
pydantic==2.0.0
```

**Dockerfile:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-build vectorstore at startup
CMD ["sh", "-c", "python -c 'from rag.vectorstore import create_vectorstore; create_vectorstore()' && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

**Consideraciones:**
- El vectorstore se reconstruye al iniciar el contenedor (~20-30s)
- ChromaDB es local al contenedor (se pierde al reiniciar, se reconstruye)
- FastAPI sirve en el `$PORT` que define la plataforma de despliegue

---

### Fase 2: Supabase - Auth + Historial (2-3 horas)

**Configurar en Supabase Dashboard:**

1. **Auth**: Habilitar email/password + Google OAuth (opcional)
2. **Tablas:**

```sql
-- Conversaciones
CREATE TABLE conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  title TEXT
);

-- Mensajes
CREATE TABLE messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  intent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Políticas: cada usuario solo ve sus conversaciones
CREATE POLICY "Users can view own conversations"
  ON conversations FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversations"
  ON conversations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own messages"
  ON messages FOR SELECT
  USING (
    conversation_id IN (
      SELECT id FROM conversations WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert own messages"
  ON messages FOR INSERT
  WITH CHECK (
    conversation_id IN (
      SELECT id FROM conversations WHERE user_id = auth.uid()
    )
  );
```

**Tablas para configuración (multi-tenancy):**

```sql
-- Configuración del chatbot (para personalización)
CREATE TABLE bot_config (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  bot_name TEXT DEFAULT 'BimBamIA',
  welcome_message TEXT,
  system_prompt TEXT,
  llm_model TEXT DEFAULT 'command-a-03-2025',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### Fase 3: Frontend Astro (4-5 horas)

**Setup inicial:**

```bash
pnpm create astro@latest bimbam-frontend
cd bimbam-frontend
pnpm add @supabase/supabase-js @supabase/ssr
```

**Estructura:**

```
frontend/
├── astro.config.mjs
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── .env.example
├── src/
│   ├── layouts/
│   │   └── Layout.astro          # Layout base con meta tags
│   ├── pages/
│   │   ├── index.astro           # Landing page
│   │   ├── login.astro           # Página de login
│   │   ├── signup.astro          # Página de registro
│   │   ├── dashboard.astro       # Chat principal (protegido)
│   │   └── auth/
│   │       └── callback.astro    # Callback de OAuth
│   ├── components/
│   │   ├── Header.astro          # Navegación
│   │   ├── ChatWindow.astro      # Ventana de chat (isla React)
│   │   ├── MessageBubble.astro   # Burbuja de mensaje
│   │   ├── SuggestedQuestions.astro  # Preguntas sugeridas
│   │   ├── LoginForm.astro       # Formulario de login
│   │   └── Sidebar.astro         # Historial de conversaciones
│   ├── islands/
│   │   └── Chat.tsx              # Componente interactivo del chat
│   ├── lib/
│   │   ├── supabase.ts           # Cliente Supabase
│   │   └── api.ts                # Funciones para llamar al backend
│   ├── styles/
│   │   ├── global.css            # Estilos globales
│   │   ├── variables.css         # CSS custom properties
│   │   └── components/
│   │       ├── chat.module.css
│   │       ├── header.module.css
│   │       └── sidebar.module.css
│   └── middleware.ts              # Auth middleware
└── public/
    └── favicon.svg
```

**Configuración de Astro:**

```typescript
// astro.config.mjs
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import node from '@astrojs/node';

export default defineConfig({
  output: 'server',
  adapter: node({
    mode: 'standalone'
  }),
  integrations: [react()],
});
```

**Ejemplo de componente Chat (isla React):**

```typescript
// src/islands/Chat.tsx
import { useState, useEffect, useRef } from 'react';
import styles from '../styles/components/chat.module.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
}

export default function Chat({ conversationId }: { conversationId?: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user' as const, content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${import.meta.env.PUBLIC_API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await getSupabaseToken()}`
        },
        body: JSON.stringify({
          message: input,
          conversation_id: conversationId
        })
      });

      const data = await res.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        intent: data.intent
      }]);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.chatContainer}>
      <div className={styles.messages}>
        {messages.map((msg, i) => (
          <div key={i} className={`${styles.bubble} ${styles[msg.role]}`}>
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className={styles.inputArea}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Escribí tu pregunta..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? '...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
}
```

**Estilos con CSS Modules:**

```css
/* src/styles/components/chat.module.css */
.chatContainer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: linear-gradient(45deg, #1a1a2e, #16213e, #0f3460);
  border-radius: 12px;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.bubble {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
  line-height: 1.5;
}

.user {
  background: #667eea;
  color: white;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}

.assistant {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-bottom-left-radius: 4px;
}

.inputArea {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
}

.inputArea input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  background: white;
  font-size: 1rem;
}

.inputArea button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  background: #667eea;
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.inputArea button:hover {
  background: #5a6fd6;
}

.inputArea button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
```

---

### Fase 4: Despliegue (1-2 horas)

#### Frontend en Netlify

1. Push del código a GitHub
2. Conectar repo en Netlify
3. Configurar:
   - **Build command**: `pnpm build`
   - **Publish directory**: `dist`
   - **Node version**: 20
4. Variables de entorno en Netlify:
   ```
   PUBLIC_API_URL=https://tu-backend-url
   PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
   PUBLIC_SUPABASE_ANON_KEY=tu-anon-key
   ```

#### Backend - Elige una plataforma (ver comparación abajo)

#### Supabase

1. Crear proyecto en supabase.com
2. Ejecutar las migraciones SQL (tablas + RLS)
3. Habilitar Auth (email/password)
4. Configurar Site URL en Authentication → URL Configuration

---

## Despliegue del Backend: Guía Completa por Plataforma

### Opción 1: Google Cloud Run (Recomendada para Portfolio)

**Por qué:** 2M requests/mes gratis, Docker nativo, cold starts de solo 2-5 segundos, sin límite de tiempo.

**Setup:**

```bash
# Instalar gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Crear proyecto
gcloud projects create bimbam-ia --name="BimBamIA"
gcloud config set project bimbam-ia

# Habilitar Cloud Run
gcloud services enable run.googleapis.com

# Build y deploy
gcloud run deploy bimbam-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2
```

**Variables de entorno:**
```bash
gcloud run services update bimbam-api \
  --update-env-vars COHERE_API_KEY=tu-key,SUPABASE_URL=tu-url,SUPABASE_SERVICE_KEY=tu-key
```

**Limites gratis:**
- 2M requests/mes
- 180,000 vCPU-seconds/mes
- 360,000 GiB-seconds/mes
- Sin límite de tiempo
- Cold start: 2-5 segundos

**Costo después del free tier:** ~$0.000024/vCPU-second

---

### Opción 2: Render (Para portfolios simples)

**Advertencia importante:** Render tiene 3 limitaciones críticas:
1. **Cold start 30-60s** tras 15 min de inactividad
2. **PostgreSQL gratis se borra a los 30 días** (no usar para datos persistentes)
3. **750 horas/mes** — si se agotan, suspenden servicios

**Setup:**
1. Push del código a GitHub
2. Conectar repo en Render → "New Web Service"
3. Configurar:
   - **Runtime**: Docker
   - **Port**: $PORT (variable de entorno de Render)
   - **Instance Type**: Free
4. Variables de entorno en Render:
   ```
   COHERE_API_KEY=tu-api-key
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_SERVICE_KEY=tu-service-key
   PORT=8000
   ```

**Cuándo usar:** Solo para demos rápidas donde el cold start no importa.

---

### Opción 3: Railway (Mejor DX, pago desde el inicio)

**Costo:** $5 de crédito de trial + $1/mes después. No es gratis indefinidamente.

**Setup:**
1. Conectar repo en railway.app
2. Railway detecta Docker automáticamente
3. Variables de entorno en el dashboard
4. Deploy automático

**Ventaja:** Sin cold starts, DX excelente, PostgreSQL/Redis incluido.

**Cuándo usar:** Cuando podés gastar $1-5/mes y querés la mejor experiencia de desarrollo.

---

### Opción 4: VPS Hetzner (Para producción/venta a negocios)

**Costo:** ~$4/mes (CX22: 2 vCPU, 4 GB RAM, 40 GB SSD)

**Setup:**

```bash
# Crear VPS en hetzner.com/cloud
# Instalar Docker
ssh root@tu-ip
curl -fsSL https://get.docker.com | sh

# Clonar repo
git clone https://github.com/tu-usuario/bimbam-backend.git
cd bimbam-backend

# Crear .env
cp .env.example .env
nano .env  # Configurar variables

# Levantar con Docker Compose
docker compose up -d
```

**Ventaja:** Control total, siempre activo, sin restricciones, sin cold starts.

**Cuándo usar:** Para vender a negocios donde necesitás confiabilidad y control.

---

### Opción 5: Oracle Cloud Always Free (Más potencia gratis)

**Gratis siempre:** 4 OCPUs ARM, 24 GB RAM, 200 GB storage.

**Setup:**
1. Crear cuenta en cloud.oracle.com (requiere tarjeta)
2. Crear instancia VM (Ubuntu/ARM)
3. Instalar Docker y desplegar

**Advertencia:** Setup más complejo, interfaz menos amigable. Pero es la opción gratuita más potente.

---

## Comparación: ¿Dónde desplegar el backend?

### Para Portfolio / Demo

| Plataforma | Costo | Cold Start | Siempre activo | Complejidad | Recomendación |
|------------|-------|------------|----------------|-------------|---------------|
| **Google Cloud Run** | Gratis (2M req) | 2-5s | Scale-to-zero | Baja | ⭐ **Mejor opción** |
| **Render** | Gratis | 30-60s | No (tras 15 min) | Baja | Aceptable si el cold start no importa |
| **Oracle Cloud Always Free** | Gratis | No | Siempre activo | Alta | Si necesitás mucha potencia |

### Para Producción / Venta a Negocios

| Plataforma | Costo | Cold Start | Siempre activo | Complejidad | Recomendación |
|------------|-------|------------|----------------|-------------|---------------|
| **VPS Hetzner** | ~$4/mes | No | Siempre activo | Media | ⭐ **Mejor relación costo-control** |
| **Railway** | $5 trial + $1/mes | No | Siempre activo | Baja | Si querés la mejor DX |
| **Render Starter** | $7/mes | No | Siempre activo | Baja | Si ya estás en Render |
| **Google Cloud Run** | Desde $0 (scales) | 2-5s | Scale-to-zero | Baja | Si el tráfico es variable |

### Tabla Resumen de Todas las Opciones

| Plataforma | Gratis siempre | Sin cold start | Docker | Credit card | Sin límite tiempo | Ideal para |
|------------|---------------|----------------|--------|-------------|-------------------|------------|
| **Google Cloud Run** | ✅ 2M req/mes | ✅ 2-5s | ✅ Nativo | Sí | ✅ | Portfolio |
| **Render** | ✅ 750 hrs/mes | ❌ 30-60s | ✅ | No | ✅ | Demo rápida |
| **Railway** | ⚠️ $5 trial | ✅ | ✅ | No | ✅ | Prototipos |
| **Oracle Cloud Always Free** | ✅ 4 OCPUs + 24GB | ✅ | ✅ | Sí | ✅ | Potencia máxima |
| **Koyeb** | ✅ 1 servicio | ✅ Sin sleep | ✅ | No | ✅ | APIs simples |
| **VPS Hetzner** | ❌ $4/mes | ✅ | ✅ | Sí | ✅ | Producción |
| **Fly.io** | ⚠️ Solo trial | ✅ | ✅ | Sí | ✅ | Edge global |

---

### Fase 5: Customización para Multi-Tenancy (2-3 horas)

Para usar este proyecto como **base para otros negocios**, crear un sistema de configuración:

**Archivo de configuración por negocio:**

```yaml
# config/bimbambuy.yaml
bot:
  name: "BimBamIA"
  welcome_message: "¡Hola! Soy el asistente de BimBam Buy."
  theme:
    primary_color: "#667eea"
    gradient: "linear-gradient(45deg, #1a1a2e, #16213e, #0f3460)"

documents:
  - docs/reembolsos-devoluciones.pdf
  - docs/programa-afiliados.pdf
  - docs/guia-envios.pdf
  - docs/faq-metodos-pago.pdf
  - docs/manual-garantia.pdf

prompts:
  intent_router: "Eres un clasificador de intenciones..."
  document_agent: "Eres un agente de soporte..."
  general_response: "Eres un asistente general..."
  response_formatter: "Formatea la respuesta..."

llm:
  model: "command-a-03-2025"
  temperature: 0

embeddings:
  model: "embed-v4.0"
```

**Para personalizar:**
1. Cambiar los PDFs en `docs/`
2. Editar los prompts en `config/prompts/`
3. Cambiar el modelo en `config/bimbambuy.yaml`
4. Ajustar colores/UI en el frontend

---

## Docker Local (desarrollo)

Para probar todo localmente con Docker:

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "4321:4321"
    environment:
      - PUBLIC_API_URL=http://localhost:8000
      - PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - COHERE_API_KEY=${COHERE_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - PORT=8000
    volumes:
      - ./backend/docs:/app/docs  # Para cambiar PDFs sin rebuild
```

---

## Resumen de Tiempo Estimado

| Fase | Tiempo | Dependencias |
|------|--------|-------------|
| 1. Backend FastAPI | 3-4h | Ninguna |
| 2. Supabase Auth + DB | 2-3h | Fase 1 |
| 3. Frontend Astro | 4-5h | Fase 1 + 2 |
| 4. Despliegue | 1-2h | Fases 1-3 |
| 5. Multi-tenancy config | 2-3h | Fases 1-4 |
| **Total** | **12-17h** | |

---

## ¿Qué cambia respecto al proyecto actual?

| Aspecto | Actual (v1) | Mejorado (v2) |
|---------|-------------|---------------|
| Frontend | Streamlit | Astro + TypeScript |
| Backend | Integrado en Streamlit | FastAPI independiente + Docker |
| Auth | Ninguna | Supabase Auth (email + OAuth) |
| Historial | SQLite efímero | Supabase PostgreSQL persistente |
| UI | Básica | Moderna, CSS Modules, responsive |
| Customización | Manual | Config YAML por negocio |
| Despliegue | Streamlit Cloud | Netlify + Cloud Run/Render/VPS |
| Escalabilidad | Limitada | Backend separado, API REST |
| Portfolio value | Alto | Muy alto |

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Cold start (si elegís Render) | Medio | Usar Google Cloud Run (2-5s) o VPS (sin cold start) |
| Supabase pausa tras 7 días | Bajo | GitHub Action keep-alive cada 3 días |
| Límites de Cohere free tier | Bajo | Monitorizar uso; upgrade si escala |
| Complejidad de mantener 2 repos | Medio | Monorepo o carpetas separadas en un repo |
| Render borra DB a los 30 días | Alto | Usar Supabase para DB (no Render Postgres) |
