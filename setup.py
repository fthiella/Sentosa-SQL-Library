from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='Sentosa SQL Library',
      version='0.1',
      description='SQL Backend Library for Datatables and Frontend Apps',
      url='http://github.com/fthiella/Sentosa-SQL-Library',
      author='Federico Thiella',
      author_email='fthiella@gmail.com',
      license='MIT',
      packages=['ssqll'],
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose'],
      include_package_data=True,
)