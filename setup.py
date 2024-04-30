from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()
setup(
    name='mpdt',
    version='1.0',
    description='Mass paper download tool',
    license="MIT",
    long_description=long_description,
    author='Luna',
    url="https://github.com/Luna5ama/mpdt",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        'requests',
        'unpywall',
        'pypdf',
        'requests-html',
        'lxml_html_clean'
    ],
    entry_points={  # Optional
        "console_scripts": [
            "mpdt=mpdt:main.main",
        ],
    },
)

