#!/usr/bin/env python
#encoding=utf-8

import ctypes
import fractions
from .constants import (
    DCTSIZE2, MAX_COMPS_IN_SCAN, C_MAX_BLOCKS_IN_MCU, D_MAX_BLOCKS_IN_MCU,
    NUM_QUANT_TBLS, NUM_HUFF_TBLS, NUM_ARITH_TBLS
)
from .utils import BytesReader

boolean = ctypes.c_int
# Representation of a single sample (pixel element value). defined in `jmorecfg.h`
JSAMPLE = ctypes.c_char
# Representation of a DCT frequency coefficient. defined in `jmorecfg.h`
JCOEF = ctypes.c_short

## defined in `jpeglib.h`
# ptr to one image row of pixel samples. 
JSAMPROW = ctypes.POINTER(JSAMPLE)
# ptr to some rows (a 2-D sample array).
JSAMPARRAY = ctypes.POINTER(JSAMPROW)

# one block of coefficients 
JBLOCK = JCOEF * DCTSIZE2
JBLOCK.__repr__ = lambda self: 'JBLOCK @ %x' % ctypes.addressof(self)
# pointer to one row of coefficient blocks
JBLOCKROW = ctypes.POINTER(JBLOCK)
# a 2-D array of coefficient blocks
JBLOCKARRAY = ctypes.POINTER(JBLOCKROW)

jmp_buf = ctypes.c_int * 37


class J_COLOR_SPACE(object):
    '''
    enum of color space. defined in `jpeglib.h`
    '''
    JCS_UNKNOWN = 0     # error/unspecified
    JCS_GRAYSCALE = 1   # monochrome
    JCS_RGB = 2         # red/green/blue, standard RGB (sRGB)
    JCS_YCbCr = 3       # Y/Cb/Cr (also known as YUV), standard YCC
    JCS_CMYK = 4        # C/M/Y/K
    JCS_YCCK = 5        # Y/Cb/Cr/K
    JCS_BG_RGB = 6      # big gamut red/green/blue, bg-sRGB
    JCS_BG_YCC = 7      # big gamut Y/Cb/Cr, bg-sYCC


class jpeg_error_mgr(ctypes.Structure):
    '''
    Error handler object
    Note. assign to `jpeg_error_mgr._fields_` later on this file.
    '''
    pass


class jpeg_memory_mgr(ctypes.Structure):
    pass


class JQUANT_TBL(ctypes.Structure):
    '''
    DCT coefficient quantization tables.
    '''
    _fields_ = (
        ('quantval', ctypes.c_uint16 * DCTSIZE2),
        ('sent_table', boolean),
    )


class JHUFF_TBL(ctypes.Structure):
    '''
    Huffman coding tables.
    '''
    _fields_ = (
        ('bits', ctypes.c_uint8 * 17),
        ('huffval', ctypes.c_uint8 * 256),
        ('sent_table', boolean),
    )


class jpeg_component_info(ctypes.Structure):
    '''
    Basic info about one component (color channel).
    '''
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
    '''
    Common fields between JPEG compression and decompression master structs.
    '''
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
    '''
    Master record for a compression instance
    '''
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

        # added by libjpeg-9, Color transform identifier, writes LSE marker if nonzero
        ('color_transform', ctypes.c_int),

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
    '''
    Master record for a decompression instance
    '''
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

        # added by libjpeg-9, Color transform identifier derived from LSE marker, otherwise zero
        ('color_transform', ctypes.c_int),

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
    '''
    This structure holds whatever state is needed to access a single
    backing-store object.  The read/write/close method pointers are called
    by jmemmgr.c to manipulate the backing-store object; all other fields
    are private to the system-dependent backing store routines.
    defined in `jmemsys.h`
    '''
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
    ('output_message', ctypes.CFUNCTYPE(None, j_common_ptr)),
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


