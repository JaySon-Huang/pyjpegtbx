#!/usr/bin/env python
#encoding=utf-8

import ctypes
from copy import deepcopy
from IPython import embed

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


jpeg_alloc_quant_table = _jpeg.jpeg_alloc_quant_table
jpeg_alloc_huff_table = _jpeg.jpeg_alloc_huff_table

DCTSIZE = 8  # The basic DCT block is 8x8 coefficients
DCTSIZE2 = 64  # DCTSIZE squared; num of elements in a block
NUM_QUANT_TBLS = 4  # Quantization tables are numbered 0..3
NUM_HUFF_TBLS = 4   # Huffman tables are numbered 0..3
NUM_ARITH_TBLS = 16  # Arith-coding tables are numbered 0..15
MAX_COMPS_IN_SCAN = 4  # JPEG limit on num of components in one scan
MAX_SAMP_FACTOR = 4  # JPEG limit on sampling factors
C_MAX_BLOCKS_IN_MCU = 10  # compressor's limit on blocks per MCU
D_MAX_BLOCKS_IN_MCU = 10  # decompressor's limit on blocks per MCU
JPEG_LIB_VERSION = 80  # Compatibility version 9.0
JPOOL_IMAGE = 1
def jround_up(a, b):
    a += b - 1
    return a - (a % b)

class J_COLOR_SPACE(object):
    JCS_UNKNOWN = 0     # error/unspecified
    JCS_GRAYSCALE = 1   # monochrome
    JCS_RGB = 2         # red/green/blue, standard RGB (sRGB)
    JCS_YCbCr = 3       # Y/Cb/Cr (also known as YUV), standard YCC
    JCS_CMYK = 4        # C/M/Y/K
    JCS_YCCK = 5        # Y/Cb/Cr/K
    JCS_BG_RGB = 6      # big gamut red/green/blue, bg-sRGB
    JCS_BG_YCC = 7      # big gamut Y/Cb/Cr, bg-sYCC

boolean = ctypes.c_int
# boolean is char : ctypes.c_int
# JDIMENSION is unsigned int : ctypes.c_uint

JSAMPLE = ctypes.c_char
JSAMPROW = ctypes.POINTER(JSAMPLE)
JSAMPARRAY = ctypes.POINTER(JSAMPROW)

JCOEF = ctypes.c_short
JBLOCK = JCOEF * DCTSIZE2
JBLOCK.__repr__ = lambda self: 'JBLOCK @ %x' % ctypes.addressof(self)
JBLOCKROW = ctypes.POINTER(JBLOCK)
JBLOCKARRAY = ctypes.POINTER(JBLOCKROW)
jmp_buf = ctypes.c_int * 37


class jpeg_error_mgr(ctypes.Structure):
    pass


class jpeg_memory_mgr(ctypes.Structure):
    pass


class JQUANT_TBL(ctypes.Structure):
    _fields_ = (
        ('quantval', ctypes.c_uint16 * DCTSIZE2),
        ('sent_table', boolean),
    )


class JHUFF_TBL(ctypes.Structure):
    _fields_ = (
        ('bits', ctypes.c_uint8 * 17),
        ('huffval', ctypes.c_uint8 * 256),
        ('sent_table', boolean),
    )


class jpeg_component_info(ctypes.Structure):
    _fields_ = (
        ('component_id', ctypes.c_int),
        ('component_index', ctypes.c_int),
        ('h_samp_factor', ctypes.c_int),
        ('v_samp_factor', ctypes.c_int),
        ('quant_tbl_no', ctypes.c_int),
        ('dc_tbl_no', ctypes.c_int),
        ('ac_tbl_no', ctypes.c_int),
        ('width_in_blocks', ctypes.c_uint),
        ('height_in_blocks', ctypes.c_uint),
        ('DCT_h_scaled_size', ctypes.c_int),
        ('DCT_v_scaled_size', ctypes.c_int),
        ('downsampled_width', ctypes.c_uint),
        ('downsampled_height', ctypes.c_uint),
        ('component_needed', boolean),
        ('MCU_width', ctypes.c_int),
        ('MCU_height', ctypes.c_int),
        ('MCU_blocks', ctypes.c_int),
        ('MCU_sample_width', ctypes.c_int),
        ('last_col_width', ctypes.c_int),
        ('last_row_height', ctypes.c_int),
        ('quant_table', ctypes.POINTER(JQUANT_TBL)),
        ('dct_table', ctypes.c_void_p),
    )


