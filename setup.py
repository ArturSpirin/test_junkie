import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="test_junkie",
    version="0.6a4",
    author="Artur Spirin",
    author_email="as.no.replies@gmail.com",
    description="Advanced test runner with built in reporting and analytics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.test-junkie.com/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    install_requires=["statistics", "psutil"],
    keywords=["automation", "testing", "tests", "test-runner"],
)