class IFDFormat(object):
    # (value, num of bytes)
    UByte = (1, 1)
    ASCII = (2, 1)
    UShort = (3, 2)
    ULong = (4, 4)
    URational = (5, 8)
    Byte = (6, 1)
    Undefined = (7, 1)
    Short = (8, 2)
    Long = (9, 4)
    Rational = (10, 8)
    Float = (11, 4)
    Double = (12, 8)

    FORMATS = (
        UByte, ASCII, UShort, ULong, URational,
        Byte, Undefined, Short, Long, Rational, Float, Double
    )

    def __init__(self, value):
        for val, nbytes in IFDFormat.FORMATS:
            if value == val:
                self.value = val
                self.nbytes = nbytes
                break

    def __str__(self):
        return {
            1:  'UByte',
            2:  'ASCII',
            3:  'UShort',
            4:  'ULong',
            5:  'URational',
            6:  'Byte',
            7:  'Undefined',
            8:  'Short',
            9:  'Long',
            10: 'Rational',
            11: 'Float',
            12: 'Double',
        }[self.value]

    def __repr__(self):
        return self.__str__()

    def get_comp(self, reader, byte_data, offset, num_comp):
        if self.value in (IFDFormat.UByte[0], IFDFormat.Byte[0]):
            if num_comp == 1:
                comp = byte_data[offset]
                return comp
            else:
                comps = []
                for _ in range(num_comp):
                    comp = byte_data[offset]
                    comps.append(comp)
                    offset += 1
                return comps
        elif self.value in (IFDFormat.UShort[0], IFDFormat.Short[0]):
            if num_comp == 1:
                comp = reader.bytes2uint16(byte_data[offset:offset+2])
                return comp
            else:
                comps = []
                for _ in range(num_comp):
                    comp = reader.bytes2uint16(byte_data[offset:offset+2])
                    comps.append(comp)
                    offset += 2
                return comps
        elif self.value in (IFDFormat.ULong[0], IFDFormat.Long[0]):
            if num_comp == 1:
                comp = reader.bytes2uint32(byte_data[offset:offset+4])
                return comp
            else:
                comps = []
                for _ in range(num_comp):
                    comp = reader.bytes2uint32(byte_data[offset:offset+4])
                    comps.append(comp)
                    offset += 4
                return comps
        elif self.value in (IFDFormat.URational[0], IFDFormat.Rational[0]):
            if num_comp == 1:
                numerator = reader.bytes2uint32(byte_data[offset:offset+4])
                denominator = reader.bytes2uint32(byte_data[offset+4:offset+8])
                comp = fractions.Fraction(numerator, denominator)
                return comp
            else:
                comps = []
                for _ in range(num_comp):
                    numerator = reader.bytes2uint32(byte_data[offset:offset+4])
                    denominator = reader.bytes2uint32(byte_data[offset+4:offset+8])
                    comp = fractions.Fraction(numerator, denominator)
                    comps.append(comp)
                    offset += 8  # point to next data
                return comps
        elif self.value == IFDFormat.ASCII[0]:
            comps = byte_data[offset:offset+num_comp]
            try:
                comps = comps[:comps.find(b'\x00')].decode('ascii')
            except UnicodeDecodeError:
                pass
        elif self.value == IFDFormat.Undefined[0]:
            comps = byte_data[offset:offset+num_comp]
        else:
            comp = None  # FIXME: handle Float, Double
        return comps


