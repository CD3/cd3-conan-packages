# Conan Package Recipes for CD3 Projects

This is a collection of recipes and utilities for building conan packages for various libraries I have written or use.
Some libraries have been included in [Conan Center](https://conan.io/center), this repo is used to develop recipes before
submitting to Conan Center.

# Using

Conan now supports [local recipe index repositories](https://docs.conan.io/2/tutorial/conan_repositories/setup_local_recipes_index.html), so you
can use this repository like a conan remote.

```
$ git clone https://github.com/CD3/cd3-conan-packages
$ conan remote add cd3-conan-packages ./cd3-conan-packages
```

