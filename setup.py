import re

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("test_junkie/__init__.py", "r") as fh:  # single source of the version
    version = re.search(r'^__version__ = "([^"]+)"', fh.read(), re.M).group(1)

setuptools.setup(
    name="test_junkie",
    version=version,
    author="Artur Spirin",
    author_email="as.no.replies@gmail.com",
    description="The Python test runner built for precision",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.test-junkie.com/",
    project_urls={
        "Documentation": "https://www.test-junkie.com/documentation/",
        "Tutorials": "https://www.test-junkie.com/tutorials/",
        "Changelog": "https://github.com/ArturSpirin/test_junkie/blob/master/CHANGELOG.md",
        "Source": "https://github.com/ArturSpirin/test_junkie",
    },
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    package_data={"test_junkie.reporter": ["assets/*.css", "assets/*.js", "assets/*.html"]},
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    install_requires=["psutil", "appdirs", "colorama", "coverage"],
    keywords=["automation", "testing", "tests", "test-runner"],
    entry_points={
          'console_scripts': [
              'tj3 = test_junkie.__main__:main',
              'tj = test_junkie.__main__:main'
          ]
    },
)
