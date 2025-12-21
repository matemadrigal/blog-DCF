# GitHub Pages - DCF Valuation Reports

Esta carpeta contiene la configuración para GitHub Pages, que permite publicar y compartir reportes DCF en línea.

## 🌐 URL de Publicación

Una vez configurado GitHub Pages, tus reportes estarán disponibles en:

```
https://matemadrigal.github.io/blog-DCF/
```

## 📁 Estructura de Archivos

```
docs/
├── index.html              # Página principal con listado de reportes
├── reports/                # Carpeta con todos los PDFs
│   ├── DCF_Report_PFE.pdf
│   ├── DCF_Report_SNY.pdf
│   └── ...
├── _config.yml            # Configuración de Jekyll (opcional)
└── README_GITHUB_PAGES.md # Esta guía
```

## 🚀 Cómo Activar GitHub Pages

### Paso 1: Configurar en GitHub

1. Ve a tu repositorio en GitHub: `https://github.com/matemadrigal/blog-DCF`
2. Haz clic en **Settings** (Configuración)
3. En el menú lateral, haz clic en **Pages**
4. En **Source**, selecciona:
   - **Branch**: `main` (o el branch que uses)
   - **Folder**: `/docs`
5. Haz clic en **Save**

### Paso 2: Esperar el Deploy

- GitHub comenzará a construir tu sitio automáticamente
- El proceso toma ~1-2 minutos
- Una vez completado, verás un mensaje verde con la URL de tu sitio

### Paso 3: Verificar

Visita la URL proporcionada (algo como `https://matemadrigal.github.io/blog-DCF/`) y deberías ver tu página con todos los reportes DCF.

## 📄 Cómo Agregar Nuevos PDFs

### Método 1: Línea de comandos (Recomendado)

```bash
# 1. Copiar el PDF a la carpeta de reportes
cp "tu_nuevo_reporte.pdf" docs/reports/

# 2. Editar index.html para agregar el nuevo reporte
# Abre docs/index.html y agrega una entrada en el array 'reports':

{
    ticker: 'AAPL',
    company: 'Apple Inc.',
    filename: 'DCF_Report_AAPL_2024.pdf',
    sector: 'Technology / Consumer Electronics',
    date: 'Q4 2024',
    size: '500 KB'
}

# 3. Commit y push
git add docs/reports/tu_nuevo_reporte.pdf docs/index.html
git commit -m "Add DCF report for AAPL"
git push
```

### Método 2: Interfaz Web de GitHub

1. Ve a tu repositorio en GitHub
2. Navega a `docs/reports/`
3. Haz clic en **Add file** → **Upload files**
4. Arrastra tu PDF
5. Haz commit
6. Edita `docs/index.html` desde GitHub para agregar la entrada del reporte

## 🔗 Compartir Enlaces Directos

### Enlace a un PDF específico:

```
https://matemadrigal.github.io/blog-DCF/reports/DCF_Report_PFE.pdf
```

### Enlace a la página principal:

```
https://matemadrigal.github.io/blog-DCF/
```

## 🎨 Personalizar la Página

### Cambiar Colores

Edita `docs/index.html` y modifica el CSS:

```css
/* Cambiar gradiente de fondo */
background: linear-gradient(135deg, #TU_COLOR_1 0%, #TU_COLOR_2 100%);

/* Cambiar color de botones */
.btn-primary {
    background: #TU_COLOR;
}
```

### Agregar Logo o Descripción

Edita la sección `<header>` en `docs/index.html`:

```html
<header>
    <img src="tu-logo.png" alt="Logo" style="max-width: 200px; margin-bottom: 20px;">
    <h1>📊 Tu Título Personalizado</h1>
    <p>Tu descripción personalizada</p>
</header>
```

## 📊 Plantilla para Nuevos Reportes

Cuando agregues un nuevo reporte al `index.html`, usa esta plantilla:

```javascript
{
    ticker: 'TICKER',           // Símbolo bursátil (ej: AAPL, MSFT)
    company: 'Nombre Completo', // Nombre de la empresa
    filename: 'nombre_archivo.pdf', // Nombre exacto del archivo PDF
    sector: 'Sector / Industria',   // Sector e industria
    date: 'Q1 2024',            // Fecha del análisis
    size: 'XXX KB'              // Tamaño del archivo
}
```

## 🔒 Permisos y Seguridad

- Los PDFs serán **públicos** y accesibles por cualquiera con el enlace
- Si necesitas controlar el acceso, considera:
  - Usar un repositorio privado (requiere GitHub Pro)
  - Usar servicios de almacenamiento con autenticación (S3, Azure Blob)
  - Implementar autenticación en el sitio

## 🆘 Troubleshooting

### El sitio no se actualiza

1. Verifica que los cambios estén en el branch correcto
2. Ve a **Actions** en GitHub para ver el estado del deploy
3. Espera 1-2 minutos después del push
4. Limpia la caché del navegador (Ctrl+Shift+R)

### El PDF no se muestra

1. Verifica que el nombre del archivo en `index.html` sea **exactamente** igual al archivo real
2. Asegúrate de que el PDF esté en `docs/reports/`
3. Los nombres de archivo con espacios o caracteres especiales pueden causar problemas - usa guiones bajos o guiones

### Error 404

- Verifica que la configuración de GitHub Pages apunte a `/docs`
- Asegúrate de que `index.html` exista en la raíz de `docs/`

## 📝 Ejemplo Completo

### Agregar reporte de Tesla (TSLA)

```bash
# 1. Generar el reporte (desde tu app DCF)
python app.py  # Genera DCF_Report_TSLA_2024.pdf

# 2. Mover a docs/reports
cp DCF_Report_TSLA_2024.pdf docs/reports/

# 3. Editar docs/index.html
# Agregar en el array 'reports':
{
    ticker: 'TSLA',
    company: 'Tesla, Inc.',
    filename: 'DCF_Report_TSLA_2024.pdf',
    sector: 'Automotive / Electric Vehicles',
    date: 'December 2024',
    size: '520 KB'
}

# 4. Commit y push
git add docs/reports/DCF_Report_TSLA_2024.pdf docs/index.html
git commit -m "Add Tesla DCF valuation report (Dec 2024)"
git push

# 5. Esperar ~1-2 minutos y visitar:
# https://matemadrigal.github.io/blog-DCF/
```

## 🎯 Mejoras Futuras

Ideas para expandir tu GitHub Pages:

- [ ] Agregar búsqueda/filtrado de reportes
- [ ] Implementar categorías por sector
- [ ] Mostrar métricas clave (P/E, EV/EBITDA) en las cards
- [ ] Agregar gráficos de valoración con Chart.js
- [ ] Crear un blog con análisis técnicos
- [ ] Implementar comparador de empresas
- [ ] Agregar RSS feed para nuevos reportes

## 📚 Recursos

- [Documentación oficial de GitHub Pages](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [GitHub Pages Custom Domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)

---

**¿Necesitas ayuda?** Abre un issue en el repositorio o consulta la documentación oficial de GitHub Pages.
