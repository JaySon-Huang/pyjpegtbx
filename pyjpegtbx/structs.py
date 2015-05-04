#!/usr/bin/env python
#encoding=utf-8

import ctypes
from .constants import (
    DCTSIZE2, MAX_COMPS_IN_SCAN, C_MAX_BLOCKS_IN_MCU, D_MAX_BLOCKS_IN_MCU,
    NUM_QUANT_TBLS, NUM_HUFF_TBLS, NUM_ARITH_TBLS
)

boolean = ctypes.c_int
JSAMPLE = ctypes.c_char
JSAMPROW = ctypes.POINTER(JSAMPLE)
JSAMPARRAY = ctypes.POINTER(JSAMPROW)

JCOEF = ctypes.c_short
JBLOCK = JCOEF * DCTSIZE2
JBLOCK.__repr__ = lambda self: 'JBLOCK @ %x' % ctypes.addressof(self)
JBLOCKROW = ctypes.POINTER(JBLOCK)
JBLOCKARRAY = ctypes.POINTER(JBLOCKROW)
jmp_buf = ctypes.c_int * 37


class J_COLOR_SPACE(object):
    JCS_UNKNOWN = 0     # error/unspecified
    JCS_GRAYSCALE = 1   # monochrome
    JCS_RGB = 2         # red/green/blue, standard RGB (sRGB)
    JCS_YCbCr = 3       # Y/Cb/Cr (also known as YUV), standard YCC
    JCS_CMYK = 4        # C/M/Y/K
    JCS_YCCK = 5        # Y/Cb/Cr/K
    JCS_BG_RGB = 6      # big gamut red/green/blue, bg-sRGB
    JCS_BG_YCC = 7      # big gamut Y/Cb/Cr, bg-sYCC


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

    fields_needed = (
        'component_id',
        'component_index',
        'h_samp_factor',
        'v_samp_factor',
        'quant_tbl_no',
        'dc_tbl_no',
        'ac_tbl_no',
        'width_in_blocks',
        'height_in_blocks',
        'DCT_h_scaled_size',
        'DCT_v_scaled_size',
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

ERROR_EXIT_FUNC = ctypes.CFUNCTYPE(None, j_common_ptr)


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
