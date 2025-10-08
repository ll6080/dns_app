FROM python:3.11-slim
WORKDIR /app
COPY server.py /app/server.py
# precreate store file path
RUN touch /app/dns_store.txt
EXPOSE 53533/udp
CMD ["python", "server.py"]