class jpeg_common_struct(ctypes.Structure):
    _fields_ = (
        ('err', ctypes.POINTER(jpeg_error_mgr)),
        ('mem', ctypes.POINTER(jpeg_memory_mgr)),
        ('progress', ctypes.c_void_p),
        ('client_data', ctypes.c_void_p),
        ('is_decompressor', boolean),
        ('global_state', ctypes.c_int),
    )
j_common_ptr = ctypes.POINTER(jpeg_common_struct)


class jpeg_compress_struct(ctypes.Structure):
    _fields_ = (
        ('err', ctypes.POINTER(jpeg_error_mgr)),
        ('mem', ctypes.POINTER(jpeg_memory_mgr)),
        ('progress', ctypes.c_void_p),
        ('client_data', ctypes.c_void_p),
        ('is_decompressor', boolean),
        ('global_state', ctypes.c_int),  # 40

        ('dest', ctypes.c_void_p),  # 48

        ('image_width', ctypes.c_uint),
        ('image_height', ctypes.c_uint),
        ('input_components', ctypes.c_int),
        ('in_color_space', ctypes.c_int),  # 64

        ('input_gamma', ctypes.c_double),  # 72

        ('scale_num', ctypes.c_uint),
        ('scale_denom', ctypes.c_uint),  # 80

        ('jpeg_width', ctypes.c_uint),
        ('jpeg_height', ctypes.c_uint),  # 88

        ('data_precision', ctypes.c_int),

        ('num_components', ctypes.c_int),
        ('jpeg_color_space', ctypes.c_int),  # 100

        ('comp_info', ctypes.POINTER(jpeg_component_info)),

        ('quant_tbl_ptrs', ctypes.POINTER(JQUANT_TBL) * NUM_QUANT_TBLS),
        ('q_scale_factor', ctypes.c_int * NUM_QUANT_TBLS),

        ('dc_huff_tbl_ptrs', ctypes.POINTER(JHUFF_TBL) * NUM_HUFF_TBLS),
        ('ac_huff_tbl_ptrs', ctypes.POINTER(JHUFF_TBL) * NUM_HUFF_TBLS),

        ('arith_dc_L', ctypes.c_uint8 * NUM_ARITH_TBLS),
        ('arith_dc_U', ctypes.c_uint8 * NUM_ARITH_TBLS),
        ('arith_ac_K', ctypes.c_uint8 * NUM_ARITH_TBLS),

        ('num_scans', ctypes.c_int),
        ('scan_info', ctypes.c_void_p),

        ('raw_data_in', boolean),
        ('arith_code', boolean),
        ('optimize_coding', boolean),
        ('CCIR601_sampling', boolean),
        ('do_fancy_downsampling', boolean),
        ('smoothing_factor', ctypes.c_int),
        ('dct_method', ctypes.c_int),

        ('restart_interval', ctypes.c_uint),
        ('restart_in_rows', ctypes.c_int),

        ('write_JFIF_header', boolean),
        ('JFIF_major_version', ctypes.c_uint8),
        ('JFIF_minor_version', ctypes.c_uint8),

        ('density_unit', ctypes.c_uint8),
        ('X_density', ctypes.c_uint16),
        ('Y_density', ctypes.c_uint16),
        ('write_Adobe_marker', boolean),

        ('next_scanline', ctypes.c_uint),

        ('progressive_mode', boolean),
        ('max_h_samp_factor', ctypes.c_int),
        ('max_v_samp_factor', ctypes.c_int),

        ('min_DCT_h_scaled_size', ctypes.c_int),
        ('min_DCT_v_scaled_size', ctypes.c_int),

        ('total_iMCU_rows', ctypes.c_uint),

        ('comps_in_scan', ctypes.c_int),
        ('cur_comp_info', ctypes.c_void_p * MAX_COMPS_IN_SCAN),

        ('MCUs_per_row', ctypes.c_uint),
        ('MCU_rows_in_scan', ctypes.c_uint),

        ('blocks_in_MCU', ctypes.c_int),
        ('MCU_membership', ctypes.c_int * C_MAX_BLOCKS_IN_MCU),

        ('Ss', ctypes.c_int),
        ('Se', ctypes.c_int),
        ('Ah', ctypes.c_int),
        ('Al', ctypes.c_int),

        ('block_size', ctypes.c_int),
        ('natural_order', ctypes.POINTER(ctypes.c_int)),
        ('lim_Se', ctypes.c_int),

        ('master', ctypes.c_void_p),
        ('main', ctypes.c_void_p),
        ('prep', ctypes.c_void_p),
        ('coef', ctypes.c_void_p),
        ('marker', ctypes.c_void_p),
        ('cconvert', ctypes.c_void_p),
        ('downsample', ctypes.c_void_p),
        ('fdct', ctypes.c_void_p),
        ('entropy', ctypes.c_void_p),
        ('script_space', ctypes.c_void_p),
        ('script_space_size', ctypes.c_int),
    )
