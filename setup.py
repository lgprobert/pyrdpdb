from setuptools import find_namespace_packages, setup

version = "4.2.2"
long_description = open("README.md").read()

setup(
    name="pyrdpdb",
    version=version,
    license="MIT",
    author="Robert Li",
    author_email="lgprobert@gmail.com",
    description="Pure Python RapidsDB Driver",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lgprobert/pyrdpdb",
    packages=find_namespace_packages(where=".", include=["pyrdpdb*", "pyrdpdb.*"]),
    package_dir={"pyrdpdb": "pyrdpdb"},
    entry_points={
        "sqlalchemy.dialects": [
            "rapidsdb.pyrdp = pyrdpdb.pyrdp.sa.pyrdp:RDPDialect_pyrdp",
            "rapidsdb.asyncrdp = pyrdpdb.aiordp.sa.asyncrapids:RDPDialect_asyncrdp",
        ]
    },
    install_requires=[
        "thrift==0.11.0",
        "SQLAlchemy>=2.0, <3.0",
    ],
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Topic :: Database",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
