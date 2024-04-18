import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scullery",
    version="0.1.17",
    author="Daniel Dunn",
    author_email="dannydunn@eternityforest.com",
    description="A utility library based on KaithemAutomation featuring a GStreamer wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EternityForest/scullery",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=["pyyaml", "beartype", "paho-mqtt", "pint"],
)


# To push to pypi
# python3 setup.py sdist bdist_wheel
# python3 -m twine upload dist/*
