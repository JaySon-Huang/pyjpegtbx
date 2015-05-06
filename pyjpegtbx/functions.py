#!/usr/bin/env python
#encoding=utf-8

import ctypes
from .structs import (
    jmp_buf, jpeg_error_mgr, j_decompress_ptr, j_compress_ptr,
    JSAMPARRAY, jvirt_barray_ptr
)

__all__ = [
    'cfopen', 'cfclose',
    'csetjmp', 'clongjmp',
    'jfuncs',
    'funcs_metadata',
]

_all_libs = (
    ('jpeg.dll', 'libjpeg.so', 'libjpeg.dylib'),
    ('c.dll', 'libc.so', 'libc.dylib'),
)


def __loadLib(liblst):
    found = False
    for libname in liblst:
        try:
            _lib = ctypes.cdll.LoadLibrary(libname)
            found = True
            return _lib
        except OSError:
            pass
    if not found:
        raise ImportError("ERROR: fail to load the dynamic library.")
_jpeg = __loadLib(_all_libs[0])
_c = __loadLib(_all_libs[1])


def jround_up(a, b):
    a += b - 1
    return a - (a % b)

cfopen = _c.fopen
cfopen.restype = ctypes.c_void_p
cfopen.argtypes = (ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_char))
cfclose = _c.fclose
cfclose.restype = None
cfclose.argtypes = (ctypes.c_void_p, )

csetjmp = _c.setjmp
csetjmp.restype = ctypes.c_int
csetjmp.argtypes = (jmp_buf, )
clongjmp = _c.longjmp
clongjmp.restype = None
clongjmp.argtypes = (jmp_buf, ctypes.c_int)

jfuncs = {}


def register_jpeg_function(funcname, restype, argtypes, asFuncname=None):
    func = _jpeg.__getattr__(funcname)
    func.restype = restype
    func.argtypes = argtypes
    if asFuncname is None:
        asFuncname = funcname
    jfuncs[asFuncname] = func

funcs_metadata = (
    ('jpeg_std_error',
        ctypes.POINTER(jpeg_error_mgr),
        (ctypes.POINTER(jpeg_error_mgr),),
        'jStdError'),

    ('jpeg_CreateDecompress',
        None,
        (j_decompress_ptr, ctypes.c_int, ctypes.c_size_t),
        'jCreaDecompress'),
    ('jpeg_CreateCompress',
        None,
        (j_compress_ptr, ctypes.c_int, ctypes.c_size_t),
        'jCreaCompress'),

    ('jpeg_stdio_src',
        None,
        (j_decompress_ptr, ctypes.c_void_p),
        'jStdSrc'),
    ('jpeg_stdio_dest',
        None,
        (j_compress_ptr, ctypes.c_void_p),
        'jStdDest'),

    ('jpeg_mem_src',
        None,
        (j_decompress_ptr, ctypes.c_char_p, ctypes.c_ulong),
        'jMemSrc'),
    ('jpeg_mem_dest',
        None,
        (j_compress_ptr,
            ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_long)),
        'jMemDest'),

    ('jpeg_start_compress',
        None,
        (j_compress_ptr, ctypes.c_int),
        'jStrtCompress'),
    ('jpeg_start_decompress',
        ctypes.c_int,
        (j_decompress_ptr, ),
        'jStrtDecompress'),

    ('jpeg_set_defaults',
        None,
        (j_compress_ptr, ),
        'jSetDefaults'),
    ('jpeg_set_quality',
        None,
        (j_compress_ptr, ctypes.c_int, ctypes.c_int),
        'jSetQuality'),
    ('jpeg_simple_progression',
        None,
        (j_compress_ptr, ),
        'jSimProgress'),

    ('jpeg_read_header',
        None,
        (j_decompress_ptr, ctypes.c_bool),
        'jReadHeader'),

    ('jpeg_write_scanlines',
        ctypes.c_uint,
        (j_compress_ptr, JSAMPARRAY, ctypes.c_uint),
        'jWrtScanlines'),
    ('jpeg_read_scanlines',
        ctypes.c_uint,
        (j_decompress_ptr, JSAMPARRAY, ctypes.c_uint),
        'jReadScanlines'),

    ('jpeg_write_coefficients',
        None,
        (j_compress_ptr, ctypes.POINTER(jvirt_barray_ptr)),
        'jWrtCoefs'),
    ('jpeg_read_coefficients',
        jvirt_barray_ptr,
        (j_decompress_ptr, ),
        'jReadCoefs'),

    ('jpeg_finish_compress',
        ctypes.c_int,
        (j_compress_ptr, ),
        'jFinCompress'),
    ('jpeg_finish_decompress',
        ctypes.c_int,
        (j_decompress_ptr, ),
        'jFinDecompress'),

    ('jpeg_destroy_compress',
        None,
        (j_compress_ptr, ),
        'jDestCompress'),
    ('jpeg_destroy_decompress',
        None,
        (j_decompress_ptr, ),
        'jDestDecompress'),
)

jpeg_alloc_quant_table = _jpeg.jpeg_alloc_quant_table
jpeg_alloc_huff_table = _jpeg.jpeg_alloc_huff_table

for funcname, res, args, shortname in funcs_metadata:
    register_jpeg_function(funcname, res, args, shortname)
