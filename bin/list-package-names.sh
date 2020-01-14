# /bin/bash
#
for dir in recipes/*
do
  conan info "${dir}"
done 2>&1 | ag '^conanfile.py' | sed "s/^.*(//;s/)//"
