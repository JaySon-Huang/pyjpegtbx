from distutils.core import setup, Extension

setup(
    name="pyjpegtbx",
    version="1.0",
    author="JaySon Hwang",
    author_email="jayson.hjs@gmail.com",

    ext_modules=[
        Extension(
            name="pyjpegtbx",
            sources=["testMoudle.c"],
            include_dirs=['/usr/include', '/usr/local/include'],
            library_dirs=['/usr/lib', '/usr/local/lib'],
            libraries=['jpeg'],
        )
    ]
)
