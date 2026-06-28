from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
        name='Sentosa SQL Library',
        version='0.3',
        description='SQL Backend Library for AI, Datatables and Frontend Apps',
        url='http://github.com/fthiella/Sentosa-SQL-Library',
        author='Federico Thiella',
        author_email='fthiella@gmail.com',
        license='MIT',
        packages=['ssll'],
        zip_safe=False,
        test_suite='nose.collector',
        tests_require=['nose'],
        include_package_data=True,
        long_description=readme(),
        long_description_content_type='text/markdown'
      )
