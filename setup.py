from setuptools import setup, find_packages

setup(
    name='vgc',
    version='2.2.1',
    description='The VGC AI Framework aims to emulate the Esports scenario of human video game championships of Pokémon with AI agents, including the game balance aspect.',
    url='https://gitlab.com/DracoStriker/pokemon-vgc-engine',
    author='Simão Reis',
    author_email='simao.reis@outlook.pt',
    license='MIT License',
    packages=find_packages(exclude=['agent*', 'example']),
    include_package_data=True,
    install_requires=['numpy>=1.15.4',
                      'gym>=0.10.9',
                      'PySimpleGUI>=4.20.0',
                      'simple-plugin-loader>=1.6',
                      'elo~=0.1.1',
                      'arcade~=2.6.7',
                      ],
    classifiers=[
        'Development Status :: 2 - Development',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.9.9',
    ],
)
