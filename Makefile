init:
	pip install -r requirements.txt

test:
	python test.py

coverage:
	rm -f .coverage
	coverage -x test.py
	coverage report --omit=tests/*,*/__init__.py,flashget/config.py
	coverage html --omit=tests/*,*/__init__.py,flashget/config.py
