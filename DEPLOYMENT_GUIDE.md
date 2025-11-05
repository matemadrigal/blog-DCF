# 🚀 Guía de Deployment - DCF Valuation Platform

**Objetivo:** Hacer tu aplicación accesible 24/7 para todo el mundo

---

## 📋 OPCIONES DE DEPLOYMENT

### **Comparación Rápida**

| Plataforma | Precio | Facilidad | Always-On | Tiempo Deploy | Recomendado |
|------------|--------|-----------|-----------|---------------|-------------|
| **Streamlit Cloud** | Gratis | ⭐⭐⭐⭐⭐ | ✅ Sí | 5 min | ✅ **Principiantes** |
| **Render** | Gratis/$7 | ⭐⭐⭐⭐ | ⚠️ Sleep/Sí | 10 min | ✅ **Recomendado** |
| **Railway** | $5/mes | ⭐⭐⭐⭐⭐ | ✅ Sí | 5 min | ✅ **Mejor calidad/precio** |
| **Heroku** | $7/mes | ⭐⭐⭐⭐ | ✅ Sí | 15 min | ⚠️ Más caro |
| **Google Cloud Run** | ~$2/mes | ⭐⭐⭐ | ✅ Sí | 20 min | 💡 Avanzado |

---

## 🎯 OPCIÓN 1: STREAMLIT COMMUNITY CLOUD (RECOMENDADO)

### **✅ Ventajas:**
- **100% Gratis** para siempre
- **Deploy en 5 minutos**
- **HTTPS automático**
- **Auto-redeploy desde GitHub**
- **URL limpia:** `https://tu-usuario-dcf.streamlit.app`
- **No requiere tarjeta de crédito**

### **📝 Pasos Detallados:**

#### **1. Preparar GitHub Repository**

Si tu repo no es público, hazlo público o asegúrate de que Streamlit Cloud tenga acceso.

```bash
# Asegúrate de tener todo commiteado
git status

# Si hay cambios sin commit
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

#### **2. Crear archivo de configuración Streamlit**

Crea `.streamlit/config.toml`:

```bash
mkdir -p .streamlit
```

Luego crea el archivo `.streamlit/config.toml` con este contenido:

```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

#### **3. Deploy en Streamlit Cloud**

1. **Ir a:** https://share.streamlit.io

2. **Login** con tu cuenta GitHub

3. **Click "New app"**

4. **Configurar:**
   ```
   Repository: tu-usuario/blog-DCF
   Branch: main
   Main file path: app.py
   ```

5. **Advanced settings (opcional):**
   ```
   Python version: 3.12
   Secrets: (si necesitas API keys)
   ```

6. **Click "Deploy"**

7. **Esperar 2-3 minutos** mientras se instalan dependencias

8. **¡Listo!** Tu app estará en:
   ```
   https://tu-usuario-blog-dcf.streamlit.app
   ```

#### **4. (Opcional) Configurar Secrets**

Si usas API keys (por ejemplo, Alpha Vantage), agrégalas en Streamlit Cloud:

1. En tu app → "Settings" → "Secrets"
2. Agregar:
   ```toml
   ALPHA_VANTAGE_API_KEY = "tu-api-key"
   ```

#### **5. Auto-Redeploy**

Cada vez que hagas `git push`, Streamlit Cloud automáticamente:
- Detecta cambios
- Reconstruye la app
- Redeploy en ~2 minutos

---

## 🎯 OPCIÓN 2: RENDER (GRATIS CON SLEEP / $7 ALWAYS-ON)

### **✅ Ventajas:**
- Gratis tier generoso
- Muy confiable
- Fácil configuración
- HTTPS automático

### **⚠️ Limitaciones (Free Tier):**
- App "duerme" después de 15 min sin uso
- Tarda ~30-50 segundos en "despertar"
- 750 horas gratis/mes (suficiente para 24/7 con poco tráfico)

### **📝 Pasos:**

#### **1. Crear cuenta en Render**

