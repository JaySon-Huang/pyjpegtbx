#!/usr/bin/env python
#encoding=utf-8

import ctypes

_all_libs = (
    ('jpeg.dll', 'libjpeg.so', 'libjpeg.dylib'),
    ('c.dll', 'libc.so', 'libc.dylib'),
)


def __loadLib(liblst):
    found = False
    for lib in liblst:
        try:
            _lib = ctypes.cdll.LoadLibrary('libjpeg.dylib')
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

# boolean is char : ctypes.c_char
# JDIMENSION is unsigned int : ctypes.c_uint

# typedef enum {
#     JCS_UNKNOWN,        /* error/unspecified */
#     JCS_GRAYSCALE,      /* monochrome */
#     JCS_RGB,        /* red/green/blue, standard RGB (sRGB) */
#     JCS_YCbCr,      /* Y/Cb/Cr (also known as YUV), standard YCC */
#     JCS_CMYK,       /* C/M/Y/K */
#     JCS_YCCK,       /* Y/Cb/Cr/K */
#     JCS_BG_RGB,     /* big gamut red/green/blue, bg-sRGB */
#     JCS_BG_YCC      /* big gamut Y/Cb/Cr, bg-sYCC */
# } J_COLOR_SPACE;

JSAMPLE = ctypes.c_char
JSAMPROW = ctypes.POINTER(JSAMPLE)
JSAMPARRAY = ctypes.POINTER(JSAMPLE)

JCOEF = ctypes.c_short
JBLOCK = JCOEF * DCTSIZE2
JBLOCKROW = ctypes.POINTER(JBLOCK)
JBLOCKARRAY = ctypes.POINTER(JBLOCKROW)
jmp_buf = ctypes.c_int * 37


class jpeg_error_mgr(ctypes.Structure):
    pass


class JQUANT_TBL(ctypes.Structure):
    _fields_ = (
        ('quantval', ctypes.c_uint16 * DCTSIZE2),
        ('sent_table', ctypes.c_int),
    )


class JHUFF_TBL(ctypes.Structure):
    _fields_ = (
        ('bits', ctypes.c_uint8 * 17),
        ('huffval', ctypes.c_uint8 * 256),
        ('sent_table', ctypes.c_int),
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
        ('component_needed', ctypes.c_int),
        ('MCU_width', ctypes.c_int),
        ('MCU_height', ctypes.c_int),
        ('MCU_blocks', ctypes.c_int),
        ('MCU_sample_width', ctypes.c_int),
        ('last_col_width', ctypes.c_int),
        ('last_row_height', ctypes.c_int),
        ('quant_table', ctypes.POINTER(JQUANT_TBL)),
        ('dct_table', ctypes.c_void_p),
    )


