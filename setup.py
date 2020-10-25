# this file contains some placeholders
# that are changed in a local copy if a release is made

import setuptools

README = 'README.md'  # the path to your readme file
README_MIME = 'text/markdown'  # it's mime type

with open(README, "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="<setup>",  # placeholder (name of repo)
    version="<>",  # placeholder (tag of release)
    author="<setup>",  # placeholder (owner of repo)
    description="<setup>",  # placeholder (description of repo)
    url="<setup>",  # placeholder (url of repo)
    long_description=long_description,
    long_description_content_type=README_MIME,
    packages=setuptools.find_packages(),
    author_email="none@none.com",  # the email of the repo owner
    classifiers=[  # add some info about you package
        "Programming Language :: Python",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent"
    ],
    install_requires=[  # add required pypi packages here
    ]
)
