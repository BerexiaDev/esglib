from setuptools import setup, find_packages

setup(
    name='esg_lib',
    version='0.1',
    packages=find_packages(),
    install_requires=[],
    author='Myrza Nurmanbetov',
    author_email='hakedhacked0@gmail.com',
    description='ESG Global Library',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
