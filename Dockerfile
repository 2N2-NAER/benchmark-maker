FROM python:3.12-slim
WORKDIR /app
COPY benchmark_maker ./benchmark_maker
COPY run_mcp.py ./
RUN useradd --create-home app
USER app
ENTRYPOINT ["python", "-m", "benchmark_maker"]
CMD ["--help"]