https://render.com → Sign up (gratis)

#### **2. Crear Web Service**

1. Click "New +" → "Web Service"
2. Conectar tu repositorio GitHub
3. Seleccionar `blog-DCF`

#### **3. Configurar:**

```
Name: dcf-valuation
Region: Oregon (US West) o el más cercano
Branch: main
Runtime: Python 3

Build Command:
pip install -r requirements.txt

Start Command:
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

#### **4. Environment Variables (opcional):**

Si usas API keys:
```
ALPHA_VANTAGE_API_KEY = tu-key
```

#### **5. Plan:**

- **Free:** $0/mes (con sleep)
- **Starter:** $7/mes (always-on, sin sleep)

#### **6. Deploy**

Click "Create Web Service" → Esperar 5-10 minutos

**URL:** `https://dcf-valuation.onrender.com`

---

## 🎯 OPCIÓN 3: RAILWAY ($5/mes - MEJOR RELACIÓN CALIDAD/PRECIO)

### **✅ Ventajas:**
- **$5/mes** (muy económico)
- **Always-on** (no sleep)
- **Deploy automático** desde GitHub
- **Muy rápido** (SSD + CDN)
- **500 horas gratis/mes** con GitHub Student Pack

### **📝 Pasos:**

#### **1. Crear cuenta en Railway**

https://railway.app → Login con GitHub

#### **2. New Project**

1. Click "New Project"
2. "Deploy from GitHub repo"
3. Seleccionar `blog-DCF`

#### **3. Configurar (Railway detecta Streamlit automáticamente)**

Railway automáticamente:
- Detecta `requirements.txt`
- Instala dependencias
- Detecta Streamlit
- Configura el comando correcto

Si necesitas personalizar, agregar en `railway.toml`:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"
```

#### **4. Environment Variables (opcional):**

En "Variables" tab:
```
ALPHA_VANTAGE_API_KEY=tu-key
```

#### **5. Deploy**

Automático! En 3-5 minutos estará listo.

**URL:** `https://blog-dcf-production.up.railway.app`

#### **6. Custom Domain (opcional):**

Railway te permite usar tu propio dominio (ej: `dcf.tudominio.com`)

---

## 🎯 OPCIÓN 4: GOOGLE CLOUD RUN (PAY-AS-YOU-GO)

### **✅ Ventajas:**
- Solo pagas por uso real (~$1-3/mes con bajo tráfico)
- Escala automáticamente
- Infraestructura Google

### **📝 Pasos (Avanzado):**

#### **1. Instalar Google Cloud CLI**

```bash
# Linux/WSL
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

#### **2. Crear Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD streamlit run app.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true
```

#### **3. Crear .dockerignore**

```
__pycache__
*.pyc
.git
.venv
venv/
.pytest_cache
.streamlit/secrets.toml
```

#### **4. Deploy**

```bash
# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Deploy
gcloud run deploy dcf-valuation \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**URL:** `https://dcf-valuation-xxxxx-uc.a.run.app`

---

## 📊 COMPARACIÓN DE COSTOS

### **Escenario: App con 100 visitas/día**

| Plataforma | Costo Mensual | Uptime | Performance |
|------------|---------------|--------|-------------|
| **Streamlit Cloud** | $0 | 99.9% | ⭐⭐⭐⭐ |
| **Render Free** | $0 | 99% (con sleep) | ⭐⭐⭐ |
| **Render Starter** | $7 | 99.9% | ⭐⭐⭐⭐ |
| **Railway** | $5 | 99.9% | ⭐⭐⭐⭐⭐ |
| **Google Cloud Run** | ~$2 | 99.95% | ⭐⭐⭐⭐⭐ |

---

## 🔧 PREPARACIÓN FINAL

### **Checklist antes de Deploy:**

#### **1. Verificar requirements.txt**

```bash
# Asegúrate de que tiene todas las dependencias
cat requirements.txt
```

