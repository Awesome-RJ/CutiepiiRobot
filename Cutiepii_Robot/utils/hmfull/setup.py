from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text("utf-8")

setup(
    name='hmfull',
    version='1.0.3',
    license='ISC',
    author="Alice Addison",
    author_email='alice@alicesworld.tech',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/ProgrammerIn-wonderland/hmfullpy',
    keywords= ["anime", "hentai", "nsfw", "sfw", "images", "gifs", "wallpaper", "discord", "ahegao", "ass", "neko", "kitsune", "yuri", "panties", "thighs", "foot", "overwatch", "dva", "erotic", "lewdkemo", "lewdneko", "lewdkitsune", "holo", "bj", "spank", "ero", "kawaii", "cute", "waifu", "hmtai", "zettaiRyouiki", "18+", "REST", "API", "Mikun"],
    long_description=long_description,
    long_description_content_type='text/x-rst',
    install_requires=[
          'requests',
      ],

)