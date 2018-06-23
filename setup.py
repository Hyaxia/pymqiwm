from setuptools import setup


setup(name='pymqiwm',
      version='0.1',
      description='Wrapper package for pymqi',
      url='http://github.com/storborg/pymqiwm',
      author='Maxim Vovshin',
      author_email='hyaxia@gmail.com',
      license='DAVAY',
      packages=['pymqiwm'],
      install_requires=[
          'py3mqi',
      ],
      zip_safe=False)
