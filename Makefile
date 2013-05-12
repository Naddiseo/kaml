run:
	clear
	python main.py test1.kaml

trace:
	clear
	python main.py -t -l test1.kaml

parse:
	clear
	python main.py -t test1.kaml

lex:
	clear
	python main.py -l test1.kaml

test:
	clear
	nosetests