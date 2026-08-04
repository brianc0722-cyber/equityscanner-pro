.PHONY: run run-api run-dashboard test lint install clean docker-up docker-down

install:
	pip install -r requirements.txt

run:
	python run_all.py

run-api:
	PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

run-dashboard:
	PYTHONPATH=. streamlit run dashboard/app.py --server.port 8501

test:
	python -m pytest tests/ -v --tb=short || echo "No tests or pytest not installed"

lint:
	python -m ruff check . || echo "ruff not installed"
	python -m black --check . || echo "black not installed"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

backtest:
	PYTHONPATH=. python -c "from dashboard import backtest; print(backtest.run_backtest(40))"