Debería incluir:
```
streamlit>=1.37
pandas>=2.2
numpy>=2.0
yfinance>=0.2
plotly>=5.24
matplotlib>=3.9
requests>=2.32
scipy>=1.13
openpyxl>=3.1
reportlab>=4.0
```

#### **2. Crear .gitignore**

```bash
# Archivo .gitignore
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/
.streamlit/secrets.toml
*.log
.DS_Store
output/
outputs/
.pre-commit-cache/
```

#### **3. Probar localmente**

```bash
# Activar entorno virtual
source .venv/bin/activate

# Correr app
streamlit run app.py

# Verificar que funciona en http://localhost:8501
```

#### **4. Commit y Push**

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

---

## 🌐 CUSTOM DOMAIN (Opcional)

### **Para cualquier plataforma:**

1. **Comprar dominio** (ej: Namecheap, Google Domains)
   - Costo: ~$10-15/año

2. **Configurar DNS:**

Para Streamlit Cloud:
```
CNAME: dcf.tudominio.com → tu-app.streamlit.app
```

Para Render/Railway:
```
CNAME: dcf.tudominio.com → dcf-valuation.onrender.com
```

3. **Agregar en plataforma:**
   - Ir a settings → Custom Domain
   - Agregar `dcf.tudominio.com`
   - Esperar propagación DNS (1-48 horas)

---

## 🔒 SEGURIDAD

### **Secrets Management:**

**NUNCA** hacer commit de:
- API keys
- Passwords
- Tokens

**Usar variables de entorno:**

`.streamlit/secrets.toml` (local, en .gitignore):
```toml
ALPHA_VANTAGE_API_KEY = "tu-key-local"
```

En código:
```python
import streamlit as st

# Lee de secrets (funciona local y en cloud)
api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", "default-key")
```

---

## 📈 MONITOREO

### **Streamlit Cloud:**
- Dashboard incluido
- Logs en tiempo real
- Métricas de uso

### **Render/Railway:**
- Logs en dashboard
- Métricas CPU/RAM
- Alertas de downtime

### **Google Analytics (opcional):**

Agregar en `app.py`:
```python
# Google Analytics tracking
import streamlit.components.v1 as components

# Agregar tu tracking code
ga_code = """
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
"""

components.html(ga_code, height=0)
```

---

## 🎯 MI RECOMENDACIÓN FINAL

### **Para ti (blog-DCF), recomiendo:**

#### **Opción A: Gratis (Empezar)**
→ **Streamlit Community Cloud**
- Gratis para siempre
- Deploy en 5 minutos
- URL: `https://tu-usuario-blog-dcf.streamlit.app`

#### **Opción B: Profesional ($5/mes)**
→ **Railway**
- Always-on
- Muy rápido
- Fácil de usar
- Mejor relación calidad/precio

#### **Opción C: Enterprise (si escala mucho)**
→ **Google Cloud Run**
- Paga solo por uso
- Escala automáticamente
- Infraestructura Google

---

## 📞 SIGUIENTES PASOS

### **1. Decide tu plataforma** (recomiendo Streamlit Cloud para empezar)

### **2. Sigue la guía específica** de arriba

### **3. Comparte tu URL** cuando esté listo! 🎉

---

## 🆘 TROUBLESHOOTING

### **Error: "Module not found"**
→ Asegúrate de que todas las dependencias están en `requirements.txt`

### **Error: "Port already in use"**
→ No especifiques puerto, usa `$PORT` variable

### **Error: "Memory limit exceeded"**
→ Usa plan paid o optimiza memoria (libera variables grandes)

### **App muy lenta**
→ Usa `@st.cache_data` para cachear datos pesados

### **Deploy falla**
→ Revisa logs en la plataforma (siempre muestran error exacto)

---

## 📚 RECURSOS

- **Streamlit Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **Render Docs:** https://render.com/docs
- **Railway Docs:** https://docs.railway.app
- **Streamlit Forum:** https://discuss.streamlit.io

---

**¿Listo para deploy? ¡Yo te ayudo con cualquier paso! 🚀**
