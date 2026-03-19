FROM python:3.12-slim

WORKDIR /decoder

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY milesight-decoder.py .

CMD ["python", "milesight-decoder.py"]