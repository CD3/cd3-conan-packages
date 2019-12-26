export-all:
	pipenv run python bin/export-packages.py $(OPTS)

create-all:
	pipenv run python bin/export-packages.py --create $(OPTS)

upload-all:
	@ echo "To upload conan packages, run the following command."
	@ echo "$$ conan upload name/version@owner/testing --all -r=remote-to-upload-to"

clean-tmp-dirs:
	@ rm _* -rf

clean-instances:
	@ find ./ -iname 'conanfile-[0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z].py' -exec rm {} \;

clean-all: clean-tmp-dirs clean-instances

test-utils:
	pipenv run python -m pytest -s $(OPTS)

test-integrations:
	pipenv run python bin/test-integrations.py $(OPTS)

create-releases:
	pipenv run python bin/export-packages.py --create ./01-configurations/releases.yaml $(OPTS)
