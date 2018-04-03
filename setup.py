from distutils.core import setup

setup(
    name='reload-cli',
    version='0.1.0',
    description='Fast reload apps',
    author='Chris Hunt',
    author_email='chrahunt@gmail.com',
    url='https://github.com/chrahunt/reload-cli',
    entry_points={
        'console_scripts': ['crestart=chain.command_line:main']
    },
    install_requires=[
        'psutil'
    ]
)