j_compress_ptr = ctypes.POINTER(jpeg_compress_struct)


class jpeg_decompress_struct(ctypes.Structure):
    _fields_ = (
        ('err', ctypes.POINTER(jpeg_error_mgr)),
        ('mem', ctypes.POINTER(jpeg_memory_mgr)),
        ('progress', ctypes.c_void_p),
        ('client_data', ctypes.c_void_p),
        ('is_decompressor', boolean),
        ('global_state', ctypes.c_int),

        ('src', ctypes.c_void_p),  # offset: 40

        ('image_width', ctypes.c_uint),
        ('image_height', ctypes.c_uint),
        ('num_components', ctypes.c_int),
        ('jpeg_color_space', ctypes.c_int),

        ('out_color_space', ctypes.c_int),  # offset: 64
        ('scale_num', ctypes.c_uint),
        ('scale_denom', ctypes.c_uint),

        ('output_gamma', ctypes.c_double),

        ('buffered_image', boolean),
        ('raw_data_out', boolean),

        ('dct_method', ctypes.c_int),  # offset: 96
        ('do_fancy_upsampling', boolean),  # offset: 100
        ('do_block_smoothing', boolean),

        ('quantize_colors', boolean),  # offset: 108

        ('dither_mode', ctypes.c_int),
        ('two_pass_quantize', boolean),
        ('desired_number_of_colors', ctypes.c_int),  # offset: 120

        ('enable_1pass_quant', boolean),
        ('enable_external_quant', boolean),
        ('enable_2pass_quant', boolean),

        ('output_width', ctypes.c_uint),  # offset: 136
        ('output_height', ctypes.c_uint),
        ('out_color_components', ctypes.c_int),
        ('output_components', ctypes.c_int),

        ('rec_outbuf_height', ctypes.c_int),

        ('actual_number_of_colors', ctypes.c_int),  # 156
        ('colormap', JSAMPARRAY),

        ('output_scanline', ctypes.c_uint),

        ('input_scan_number', ctypes.c_int),
        ('input_iMCU_row', ctypes.c_uint),

        ('output_scan_number', ctypes.c_int),
        ('output_iMCU_row', ctypes.c_uint),

        ('coef_bits', ctypes.POINTER(ctypes.c_int)),

        ('quant_tbl_ptrs', ctypes.POINTER(JQUANT_TBL) * NUM_QUANT_TBLS),

        ('dc_huff_tbl_ptrs', ctypes.POINTER(JHUFF_TBL) * NUM_HUFF_TBLS),
        ('ac_huff_tbl_ptrs', ctypes.POINTER(JHUFF_TBL) * NUM_HUFF_TBLS),

        ('data_precision', ctypes.c_int),

        ('comp_info', ctypes.POINTER(jpeg_component_info)),

        ('is_baseline', boolean),
        ('progressive_mode', boolean),
        ('arith_code', boolean),

        ('arith_dc_L', ctypes.c_uint8 * NUM_ARITH_TBLS),
        ('arith_dc_U', ctypes.c_uint8 * NUM_ARITH_TBLS),
        ('arith_ac_K', ctypes.c_uint8 * NUM_ARITH_TBLS),

        ('restart_interval', ctypes.c_uint),

        ('saw_JFIF_marker', boolean),  # 376

        ('JFIF_major_version', ctypes.c_uint8),
        ('JFIF_minor_version', ctypes.c_uint8),
        ('density_unit', ctypes.c_uint8),
        ('X_density', ctypes.c_uint16),
        ('Y_density', ctypes.c_uint16),
        ('saw_Adobe_marker', boolean),
        ('Adobe_transform', ctypes.c_uint8),

        ('CCIR601_sampling', boolean),

        ('marker_list', ctypes.c_void_p),

        ('max_h_samp_factor', ctypes.c_int),
        ('max_v_samp_factor', ctypes.c_int),

        ('min_DCT_h_scaled_size', ctypes.c_int),
        ('min_DCT_v_scaled_size', ctypes.c_int),

        ('total_iMCU_rows', ctypes.c_uint),

        ('sample_range_limit', ctypes.c_void_p),  # offset: 432

        ('comps_in_scan', ctypes.c_int),

        ('cur_comp_info', ctypes.POINTER(jpeg_component_info) * MAX_COMPS_IN_SCAN),

        ('MCUs_per_row', ctypes.c_uint),
        ('MCU_rows_in_scan', ctypes.c_uint),

        ('blocks_in_MCU', ctypes.c_int),
        ('MCU_membership', ctypes.c_int * D_MAX_BLOCKS_IN_MCU),

        ('Ss', ctypes.c_int),
        ('Se', ctypes.c_int),
        ('Ah', ctypes.c_int),
        ('Al', ctypes.c_int),

        ('block_size', ctypes.c_int),
        ('natural_order', ctypes.POINTER(ctypes.c_int)),
        ('lim_Se', ctypes.c_int),

        ('unread_marker', ctypes.c_int),

        ('master', ctypes.c_void_p),
        ('main', ctypes.c_void_p),
        ('coef', ctypes.c_void_p),
        ('post', ctypes.c_void_p),
        ('inputctl', ctypes.c_void_p),
        ('marker', ctypes.c_void_p),
        ('entropy', ctypes.c_void_p),
        ('idct', ctypes.c_void_p),
        ('upsample', ctypes.c_void_p),
        ('cconvert', ctypes.c_void_p),
        ('cquantize', ctypes.c_void_p),
    )
