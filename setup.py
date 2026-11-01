from setuptools import setup, find_packages

setup(
    name="african_health_hub_flask",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-login',
        'flask-cors',
        'pyodbc',
    ],
)
