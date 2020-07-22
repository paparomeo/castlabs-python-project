HTTP_PORT ?= 8080
WORKERS ?= ""

bin=.venv/bin
pip=$(bin)/pip
uvicorn=$(bin)/uvicorn
coverage=$(bin)/coverage

.venv:
	python -m venv .venv
	$(pip) install --upgrade pip
	$(pip) install -r requirements-dev.txt

build: .venv

run: .venv
	@$(uvicorn) app.main:app --port=$(HTTP_PORT)

test: .venv
	@$(coverage) run -m pytest && $(coverage) report

docker:
	@HTTP_PORT=$(HTTP_PORT) WORKERS=${WORKERS} docker-compose up app