class IFDType(object):
    TAGS = {
        ## tags in IFD
        # Tags relating to image data structure
        0x0100: ('ImageWidth', 'Image width'),
        0x0101: ('ImageLength', 'Image height'),
        0x0102: ('BitsPerSample', 'Number of bits per component'),
        0x0103: ('Compression', 'Compression scheme'),
        0x0106: ('PhotometricInterpretation', 'Pixel composition'),
        0x0112: ('Orientation', 'Orientation of image'),
        0x0115: ('SamplesPerPixel', 'Number of components'),
        0x011c: ('PlanarConfiguration', 'Image data arrangement'),
        0x0212: ('YCbCrSubSampling', 'Subsampling ratio of Y to C'),
        0x0213: ('YCbCrPositioning', 'Y and C positioning'),
        0x011a: ('XResolution', 'Image resolution in width direction'),
        0x011b: ('YResolution', 'Image resolution in height direction'),
        0x0128: ('ResolutionUnit', 'Unit of X and Y resolution'),
        # Tags relating to recording offset
        0x0111: ('StripOffsets', 'Image data location'),
        0x0116: ('RowsPerStrip', 'Number of rows per strip'),
        0x0117: ('StripByteCounts', 'Bytes per compressed strip'),
        0x0201: ('JPEGInterchangeFormat', 'Offset to JPEG SOI'),
        0x0202: ('JPEGInterchangeFormatLength', 'Bytes of JPEG data'),
        # Tags relating to image data characteristics
        0x012d: ('TransferFunction', 'Transfer function'),
        0x013e: ('WhitePoint', 'White point chromaticity'),
        0x013f: ('PrimaryChromaticities', 'Chromaticities of primaries'),
        0x0211: ('YCbCrCoefficients', 'Color space transformation matrix coefficients'),
        0x0214: ('ReferenceBlackWhite', 'Pair of black and white reference values'),
        # Other tags
        0x0132: ('DateTime', 'File change date and time'),
        0x010e: ('ImageDescription', 'Image title'),
        0x010f: ('Make', 'Image input equipment manufacturer'),
        0x0110: ('Model', 'Image input equipment model'),
        0x0131: ('Software', 'Software used'),
        0x013b: ('Artist', 'Person who created the image'),
        0x8298: ('Copyright', 'Copyright holder'),
        # pointer to other IFDs
        0x8769: ('ExifOffset', ''),
        0x8825: ('GPSInfo', ''),
        0x0302: ('ICC Profile Descriptor', ''),
        0x5110: ('PixelUnit', ''),
        0x5111: ('PixelPerUnitX', ''),
        0x5112: ('PixelPerUnitY', ''),

        ## tags in Exif IFD
        # Tags Relating to Version
        0x9000: ('ExifVersion', 'Exif version'),
        0xa000: ('FlashpixVersion', 'Supported Flashpix version'),
        # Tag Relating to Image Data Characteristics
        0xa001: ('ColorSpace', 'Color space information'),
        0xa500: ('Gamma', 'Gamma'),
        # Tags Relating to Image Configuration
        0x9101: ('ComponentsConfiguration', 'Meaning of each component'),
        0x9102: ('CompressedBitsPerPixel', 'Image compression mode'),
        0xa002: ('PixelXDimension', 'Valid image width'),
        0xa003: ('PixelYDimension', 'Valid image height'),
        # Tags Relating to User Information
        0x927c: ('MakerNote', 'Manufacturer notes'),
        0x9286: ('UserComment', 'User comments'),
        # Tag Relating to Related File Information
        0xa004: ('RelatedSoundFile', 'Related audio file'),
        # Tags Relating to Date and Time
        0x9003: ('DateTimeOriginal', 'Date and time of original data generation'),
        0x9004: ('DateTimeDigitized', 'Date and time of digital data generation'),
        0x9290: ('SubSecTime', 'DateTime subseconds'),
        0x9291: ('SubSecTimeOriginal', 'DateTimeOriginal subseconds'),
        0x9292: ('SubSecTimeDigitized', 'DateTimeDigitized subseconds'),
        # Others Tags
        0xa420: ('ImageUniqueID', 'Unique image ID'),
        0xa430: ('CameraOwnerName', 'Camera Owner Name'),
        0xa431: ('BodySerialNumber', 'Body Serial Number'),
        0xa432: ('LensSpecification', 'Lens Specification'),
        0xa433: ('LensMake', 'Lens Make'),
        0xa434: ('LensModel', 'Lens Model'),
        0xa435: ('LensSerialNumber', 'Lens Serial Number'),
        # Tags Relating to Picture-Taking Conditions
        0x829a: ('ExposureTime', 'Exposure time'),
        0x829d: ('FNumber', 'F number'),
        0x8822: ('ExposureProgram', 'Exposure program'),
        0x8824: ('SpectralSensitivity', 'Spectral sensitivity'),
        0x8827: ('PhotographicSensitivity', 'Photographic Sensitivity'),
        0x8828: ('OECF', 'Optoelectric conversion factor'),
        0x8830: ('SensitivityType', 'Sensitivity Type'),
        0x8831: ('StandardOutputSensitivity', 'Standard Output Sensitivity'),
        0x8832: ('RecommendedExposureIndex', 'Recommended ExposureIndex'),
        0x8833: ('ISOSpeed', 'ISO Speed'),
        0x8834: ('ISOSpeedLatitudeyyy', 'ISO Speed Latitude yyy'),
        0x8835: ('ISOSpeedLatitudezzz', 'ISO Speed Latitude zzz'),
        0x9201: ('ShutterSpeedValue', 'Shutter speed'),
        0x9202: ('ApertureValue', 'Aperture'),
        0x9203: ('BrightnessValue', 'Brightness'),
        0x9204: ('ExposureBiasValue', 'Exposure bias'),
        0x9205: ('MaxApertureValue', 'Maximum lens aperture'),
        0x9206: ('SubjectDistance', 'Subject distance'),
        0x9207: ('MeteringMode', 'Metering mode'),
        0x9208: ('LightSource', 'Light source'),
        0x9209: ('Flash', 'Flash'),
        0x920a: ('FocalLength', 'Lens focal length'),
        0x9214: ('SubjectArea', 'Subject area'),
        0xa20b: ('FlashEnergy', 'Flash energy'),
        0xa20c: ('SpatialFrequencyResponse', 'Spatial frequency response'),
        0xa20e: ('FocalPlaneXResolution', 'Focal plane X resolution'),
        0xa20f: ('FocalPlaneYResolution', 'Focal plane Y resolution'),
        0xa210: ('FocalPlaneResolutionUnit', 'Focal plane resolution unit'),
        0xa214: ('SubjectLocation', 'Subject location'),
        0xa215: ('ExposureIndex', 'Exposure index'),
        0xa217: ('SensingMethod', 'Sensing method'),
        0xa300: ('FileSource', 'File source'),
        0xa301: ('SceneType', 'Scene type'),
        0xa302: ('CFAPattern', 'CFA pattern'),
        0xa401: ('CustomRendered', 'Custom image processing'),
        0xa402: ('ExposureMode', 'Exposure mode'),
        0xa403: ('WhiteBalance', 'White balance'),
        0xa404: ('DigitalZoomRatio', 'Digital zoom ratio'),
        0xa405: ('FocalLengthIn35mmFilm', 'Focal length in 35 mm film'),
        0xa406: ('SceneCaptureType', 'Scene capture type'),
        0xa407: ('GainControl', 'Gain control'),
        0xa408: ('Contrast', 'Contrast'),
        0xa409: ('Saturation', 'Saturation'),
        0xa40a: ('Sharpness', 'Sharpness'),
        0xa40b: ('DeviceSettingDescription', 'Device settings description'),
        0xa40c: ('SubjectDistanceRange', 'Subject distance range'),

        ## tags in GPS Info IFD
        0x0000: ('GPSVersionID', 'GPS tag version'),
        0x0001: ('GPSLatitudeRef', 'North or South Latitude'),
        0x0002: ('GPSLatitude', 'Latitude'),
        0x0003: ('GPSLongitudeRef', 'East or West Longitude'),
        0x0004: ('GPSLongitude', 'Longitude'),
        0x0005: ('GPSAltitudeRef', 'Altitude reference'),
        0x0006: ('GPSAltitude', 'Altitude'),
        0x0007: ('GPSTimeStamp', 'GPS time (atomic clock)'),
        0x0008: ('GPSSatellites', 'GPS satellites used for measurement'),
        0x0009: ('GPSStatus', 'GPS receiver status'),
        0x000a: ('GPSMeasureMode', 'GPS measurement mode'),
        0x000b: ('GPSDOP', 'Measurement precision'),
        0x000c: ('GPSSpeedRef', 'Speed unit'),
        0x000d: ('GPSSpeed', 'Speed of GPS receiver'),
        0x000e: ('GPSTrackRef', 'Reference for direction of movement'),
        0x000f: ('GPSTrack', 'Direction of movement'),
        0x0010: ('GPSImgDirectionRef', 'Reference for direction of image'),
        0x0011: ('GPSImgDirection', 'Direction of image'),
        0x0012: ('GPSMapDatum', 'Geodetic survey data used'),
        0x0013: ('GPSDestLatitudeRef', 'Reference for latitude of destination'),
        0x0014: ('GPSDestLatitude', 'Latitude of destination'),
        0x0015: ('GPSDestLongitudeRef', 'Reference for longitude of destination'),
        0x0016: ('GPSDestLongitude', 'Longitude of destination'),
        0x0017: ('GPSDestBearingRef', 'Reference for bearing of destination'),
        0x0018: ('GPSDestBearing', 'Bearing of destination'),
        0x0019: ('GPSDestDistanceRef', 'Reference for distance to destination'),
        0x001a: ('GPSDestDistance', 'Distance to destination'),
        0x001b: ('GPSProcessingMethod', 'Name of GPS processing method'),
        0x001c: ('GPSAreaInformation', 'Name of GPS area'),
        0x001d: ('GPSDateStamp', 'GPS date'),
        0x001e: ('GPSDifferential', 'GPS differential correction'),
        0x001f: ('GPSHPositioningError', 'Horizontal positioning error'),
    }

    def __init__(self, _type):
        try:
            self.id = _type
            self.name, self.description = self.TAGS[_type]
        except KeyError:
            self.id = _type
            self.name = '<Unknown>'
            self.description = None

    def __str__(self):
        if self.name != '<Unknown>':
            return self.name
        else:
            return '<Unknown: 0x%x>' % self.id

    def __repr__(self):
        return self.__str__()


