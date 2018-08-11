init:
	pipenv install

run: build
	PYTHONPATH=build/lib.linux-x86_64-3.6/:$(PYTHONPATH) \
	FLASK_DEBUG=1 \
	FLASK_APP=blooming_history_aggregator \
	flask run --host 0.0.0.0

test: build
	PYTHONPATH=build/lib.linux-x86_64-3.6:$(PYTHONPATH) \
	py.test -vs --fulltrace tests/

build:
	python3 setup.py build

dist: clean
	python3 setup.py sdist bdist_wheel

clean:
	rm -rf build/ dist/ blooming_history_aggregator_service.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} \+
	find . -type f -name "*.pyc" -exec rm -rf {} \+

.PHONY: init test build dist clean
