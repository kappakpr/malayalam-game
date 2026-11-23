docker run --rm \
  -v "$(pwd)":/app \
  -w /app \
  python:3.11.17-trixie \
  python -m unittest discover -v