.PHONY: install run dev clean

install:
	pip install -r requirements.txt
	pip install -e .

run:
	term
	
dev:
	python watch.py watchmedo auto-restart --directory=./termbrowser --pattern="*.py" --recursive -- term


# Remove cache and compiled files
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +

