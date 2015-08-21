from setuptools import setup

setup(
    name='letsencrypt-icecast',
    py_modules = ['icecast'],
    install_requires=[
        'letsencrypt',
        'zope.interface',
    ],
    entry_points={
        'letsencrypt.plugins': [
            'icecast_installer = icecast:IcecastInstaller',
        ],
    },
)