class jpeg_compress_struct(ctypes.Structure):
    _fields_ = (
        ('err', ctypes.c_void_p),
        ('mem', ctypes.c_void_p),
        ('progress', ctypes.c_void_p),
        ('client_data', ctypes.c_void_p),
        ('is_decompressor', ctypes.c_char),
        ('global_state', ctypes.c_int),

        ('dest', ctypes.c_void_p),
        ('image_width', ctypes.c_uint),
        ('image_height', ctypes.c_uint),
        ('input_components', ctypes.c_int),
        ('in_color_space', ctypes.c_int),
        ('input_gamma', ctypes.c_double),
        ('scale_num', ctypes.c_uint),
        ('scale_denom', ctypes.c_uint),
        ('jpeg_width', ctypes.c_uint),
        ('jpeg_height', ctypes.c_uint),
        ('data_precision', ctypes.c_int),
        ('num_components', ctypes.c_int),
        ('jpeg_color_space', ctypes.c_int),
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
        ('raw_data_in', ctypes.c_char),
        ('arith_code', ctypes.c_char),
        ('optimize_coding', ctypes.c_char),
        ('CCIR601_sampling', ctypes.c_char),
        ('do_fancy_downsampling', ctypes.c_char),
        ('smoothing_factor', ctypes.c_int),
        ('dct_method', ctypes.c_void_p),
        ('restart_interval', ctypes.c_uint),
        ('restart_in_rows', ctypes.c_int),
        ('write_JFIF_header', ctypes.c_char),
        ('JFIF_major_version', ctypes.c_uint8),
        ('JFIF_minor_version', ctypes.c_uint8),
        ('density_unit', ctypes.c_uint8),
        ('X_density', ctypes.c_uint16),
        ('Y_density', ctypes.c_uint16),
        ('write_Adobe_marker', ctypes.c_char),
        ('color_transform', ctypes.c_int),
        ('next_scanline', ctypes.c_uint),
        ('progressive_mode', ctypes.c_char),
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


class jpeg_common_struct(ctypes.Structure):
    _fields_ = (
        ('err', ctypes.c_void_p),
        ('mem', ctypes.c_void_p),
        ('progress', ctypes.c_void_p),
        ('client_data', ctypes.c_void_p),
        ('is_decompressor', ctypes.c_char),
        ('global_state', ctypes.c_int),
    )
j_common_ptr = ctypes.POINTER(jpeg_common_struct)


class jpeg_decompress_struct(ctypes.Structure):
    _fields_ = (
        ('err', ctypes.POINTER(jpeg_error_mgr)),
        ('mem', ctypes.c_void_p),
        ('progress', ctypes.c_void_p),
        ('client_data', ctypes.c_void_p),
        ('is_decompressor', ctypes.c_char),
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

        ('buffered_image', ctypes.c_int),
        ('raw_data_out', ctypes.c_int),

        ('dct_method', ctypes.c_int),  # offset: 96
        ('do_fancy_upsampling', ctypes.c_int),  # offset: 100
        ('do_block_smoothing', ctypes.c_int),

        ('quantize_colors', ctypes.c_int),  # offset: 108

        ('dither_mode', ctypes.c_int),
        ('two_pass_quantize', ctypes.c_int),
        ('desired_number_of_colors', ctypes.c_int),  # offset: 120

        ('enable_1pass_quant', ctypes.c_int),
        ('enable_external_quant', ctypes.c_int),
        ('enable_2pass_quant', ctypes.c_int),

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

        ('is_baseline', ctypes.c_int),
        ('progressive_mode', ctypes.c_int),
        ('arith_code', ctypes.c_int),

        ('arith_dc_L', ctypes.c_uint8 * NUM_ARITH_TBLS),
        ('arith_dc_U', ctypes.c_uint8 * NUM_ARITH_TBLS),
        ('arith_ac_K', ctypes.c_uint8 * NUM_ARITH_TBLS),

        ('restart_interval', ctypes.c_uint),

        ('saw_JFIF_marker', ctypes.c_int),  # 376

        ('JFIF_major_version', ctypes.c_uint8),
        ('JFIF_minor_version', ctypes.c_uint8),
        ('density_unit', ctypes.c_uint8),
        ('X_density', ctypes.c_uint16),
        ('Y_density', ctypes.c_uint16),
        ('saw_Adobe_marker', ctypes.c_int),
        ('Adobe_transform', ctypes.c_uint8),

        ('CCIR601_sampling', ctypes.c_int),

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
    ('pre_zero', ctypes.c_char),
    ('dirty', ctypes.c_char),
    ('b_s_open', ctypes.c_char),
    ('next', ctypes.POINTER(jvirt_barray_control)),
    ('b_s_info', backing_store_info),
)

funcs = {}
cfopen = _c.fopen
cfopen.restype = ctypes.c_void_p
cfopen.argtypes = (ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_char))
csetjmp = _c.setjmp
csetjmp.restype = ctypes.c_int
csetjmp.argtypes = (jmp_buf,)
clongjmp = _c.longjmp
clongjmp.restype = None
clongjmp.argtypes = (jmp_buf, ctypes.c_int)
ERROR_EXIT_FUNC = ctypes.CFUNCTYPE(None, j_common_ptr)
def py_error_exit(cinfo):
    print('error_exit')
    clongjmp(cinfo.err.setjmp_buffer, 1)
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
    # if funcname == 'jpeg_CreateDecompress':
    #     func = lambda cinfo: _func(cinfo, JPEG_LIB_VERSION, ctypes.sizeof(jpeg_decompress_struct))
    # elif funcname == 'jpeg_CreateCompress':
    #     func = lambda cinfo: _func(cinfo, JPEG_LIB_VERSION, ctypes.sizeof(jpeg_compress_struct))
    # else:
    #     func = _func
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
        (),
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

    ('jpeg_start_compress',
        None,
        (),
        'jStrtCompress'),
    ('jpeg_start_decompress',
        None,
        (),
        'jStrtDecompress'),

    ('jpeg_read_header',
        None,
        (j_decompress_ptr, ctypes.c_bool),
        'jReadHeader'),
    ('jpeg_set_defaults',
        None,
        (),
        'jSetDefaults'),
    ('jpeg_set_quality',
        None,
        (),
        'jSetQuality'),
    ('jpeg_simple_progression',
        None,
        (),
        'jSimProgress'),

    ('jpeg_read_scanlines',
        None,
        (),
        'jReadScanlines'),
    ('jpeg_write_scanlines',
        None,
        (),
        'jWrtScanlines'),

    ('jpeg_read_coefficients',
        None,
        (),
        'jReadCoefs'),
    ('jpeg_write_coefficients',
        None,
        (),
        'jWrtCoefs'),

    ('jpeg_finish_decompress',
        None,
        (),
        'jFinDecompress'),
    ('jpeg_finish_compress',
        None,
        (),
        'jFinCompress'),

    ('jpeg_destroy_compress',
        None,
        (),
        'jDestCompress'),
    ('jpeg_destroy_decompress',
        None,
        (),
        'jDestDecompress'),
)

for funcname, res, args, nickname in funcs_metadata:
    register_function(funcname, res, args, nickname)


class JPEGImage(object):
    @classmethod
    def getInstanceFromcinfo(cls, cinfo):
        from IPython import embed
        obj = cls()
        obj.size = (cinfo.image_width, cinfo.image_height)
        obj._color_space = cinfo.jpeg_color_space
        obj.progressive_mode = bool(cinfo.progressive_mode)
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

        # DCT/RGB数据
        embed()

        return obj


def parse():
    print(funcs.keys())
    f = open('lfs.jpg', 'rb')
    contents = f.read()
    cinfo = jpeg_decompress_struct()
    jerr = jpeg_error_mgr()
    cinfo.err = funcs['jStdError'](ctypes.byref(jerr))
    jerr.error_exit = error_exit
    # infile = cfopen(b'lfs.jpg', b'rb')
    print(ctypes.sizeof(jpeg_decompress_struct))
    funcs['jCreaDecompress'](ctypes.byref(cinfo), JPEG_LIB_VERSION, ctypes.sizeof(jpeg_decompress_struct))
    print(cinfo.global_state)
    # funcs['jStdSrc'](ctypes.byref(cinfo), infile)
    funcs['jMemSrc'](ctypes.byref(cinfo), contents, len(contents))
    funcs['jReadHeader'](ctypes.byref(cinfo), True)

    img = JPEGImage.getInstanceFromcinfo(cinfo)
parse()
