PATH := $(CURDIR)/venv/bin:$(PATH)
.PHONY: venv clean watch jupyterhub

venv:
	tox -e venv

watch: venv
	venv/bin/jlpm run watch&
	venv/bin/jupyter lab \
	    --debug \
		--autoreload \
		--config=integration-tests/jupyterlab_config.py \
		--no-browser \
		--notebook-dir=integration-tests/examples

build: venv
	venv/bin/jlpm run build
	venv/bin/jlpm run install:extension
	venv/bin/jupyter lab build

clean:
	venv/bin/jlpm run clean:all || echo 'not cleaning jlpm'
	rm -rf venv/


jupyterhub: build
	cd integration-tests && \
	jupyterhub --config=jupyterhub_config.py
