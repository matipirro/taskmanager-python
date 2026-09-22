# 1. Imagen base: Python 3.14 slim (versión ligera, ~150 MB)
FROM python:3.14-slim

# 2. Directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copia requirements.txt primero (aprovechar caché de dependencias)
COPY requirements.txt .

# 4. Instala dependencias (build time — una sola vez por cambio en requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia el resto del código de la app
COPY . .

# 6. Documenta el puerto que la app usa (documentación, no abre nada por sí solo)
EXPOSE 8000

# 7. Comando que se ejecuta al arrancar el contenedor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]