export-all:
	pipenv run python bin/export-packages.py $(OPTS)

create-all:
	pipenv run python bin/export-packages.py --create $(OPTS)

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

create-masters:
	pipenv run python bin/export-packages.py --create ./01-configurations/masters.yaml $(OPTS)

list-package-references:
	@ for file in recipes/*/conanfile.py; do conan info $$file; done 2>&1 | grep "^conanfile.py" | sed "s|conanfile.py (||;s|)$$|@$(OWNER_AND_CHANNEL)|"

remove-all-from-remote:
	make list-package-references OWNER_AND_CHANNEL="cd3/devel" | xargs -n 1 conan remove -r cd3 -f

upload-all:
	make list-package-references OWNER_AND_CHANNEL="cd3/devel" | grep "@cd3/devel" | xargs -n 1 conan upload -r cd3 --all

check-for-new-releases:
	pipenv run python bin/check-for-new-releases.py
