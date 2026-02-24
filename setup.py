from setuptools import setup, find_packages

setup(
    name="nsp-proselint",
    version="0.1.0",
    description="Formulaic prose detection and replacement for LLM outputs",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pyyaml>=6.0",
    ],
    package_data={
        "nsp_proselint": ["dictionaries/*.yaml"],
    },
)
