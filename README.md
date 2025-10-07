# blog-DCF

Instrucciones mínimas para configurar y ejecutar el proyecto.

Requisitos
- Python 3.11/3.12
- Git

Pasos (Linux, usando el terminal integrado de VS Code)

1. Abrir el proyecto en VS Code y abrir el terminal integrado (Ctrl+`).

2. Crear y activar un entorno virtual (si no existe):

```bash
cd /home/mateo/blog-DCF
python3 -m venv .venv
source .venv/bin/activate
```

3. Actualizar pip y herramientas de empaquetado:

```bash
python -m pip install --upgrade pip setuptools wheel
```

4. Instalar dependencias:

```bash
pip install -r requirements.txt
```

5. Seleccionar el intérprete del proyecto en VS Code (Ctrl+Shift+P → Python: Select Interpreter) y elegir `/.venv/bin/python`.

6. Ejecutar la app Streamlit desde la tarea de VS Code (Tasks → Run Task → "Streamlit: Run app.py") o desde el terminal:

```bash
source .venv/bin/activate
streamlit run app.py
```

Notas
- Si no puedes crear virtualenv por falta de paquetes del sistema en Debian/Ubuntu, instala:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
```

- Si usas Conda/pyenv: crea y activa tu entorno y luego ejecuta `pip install -r requirements.txt`.

