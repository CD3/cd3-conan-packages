dummy:
	echo "Choose a command"

export-all:
	pipenv run python bin/export-packages.py $(OPTS)

export-releases:
	pipenv run python bin/export-packages.py $(OPTS) ./01-configurations/releases.yaml

create-releases:
	pipenv run python bin/export-packages.py --create ./01-configurations/releases.yaml $(OPTS)

create-all:
	pipenv run python bin/export-packages.py --create $(OPTS)

upload-all:
	@ echo "To upload conan packages, run the following command."
	@ echo "$$ conan upload name/version@owner/testing --all -r=remote-to-upload-to"

clean-tmp-dirs:
	@ rm _* -rf

clean-instances:
	@ find ./ -iname 'conanfile-[0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z].py' -exec rm {} \;

clean-test_package-build-dirs:
	@ rm recipies/*/test_package/build -rf

clean-all: clean-tmp-dirs clean-instances clean-test_package-build-dirs

test-utils:
	pipenv run python -m pytest -s $(OPTS)

test-integrations:
	pipenv run python bin/test-integrations.py $(OPTS)

list-package-references:
	@ for file in recipes/*/conanfile.py; do conan info $$file; done 2>&1 | grep "^conanfile.py" | sed "s|conanfile.py (||;s|)$$|@$(OWNER_AND_CHANNEL)|"

remove-all-from-remote:
	make list-package-references OWNER_AND_CHANNEL="cd3/devel" | xargs -n 1 conan remove -r cd3 -f

upload-all:
	make list-package-references OWNER_AND_CHANNEL="cd3/devel" | grep "@cd3/devel" | xargs -n 1 conan upload -r cd3 --all

check-for-new-releases:
	pipenv run python bin/check-for-new-releases.py
