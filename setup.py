from setuptools import setup


setup(name='pymqim',
      version='0.1',
      description='Wrapper package for pymqi',
      url='http://github.com/storborg/pymqim',
      author='Maxim Vovshin',
      author_email='hyaxia@gmail.com',
      license='DAVAY',
      packages=['pymqim'],
      install_requires=[
          'py3mqi',
      ],
      zip_safe=False)
