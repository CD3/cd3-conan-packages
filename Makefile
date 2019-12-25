export-all:
	pipenv run python bin/export-packages.py

create-all:
	pipenv run python bin/export-packages.py --create

upload-all:
	@ echo "To upload conan packages, run the following command."
	@ echo "$$ conan upload name/version@owner/testing --all -r=remote-to-upload-to"

clean-tmp-dirs:
	@ rm _* -rf

clean-instances:
	@ find ./ -iname 'conanfile-[0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z].py' -exec rm {} \;

clean-all: clean-tmp-dirs clean-instances

test:
	pipenv run python -m pytest -s $(OPTS)

create-releases:
	pipenv run python bin/export-packages.py --create ./01-configurations/releases.yaml
