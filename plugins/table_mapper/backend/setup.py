from setuptools import setup, find_packages

setup(
    name="baserow-table-mapper",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # 依赖 Baserow 核心包
    ],
    description="Baserow plugin for automatic field mapping between tables",
    author="Baserow Community",
    license="MIT",
)
