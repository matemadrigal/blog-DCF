# 🚀 Guía Completa de Deployment en Vercel

Esta guía te llevará paso a paso para deployar tu aplicación DCF Valuation Platform en Vercel y generar un enlace web funcional.

## 📋 Tabla de Contenidos

1. [Prerrequisitos](#prerrequisitos)
2. [Preparación del Proyecto](#preparación-del-proyecto)
3. [Opción 1: Deployment Solo del Frontend](#opción-1-deployment-solo-del-frontend-recomendado)
4. [Opción 2: Deployment Full Stack (Frontend + Backend)](#opción-2-deployment-full-stack)
5. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
6. [Dominio Personalizado](#dominio-personalizado)
7. [Troubleshooting](#troubleshooting)
8. [Monitoreo y Logs](#monitoreo-y-logs)

---

## Prerrequisitos

### 1. Cuenta en Vercel
- Ve a [vercel.com](https://vercel.com)
- Regístrate con GitHub, GitLab o Bitbucket (recomendado GitHub)
- Verifica tu email

### 2. Repositorio en GitHub
- Tu código debe estar en un repositorio de GitHub
- Asegúrate de que todos los cambios estén pusheados:

```bash
git add -A
git commit -m "Preparar para deployment en Vercel"
git push origin main
```

### 3. Verificar Estructura del Proyecto

Tu proyecto debe tener esta estructura:

```
blog-DCF/
├── frontend/              # ✅ Aplicación Next.js
│   ├── app/
│   ├── package.json
│   ├── next.config.js
│   └── .env.example
├── api/                   # ✅ Backend FastAPI
│   ├── main.py
│   └── routers/
├── src/                   # ✅ Lógica de negocio
├── vercel.json           # ✅ Configuración de Vercel
└── requirements-api.txt  # ✅ Dependencias Python
```

---

## Preparación del Proyecto

### 1. Actualizar .gitignore

Asegúrate de que `.gitignore` incluya:

```gitignore
# Environment variables
.env
.env.local
.env*.local

# Vercel
.vercel

# Next.js
frontend/.next/
frontend/out/
frontend/build/

# Python
__pycache__/
*.pyc
venv/

# Data
data/*.db
```

### 2. Crear .env.example para el Frontend

```bash
cd frontend
cat > .env.example << 'EOF'
# API URL - Actualizar con tu URL de producción del backend
NEXT_PUBLIC_API_URL=https://tu-backend-api.com
EOF
```

### 3. Push Final

```bash
git add -A
git commit -m "Configuración final para Vercel"
git push
```

---

## Opción 1: Deployment Solo del Frontend (Recomendado)

Esta es la opción más sencilla. Deployamos solo el frontend en Vercel y el backend en otro servicio.

### Paso 1: Deployar el Backend en Railway/Render

**Opción A: Railway (Recomendado)**

1. Ve a [railway.app](https://railway.app)
2. Conecta tu cuenta de GitHub
3. Click en "New Project" → "Deploy from GitHub repo"
4. Selecciona tu repositorio `blog-DCF`
5. Railway detectará automáticamente que es un proyecto Python

Configura las variables de entorno en Railway:
```bash
PYTHONUNBUFFERED=1
ENVIRONMENT=production
LOG_LEVEL=INFO

# API Keys (opcionales)
ALPHA_VANTAGE_API_KEY=tu_key
FMP_API_KEY=tu_key
```

6. Añade un comando de inicio en Railway:
```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

7. Railway te dará una URL como: `https://tu-proyecto.up.railway.app`
8. **Guarda esta URL** - la necesitarás para el frontend

**Opción B: Render**

1. Ve a [render.com](https://render.com)
2. New → Web Service
3. Conecta tu repositorio GitHub
4. Configuración:
   - **Name**: `dcf-backend`
   - **Environment**: Python 3.11
   - **Build Command**: `pip install -r requirements-api.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

5. Variables de entorno:
```
ENVIRONMENT=production
LOG_LEVEL=INFO
```

6. Click "Create Web Service"
7. Render te dará una URL como: `https://dcf-backend.onrender.com`

### Paso 2: Deployar el Frontend en Vercel

1. **Ve a [vercel.com/dashboard](https://vercel.com/dashboard)**

2. **Click en "Add New..." → "Project"**

3. **Importa tu repositorio de GitHub**
   - Busca `blog-DCF`
   - Click en "Import"

4. **Configura el proyecto:**

   **Framework Preset**: Next.js (auto-detectado)

   **Root Directory**: `frontend` ⚠️ **MUY IMPORTANTE**
   - Click en "Edit"
   - Selecciona `frontend`

   **Build Command**:
   ```bash
   npm run build
   ```

   **Output Directory**:
   ```bash
   .next
   ```

   **Install Command**:
   ```bash
   npm install
   ```

5. **Configura las Variables de Entorno:**

   Click en "Environment Variables" y añade:

   | Name | Value | Environment |
   |------|-------|-------------|
   | `NEXT_PUBLIC_API_URL` | `https://tu-backend.railway.app` | Production |
   | `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Development |

   ⚠️ **Reemplaza** `https://tu-backend.railway.app` con la URL real de tu backend (Railway o Render)

6. **Click en "Deploy"**

   Vercel comenzará a hacer el build. Esto toma 2-5 minutos.

7. **¡Listo!** 🎉

   Vercel te dará una URL como:
   ```
   https://dcf-valuation-platform.vercel.app
   ```

   También puedes ver:
   - Dashboard: `https://tu-app.vercel.app/dashboard`
   - Análisis: `https://tu-app.vercel.app/analysis`

---

## Opción 2: Deployment Full Stack

Si quieres deployar todo en Vercel (experimental):

### Paso 1: Configurar vercel.json

El archivo `vercel.json` ya está configurado, pero verifica:

```json
{
  "version": 2,
  "name": "dcf-valuation-platform",
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "installCommand": "cd frontend && npm install",
  "framework": "nextjs",
  "regions": ["iad1"]
}
```

### Paso 2: Deployar en Vercel

1. Sigue los mismos pasos de la Opción 1
2. **Root Directory**: Déjalo en raíz (no selecciones `frontend`)
3. Variables de entorno:
   ```
   NEXT_PUBLIC_API_URL=https://tu-proyecto.vercel.app/api
   ENVIRONMENT=production
   ```

⚠️ **Limitación**: El backend Python en Vercel Serverless Functions tiene limitaciones:
- Timeout de 10 segundos
- 50MB máximo de código
- No soporta todas las librerías Python

Por eso recomendamos la **Opción 1**.

---

## Configuración de Variables de Entorno

### En Vercel (Frontend)

1. Ve a tu proyecto en Vercel
2. Settings → Environment Variables
3. Añade estas variables:

```bash
# Requerido
NEXT_PUBLIC_API_URL=https://tu-backend-url.com

# Opcional (para analytics)
NEXT_PUBLIC_VERCEL_ENV=production
```

### En Railway/Render (Backend)

```bash
# Requerido
ENVIRONMENT=production
LOG_LEVEL=INFO

# Opcional - API Keys para datos premium
ALPHA_VANTAGE_API_KEY=your_key_here
FMP_API_KEY=your_key_here
IEX_CLOUD_API_KEY=your_key_here

# Base de datos (SQLite funciona bien)
# No necesitas configurar nada adicional
```

---

## Dominio Personalizado

### Opción 1: Usar Dominio de Vercel (Gratis)

Vercel te da automáticamente:
```
https://dcf-valuation-platform.vercel.app
```

Para cambiar el nombre:
1. Project Settings → Domains
2. Edita el dominio de Vercel

### Opción 2: Dominio Personalizado

Si tienes tu propio dominio (ej: `valuation.tudominio.com`):

1. **En Vercel:**
   - Ve a Settings → Domains
   - Click "Add"
   - Ingresa tu dominio: `valuation.tudominio.com`

2. **En tu proveedor de DNS (GoDaddy, Namecheap, Cloudflare, etc):**
   - Añade un registro CNAME:
     ```
     Type: CNAME
     Name: valuation (o @  para root)
     Value: cname.vercel-dns.com
     TTL: Automatic
     ```

3. **Espera 24-48 horas** para que se propague el DNS

4. Vercel automáticamente configura HTTPS con Let's Encrypt ✅

---

## Troubleshooting

### Error: "Module not found"

**Solución:**
```bash
# En tu repositorio local
cd frontend
rm -rf node_modules package-lock.json
npm install
git add package-lock.json
git commit -m "Update dependencies"
git push
```

Luego redeploy en Vercel: Deployments → Latest → Redeploy

### Error: "API request failed"

**Verifica:**

1. La URL del backend en variables de entorno:
   ```bash
   # En Vercel → Settings → Environment Variables
   NEXT_PUBLIC_API_URL=https://tu-backend.railway.app
   ```

2. CORS en el backend (api/main.py):
   ```python
   ALLOWED_ORIGINS = [
       "https://tu-app.vercel.app",
       "https://*.vercel.app",
   ]
   ```

3. El backend está corriendo:
   ```bash
   curl https://tu-backend.railway.app/api/health
   ```

### Error: "Build failed"

1. **Revisa los logs** en Vercel → Deployments → (click en el deployment fallido)

2. **Errores comunes:**

   **TypeScript errors:**
   ```bash
   # Añade a next.config.js
   typescript: {
     ignoreBuildErrors: true,
   },
   ```

   **ESLint errors:**
   ```bash
   # Añade a next.config.js
   eslint: {
     ignoreDuringBuilds: true,
   },
   ```

3. **Test local:**
   ```bash
   cd frontend
   npm run build
   ```

   Si falla localmente, arreglalo antes de deployar.

### Database no funciona

**Railway/Render**: La base de datos SQLite se guarda en el filesystem, que es efímero.

**Soluciones:**

1. **Railway** tiene volumes persistentes:
   - Settings → Volumes → Add Volume
   - Mount Path: `/app/data`

2. **PostgreSQL** (avanzado):
   - Usa Railway Postgres
   - Migra de SQLite a PostgreSQL

3. **Vercel KV** (para cache simple):
   - Storage → Create KV Database

---

## Monitoreo y Logs

### Ver Logs en Tiempo Real

**Vercel:**
```bash
vercel logs --follow
```

**Railway:**
- Dashboard → Tu servicio → Logs
- Logs en tiempo real con filtros

**Render:**
- Dashboard → Tu servicio → Logs
- Búsqueda de logs históricos

### Monitoreo de Performance

**Vercel Analytics** (Gratis):
1. Project → Analytics
2. Ver métricas de Web Vitals automáticamente

**Health Checks:**

Tu API tiene un endpoint de health:
```bash
curl https://tu-backend.railway.app/api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-11-28T...",
  "services": {
    "database": true,
    "cache": true
  }
}
```

### Configurar Uptime Monitoring

**UptimeRobot** (Gratis):
1. Regístrate en [uptimerobot.com](https://uptimerobot.com)
2. Add New Monitor
3. Type: HTTP(s)
4. URL: `https://tu-backend.railway.app/api/health`
5. Monitoring Interval: 5 minutes
6. Email alerts: Sí

---

## 🎉 Resumen: De 0 a Producción en 10 Minutos

### ⚡ Quick Start

```bash
# 1. Push tu código
git push

# 2. Deploy backend en Railway
# → Ir a railway.app
# → New Project → Deploy from GitHub
# → Comando: uvicorn api.main:app --host 0.0.0.0 --port $PORT
# → Guardar URL: https://tu-backend.railway.app

# 3. Deploy frontend en Vercel
# → Ir a vercel.com
# → Import GitHub repo
# → Root Directory: frontend
# → Environment Variable:
#    NEXT_PUBLIC_API_URL=https://tu-backend.railway.app
# → Deploy

# 4. ¡Listo! Tu URL:
# https://dcf-valuation-platform.vercel.app
```

### URLs Importantes

Después del deployment tendrás:

- **Frontend**: `https://tu-app.vercel.app`
- **Backend**: `https://tu-backend.railway.app`
- **API Docs**: `https://tu-backend.railway.app/api/docs`
- **Health Check**: `https://tu-backend.railway.app/api/health`

### Compartir tu Aplicación

Comparte este enlace con quien quieras:
```
https://dcf-valuation-platform.vercel.app
```

¡Cualquiera puede usarlo sin instalar nada! 🚀

---

## Soporte

**Problemas comunes:**
- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

**Errores específicos del proyecto:**
- Revisa los logs en Vercel/Railway
- Verifica las variables de entorno
- Prueba localmente primero con `npm run dev`

**¿Necesitas ayuda?**
1. Revisa esta guía de nuevo
2. Busca el error en los logs
3. Abre un issue en GitHub

---

## Checklist Final ✅

Antes de deployar, verifica:

- [ ] Código pusheado a GitHub
- [ ] `package.json` con scripts correctos en `frontend/`
- [ ] `requirements-api.txt` actualizado
- [ ] Variables de entorno configuradas
- [ ] `.gitignore` actualizado
- [ ] Build funciona localmente (`npm run build`)
- [ ] Backend funciona localmente (`uvicorn api.main:app`)
- [ ] Health check responde: `/api/health`

¡Ahora estás listo para deployar! 🚀