j_decompress_ptr = ctypes.POINTER(jpeg_decompress_struct)


class backing_store_info(ctypes.Structure):
    _fields_ = (
        ('read_backing_store', ctypes.c_void_p),
        ('write_backing_store', ctypes.c_void_p),
        ('close_backing_store', ctypes.c_void_p),
        ('temp_file', ctypes.c_void_p),
        ('temp_name', ctypes.c_char * 64),
    )


# 链表的声明方法
class jvirt_barray_control(ctypes.Structure):
    pass
jvirt_barray_control._fields_ = (
    ('mem_buffer', JBLOCKARRAY),
    ('rows_in_array', ctypes.c_uint),
    ('blocksperrow', ctypes.c_uint),
    ('maxaccess', ctypes.c_uint),
    ('rows_in_mem', ctypes.c_uint),
    ('rowsperchunk', ctypes.c_uint),
    ('cur_start_row', ctypes.c_uint),
    ('first_undef_row', ctypes.c_uint),
    ('pre_zero', boolean),
    ('dirty', boolean),
    ('b_s_open', boolean),
    ('next', ctypes.POINTER(jvirt_barray_control)),
    ('b_s_info', backing_store_info),
)
jvirt_barray_ptr = ctypes.POINTER(jvirt_barray_control)

ALLOC_SARRAY_FUNC = ctypes.CFUNCTYPE(
    JSAMPARRAY,
    j_common_ptr, ctypes.c_int, ctypes.c_uint, ctypes.c_uint
)
ACCESS_VIRT_BARRAY_FUNC = ctypes.CFUNCTYPE(
    JBLOCKARRAY,
    j_common_ptr, jvirt_barray_ptr, ctypes.c_uint, ctypes.c_uint, ctypes.c_int
)
ALLOC_SMALL_FUNC = ctypes.CFUNCTYPE(
    ctypes.c_void_p,
    j_common_ptr, ctypes.c_int, ctypes.c_size_t
)
REQUEST_VIRT_BARRAY_FUNC = ctypes.CFUNCTYPE(
    jvirt_barray_ptr,
    j_common_ptr, ctypes.c_int, boolean, ctypes.c_uint, ctypes.c_uint, ctypes.c_int
)

