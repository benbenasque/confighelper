from setuptools import setup, find_packages

setup(
      name='confighelper',
      version='0.1.1',
      description='Simultaneous command-line and yaml file configuration handling',
      url='https://github.com/samwisehawkins/confighelper',
      author='Sam Hawkins',
      author_email='sam@computing.io',
      license='MIT',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
      ],

       keywords='configuration yaml docopt parsing',
       #packages=find_packages(exclude=['docs', 'tests']),
       py_modules=['confighelper'],
       install_requires=['docopt', 'pyyaml'],
       extra_requires= {'test' : ['pytest']}
)  
