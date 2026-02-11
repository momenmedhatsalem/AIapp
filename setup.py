from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="justyol_dashboard",
    version="0.0.1",
    description="Justyol Unified Dashboard System",
    author="Ahmed Badran",
    author_email="ahmed@justyol.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
