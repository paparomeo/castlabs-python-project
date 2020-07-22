HTTP_PORT ?= 8080

bin=.venv/bin
pip=$(bin)/pip
uvicorn=$(bin)/uvicorn
coverage=$(bin)/coverage

build:
	python -m venv .venv
	$(pip) install --upgrade pip
	$(pip) install -r requirements-dev.txt

run:
	@$(uvicorn) app.main:app --port=$(HTTP_PORT)

test:
	@$(coverage) run -m pytest && $(coverage) report
