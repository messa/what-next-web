run_dev: content.json
	test -d node_modules || npm install
	npm run develop

content.json:
	python3 fetch_content.py > $@

.DELETE_ON_ERROR:
