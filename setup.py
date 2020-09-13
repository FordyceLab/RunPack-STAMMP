from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
	name = 'runpack-stammp',
	version = '0.1.0',
	url = 'https://github.com/FordyceLab/RunPack-STAMMP.git',
	author = 'Daniel Mokhtari',
	author_email = '',
	description = 'STAMMP Experimental Aquisition',
	packages = find_packages(),    
	install_requires = requirements,
)