import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="test_junkie",
    version="0.4a1",
    author="Artur Spirin",
    author_email="as.no.replies@gmail.com",
    description="Advanced execution framework for test scenarios",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ArturSpirin/test_junkie",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Development Status :: 3 - Alpha"
    ],
    install_requires=["statistics", "psutil"],
)