jpeg_memory_mgr._fields_ = (
    ('alloc_small', ALLOC_SMALL_FUNC),
    ('alloc_large', ctypes.c_void_p),
    ('alloc_sarray', ALLOC_SARRAY_FUNC),
    ('alloc_barray', ctypes.c_void_p),
    ('request_virt_sarray', ctypes.c_void_p),
    ('request_virt_barray', REQUEST_VIRT_BARRAY_FUNC),
    ('realize_virt_arrays', ctypes.c_void_p),
    ('access_virt_sarray', ctypes.c_void_p),
    ('access_virt_barray', ACCESS_VIRT_BARRAY_FUNC),
    ('free_pool', ctypes.c_void_p),
    ('self_destruct', ctypes.c_void_p),
    ('max_memory_to_use', ctypes.c_long),
    ('max_alloc_chunk', ctypes.c_long),
)

funcs = {}
cfopen = _c.fopen
cfopen.restype = ctypes.c_void_p
cfopen.argtypes = (ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_char))
cfclose = _c.fclose
cfclose.restype = None
cfclose.argtypes = (ctypes.c_void_p, )

csetjmp = _c.setjmp
csetjmp.restype = ctypes.c_int
csetjmp.argtypes = (jmp_buf,)
clongjmp = _c.longjmp
clongjmp.restype = None
clongjmp.argtypes = (jmp_buf, ctypes.c_int)
ERROR_EXIT_FUNC = ctypes.CFUNCTYPE(None, j_common_ptr)
def py_error_exit(cinfo):
    print('in calling error_exit')
    # clongjmp(cinfo.contents.err.contents.setjmp_buffer, 1)
error_exit = ERROR_EXIT_FUNC(py_error_exit)


class msg_parm(ctypes.Union):
    _fields_ = (
        ('i', ctypes.c_int * 8),
        ('s', ctypes.c_char * 80)
    )
jpeg_error_mgr._fields_ = (
    ('error_exit', ERROR_EXIT_FUNC),
    ('emit_message', ctypes.c_void_p),
    ('output_message', ctypes.c_void_p),
    ('format_message', ctypes.c_void_p),
    ('reset_error_mgr', ctypes.c_void_p),
    ('msg_code', ctypes.c_int),
    ('msg_parm', msg_parm),
    ('trace_level', ctypes.c_int),
    ('num_warnings', ctypes.c_long),
    ('jpeg_message_table', ctypes.POINTER(ctypes.c_char_p)),
    ('last_jpeg_message', ctypes.c_int),
    ('addon_message_table', ctypes.POINTER(ctypes.c_char_p)),
    ('first_addon_message', ctypes.c_int),
    ('last_addon_message', ctypes.c_int),
    ('setjmp_buffer', jmp_buf),
)