class IFD(object):
    @classmethod
    def from_bytes(cls, reader, byte_data, offset, num):
        self = cls()
        if num is not None:
            ifds = [('IFD%d' % num, self)]
        # num of entries
        self.num_entries = reader.bytes2uint16(byte_data[offset:offset+2])
        self.entries = []
        index = offset + 2
        for i in range(self.num_entries):
            _type = IFDType(reader.bytes2uint16(byte_data[index:index+2]))
            fmt = IFDFormat(reader.bytes2uint16(byte_data[index+2:index+4]))
            ncomp = reader.bytes2uint32(byte_data[index+4:index+8])
            total_nbytes = fmt.nbytes*ncomp
            if total_nbytes > 4:  # next 4 bytes is a pointer to the true comp
                comp_offset = reader.bytes2uint32(byte_data[index+8:index+12])
                comps = fmt.get_comp(reader, byte_data, comp_offset, ncomp)
                # print(_type, fmt, ncomp, '%s @ %s' % (comps, hex(comp_offset)))
            else:  # next 4 bytes store the comp
                comps = fmt.get_comp(reader, byte_data, index+8, ncomp)
                # print(_type, fmt, ncomp, comps)
            self.entries.append(
                (_type, fmt, ncomp, comps)
            )
            index += 12

            if _type.id == 0x8769:  # Exif子IFD
                _, exif_ifd = IFD.from_bytes(reader, byte_data, offset=comps, num=None)
                ifds.append(('ExifIFD', exif_ifd))
            elif _type.id == 0x8825:  # GPSInfo
                _, GPSInfo = IFD.from_bytes(reader, byte_data, offset=comps, num=None)
                ifds.append(('GPSInfo', GPSInfo))

        # offset to next IFD
        offset = reader.bytes2uint32(byte_data[index:index+4])
        if num is not None:
            return offset, ifds
        else:
            return offset, self

    def iter_entries(self):
        for entry in self.entries:
            yield entry


class TIFF(object):

    @classmethod
    def from_bytes(cls, byte_data):
        self = cls()
        self.header = byte_data[:8]
        if self.header[:2] == b'II':
            reader = BytesReader(BytesReader.LITTLE_ENDIAN)
        elif self.header[:2] == b'MM':
            reader = BytesReader(BytesReader.BIG_ENDIAN)
        else:
            pass  # FIXME: broken data
        self.tag = reader.bytes2uint16(self.header[2:4])
        self.ifds = []
        # offset to IFD0
        num = 0
        offset = reader.bytes2uint32(self.header[4:8])
        while offset != 0:
            offset, ifds = IFD.from_bytes(reader, byte_data, offset, num)
            self.ifds.extend(ifds)
            num += 1
        return self

    def iter_IFDs(self):
        for ifd in self.ifds:
            yield ifd
