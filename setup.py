import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scullery",
    version="0.1.0",
    author="Daniel Dunn",
    author_email="dannydunn@eternityforest.com",
    description="A utility library based on KaithemAutomation featuring a GStreamer wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EternityForest/scullery",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.6',
    install_requires=[
          'pyyaml',
          'typeguard',
          "sf2utils",
          "pyFluidSynth"
      ],
)