def register_function(funcname, restype, argtypes, asFuncname=None):
    func = _jpeg.__getattr__(funcname)
    func.restype = restype
    func.argtypes = argtypes
    if asFuncname is None:
        asFuncname = funcname
    funcs[asFuncname] = func

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

for funcname, res, args, nickname in funcs_metadata:
    register_function(funcname, res, args, nickname)


class JPEGImage(object):

    MODE_DCT = 1
    MODE_RGB = 2

    @classmethod
    def open(cls, filename, mode=MODE_DCT):
        f = open(filename, 'rb')
        contents = f.read()
        cinfo = jpeg_decompress_struct()
        jerr = jpeg_error_mgr()
        cinfo.err = funcs['jStdError'](ctypes.byref(jerr))
        jerr.error_exit = error_exit
        funcs['jCreaDecompress'](
            ctypes.byref(cinfo),
            JPEG_LIB_VERSION, ctypes.sizeof(jpeg_decompress_struct)
        )
        ## use `jMemSrc` instead
        # infile = cfopen(b'lfs.jpg', b'rb')
        # funcs['jStdSrc'](ctypes.byref(cinfo), infile)
        funcs['jMemSrc'](ctypes.byref(cinfo), contents, len(contents))
        funcs['jReadHeader'](ctypes.byref(cinfo), True)

        obj = cls()
        obj.size = (cinfo.image_width, cinfo.image_height)
        obj._color_space = cinfo.jpeg_color_space
        obj.progressive_mode = bool(cinfo.progressive_mode)
        obj.optimize_coding = False

        # 颜色分量信息
        # 把指针转化为指向cinfo.num_components个jpeg_component_info结构体的指针
        obj.comp_infos = []
        ComponentInfoArrayType = ctypes.POINTER(
            cinfo.num_components * jpeg_component_info
        )
        comps = ctypes.cast(cinfo.comp_info, ComponentInfoArrayType)
        for comp in comps.contents:
            comp_info = {}
            for key, _ in jpeg_component_info._fields_:
                comp_info[key] = comp.__getattribute__(key)
            obj.comp_infos.append(comp_info)

        # 量化表
        obj.quant_tbls = []
        for quant_tbl_ptr in cinfo.quant_tbl_ptrs:
            tbl = {}
            try:
                tbl['quantval'] = [_ for _ in quant_tbl_ptr.contents.quantval]
            except ValueError:
                pass
            else:
                obj.quant_tbls.append(tbl)

        # 哈夫曼表
        obj.dc_huff_tbl = []
        for huff_tbl_ptr in cinfo.dc_huff_tbl_ptrs:
            tbl = {}
            try:
                tbl['bits'] = [_ for _ in huff_tbl_ptr.contents.bits]
                tbl['huffval'] = [_ for _ in huff_tbl_ptr.contents.huffval]
            except ValueError:
                pass
            else:
                obj.dc_huff_tbl.append(tbl)
        obj.ac_huff_tbl = []
        for huff_tbl_ptr in cinfo.ac_huff_tbl_ptrs:
            tbl = {}
            try:
                tbl['bits'] = [_ for _ in huff_tbl_ptr.contents.bits]
                tbl['huffval'] = [_ for _ in huff_tbl_ptr.contents.huffval]
            except ValueError:
                pass
            else:
                obj.ac_huff_tbl.append(tbl)

        # DCT/RGB data
        obj.mode = mode
        if mode == JPEGImage.MODE_DCT:
            obj.data = []
            coef_arrays = funcs['jReadCoefs'](ctypes.byref(cinfo))
            CoefArraysType = ctypes.POINTER(jvirt_barray_ptr * cinfo.num_components)
            coef_arrays = ctypes.cast(coef_arrays, CoefArraysType)
            for i, coef_array in enumerate(coef_arrays.contents):
                comp = obj.comp_infos[i]
                block_array = coef_array.contents.mem_buffer
                component_blocks = []
                for nrow in range(comp['height_in_blocks']):
                    block_row = cinfo.mem.contents.access_virt_barray(
                        ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                        coef_array, nrow, 1, int(False)
                    )
                    block_row = ctypes.cast(
                        block_row.contents, ctypes.POINTER(
                            JBLOCK * comp['width_in_blocks']
                        )
                    )
                    for block in block_row.contents:
                        component_blocks.append(list(block))
                obj.data.append(component_blocks)
        elif mode == JPEGImage.MODE_RGB:
            obj.data = []
            funcs['jStrtDecompress'](ctypes.byref(cinfo))
            row_stride = cinfo.output_width * cinfo.output_components
            buf = cinfo.mem.contents.alloc_sarray(
                ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                JPOOL_IMAGE, row_stride, 1
            )
            while cinfo.output_scanline < cinfo.output_height:
                funcs['jReadScanlines'](
                    ctypes.byref(cinfo), buf, 1
                )
                tbuf = ctypes.cast(
                    buf.contents,
                    ctypes.POINTER(JSAMPLE*row_stride)
                )
                for ncol in range(0, row_stride, 3):
                    rgb = [_ for _ in tbuf.contents[ncol:ncol+3]]
                    obj.data.append(rgb)

        funcs['jFinDecompress'](ctypes.byref(cinfo))
        funcs['jDestDecompress'](ctypes.byref(cinfo))
        return obj

    ## 黑科技.强行解析地址.
    # def getNextBlockPtr(block):
    #     addr = ctypes.addressof(block)
    #     addr += ctypes.sizeof(JBLOCK)
    #     return ctypes.cast(addr, ctypes.POINTER(JBLOCK))

    def copy(self):
        obj = deepcopy(self)
        return obj

    def save(self, filename, quality=75):
        cinfo = jpeg_compress_struct()
        jerr = jpeg_error_mgr()
        cinfo.err = funcs['jStdError'](ctypes.byref(jerr))
        jerr.error_exit = error_exit
        funcs['jCreaCompress'](
            ctypes.byref(cinfo),
            JPEG_LIB_VERSION, ctypes.sizeof(jpeg_compress_struct)
        )
        fp = cfopen(filename.encode(), b'wb')
        funcs['jStdDest'](ctypes.byref(cinfo), fp)
        cinfo.image_width, cinfo.image_height = self.size
        if self.mode == JPEGImage.MODE_RGB:
            cinfo.input_components = 3  # 3 for R,G,B
            cinfo.in_color_space = J_COLOR_SPACE.JCS_RGB
            funcs['jSetDefaults'](ctypes.byref(cinfo))
            funcs['jSetQuality'](ctypes.byref(cinfo), quality, int(True))

            funcs['jStrtCompress'](ctypes.byref(cinfo), int(True))

            bdata = b''.join(
                bytes(rgb) for rgb in self.data
            )
            row_stride = cinfo.image_width * 3
            rowcnt = 0
            while rowcnt < cinfo.image_height:
                row = ctypes.create_string_buffer(
                    bdata[rowcnt*row_stride:(rowcnt+1)*row_stride]
                )
                row_ptr = ctypes.cast(
                    ctypes.pointer(ctypes.pointer(row)),
                    JSAMPARRAY
                )
                funcs['jWrtScanlines'](ctypes.byref(cinfo), row_ptr, 1)
                rowcnt += 1

        elif self.mode == JPEGImage.MODE_DCT:
            cinfo.input_components = 3  # 3 for Y,Cr,Cb
            cinfo.jpeg_color_space = self._color_space

            cinfo.in_color_space = J_COLOR_SPACE.JCS_YCbCr
            cinfo.optimize_coding = int(self.optimize_coding)

            funcs['jSetDefaults'](ctypes.byref(cinfo))

            cinfo.in_color_space = 3
            cinfo.num_components = 3
            cinfo.jpeg_width, cinfo.jpeg_height = self.size

            if self.progressive_mode:
                funcs['jSimProgress'](ctypes.byref(cinfo))

            min_h, min_v = 16, 16
            ComponentInfoArrayType = ctypes.POINTER(
                cinfo.num_components * jpeg_component_info
            )
            comp_infos = ctypes.cast(cinfo.comp_info, ComponentInfoArrayType)

            # set params to alloc coef arrays
            coef_arrays = ctypes.cast(
                cinfo.mem.contents.alloc_small(
                    ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                    JPOOL_IMAGE, ctypes.sizeof(jvirt_barray_ptr) * cinfo.num_components
                ),
                ctypes.POINTER(jvirt_barray_ptr * cinfo.num_components)
            )

            # `min_DCT_h(v)_scaled_size` must be filled
            for i, comp_info in enumerate(comp_infos.contents):
                comp_info.component_index = self.comp_infos[i]['component_index']
                comp_info.component_id = self.comp_infos[i]['component_id']
                comp_info.quant_tbl_no = self.comp_infos[i]['quant_tbl_no']
                comp_info.ac_tbl_no = self.comp_infos[i]['ac_tbl_no']
                comp_info.dc_tbl_no = self.comp_infos[i]['dc_tbl_no']

                comp_info.DCT_h_scaled_size = self.comp_infos[i]['DCT_h_scaled_size']
                comp_info.DCT_v_scaled_size = self.comp_infos[i]['DCT_v_scaled_size']
                comp_info.h_samp_factor = self.comp_infos[i]['h_samp_factor']
                comp_info.v_samp_factor = self.comp_infos[i]['v_samp_factor']
                comp_info.width_in_blocks = self.comp_infos[i]['width_in_blocks']
                comp_info.height_in_blocks = self.comp_infos[i]['height_in_blocks']

                # allocate the space of coef arrays
                coef_array = cinfo.mem.contents.request_virt_barray(
                    ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                    JPOOL_IMAGE, int(True),
                    jround_up(comp_info.width_in_blocks, comp_info.h_samp_factor),
                    jround_up(comp_info.height_in_blocks, comp_info.v_samp_factor),
                    comp_info.v_samp_factor
                )
                coef_arrays.contents.__setitem__(i, coef_array)
                min_h = min(min_h, self.comp_infos[i]['DCT_h_scaled_size'])
                min_v = min(min_v, self.comp_infos[i]['DCT_v_scaled_size'])
            cinfo.min_DCT_h_scaled_size = min_h
            cinfo.min_DCT_v_scaled_size = min_v

            # realize virtual block arrays
            funcs['jWrtCoefs'](
                ctypes.byref(cinfo),
                ctypes.cast(coef_arrays, ctypes.POINTER(jvirt_barray_ptr))
            )

            # populate the array with the DCT coefficients
            for i, (comp_info, coef_array) in enumerate(
                zip(self.comp_infos, coef_arrays.contents)
            ):

                for nrow in range(comp_info['height_in_blocks']):

                    block_row = cinfo.mem.contents.access_virt_barray(
                        ctypes.cast(ctypes.byref(cinfo), j_common_ptr),
                        coef_array, nrow, 1, int(True)
                    )
                    block_row = ctypes.cast(
                        block_row.contents, ctypes.POINTER(
                            JBLOCK * comp_info['width_in_blocks']
                        )
                    )
                    for ncol in range(comp_info['width_in_blocks']):
                        block = JBLOCK()
                        for j in range(DCTSIZE2):
                            block[j] = \
                                self.data[i][nrow*comp_info['width_in_blocks']+ncol][j]
                        block_row.contents.__setitem__(
                            ncol, block
                        )

            # get the quantization tables
            for i, quant_table in enumerate(self.quant_tbls):
                # type of quant_table is c_ushort_Array_64
                for j in range(DCTSIZE2):
                    cinfo.quant_tbl_ptrs[i].contents.quantval[j] = \
                        self.quant_tbls[i]['quantval'][j]

        # release resources
        funcs['jFinCompress'](ctypes.byref(cinfo))
        funcs['jDestCompress'](ctypes.byref(cinfo))
        cfclose(fp)


def main():
    print(funcs.keys())
    embed()
    img = JPEGImage.open('lfs.jpg', True)
    img.save('lfs_t.jpg')

if __name__ == '__main__':
    main()
