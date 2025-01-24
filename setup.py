from setuptools import setup, find_packages

setup(
    name='vgc2',
    version='3.0.5.7',
    description='The VGC AI Framework emulates the Video Game Championships of Pokémon with Pokémon AI Trainer agents.',
    url='https://gitlab.com/DracoStriker/pokemon-vgc-engine',
    author='Simão Reis',
    author_email='simao.reis@vortex-colab.com, simao.reis@outlook.pt',
    license='MIT License',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['arcade~=2.6.17',
                      'numpy~=1.26.4',
                      'gymnasium~=0.29.1',
                      'customtkinter~=5.2.2',
                      'torch~=2.2.1',
                      'pygad~=3.3.1',
                      'scipy~=1.12.0',
                      'setuptools~=69.1.1',
                      ],
    classifiers=[
        'Development Status :: 2 - Development',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.10.0',
    ],
)
