from setuptools import setup

setup(name='confighelper',
      version='0.1',
      description='Simultaneous command-line and yaml file configuration handling',
      url='https://github.com/samwisehawkins/confighelper',
      author='Sam Hawkins',
      author_email='sam@computing.io',
      license='MIT',
      py_modules=['confighelper', 'docopt'],
      install_requires = ['pyyaml'])
      

