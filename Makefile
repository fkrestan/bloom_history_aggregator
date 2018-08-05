init:
	pipenv install

test:
	py.test -vs --fulltrace tests/

build:
	python3 setup.py build

dist: clean
	python3 setup.py sdist bdist_wheel

clean:
	rm -rf build/ dist/ blooming_history_aggregator_service.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} \+

.PHONY: init test build dist clean
