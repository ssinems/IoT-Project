FROM python:3.7-slim
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python", "flask_stream.py"]
