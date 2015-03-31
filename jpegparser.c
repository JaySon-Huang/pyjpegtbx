#include <stdlib.h>
#include <stdio.h>
#include <setjmp.h>
#include <assert.h>

#include <jpeglib.h>

#include <Python/Python.h>

// 必要的struct
typedef struct backing_store_struct * backing_store_ptr;
typedef struct backing_store_struct {
    void (*read_backing_store) 
        (j_common_ptr cinfo,
         backing_store_ptr info,
         void FAR * buffer_address,
         long file_offset, long byte_count);
    void (*write_backing_store)
        (j_common_ptr cinfo,
         backing_store_ptr info,
         void FAR * buffer_address,
         long file_offset, long byte_count);
    void (*close_backing_store)
        (j_common_ptr cinfo,
         backing_store_ptr info);

    FILE * temp_file;
    char temp_name[64];
} backing_store_info;

struct jvirt_barray_control {
    JBLOCKARRAY mem_buffer;   /* => the in-memory buffer 指向内存缓冲区 */
    JDIMENSION rows_in_array; /* total virtual array height  */
    JDIMENSION blocksperrow;  /* width of array (and of memory buffer) */
    JDIMENSION maxaccess;     /* max rows accessed by access_virt_barray */
    JDIMENSION rows_in_mem;   /* height of memory buffer 在内存中内容的高度 */
    JDIMENSION rowsperchunk;  /* allocation chunk size in mem_buffer */
    JDIMENSION cur_start_row; /* first logical row # in the buffer 内存中内容的第一行的行号 */
    JDIMENSION first_undef_row;   /* row # of first uninitialized row 第一个没有初始化的行的行号，可以看作是含数据的最后一行的后一行 */
    boolean pre_zero;     /* pre-zero mode requested? */
    boolean dirty;        /* do current buffer contents need written? 是否"脏"数据,需要写回? */
    boolean b_s_open;     /* is backing-store data valid? 有没有恢复的数据 */
    jvirt_barray_ptr next;    /* link to next virtual barray control block 下一块数据块 */
    backing_store_info b_s_info;  /* System-dependent control info 恢复数据的内容 */
};

// 异常处理. error_ptr、error_mgr_t、my_error_exit
typedef struct error_mgr_t * error_ptr;
struct error_mgr_t {
    struct jpeg_error_mgr pub;
    jmp_buf setjmp_buffer;
};
static void
my_error_exit(j_common_ptr cinfo)
{
    error_ptr myerr = (error_ptr) cinfo->err;
    (*cinfo->err->output_message) (cinfo);
    longjmp(myerr->setjmp_buffer, 1);
}

// 函数声明
PyObject *parse(char* filename, int isdct);
static PyObject *__getdct(
    struct jpeg_decompress_struct *cinfo);
static PyObject *__getdata(
    struct jpeg_decompress_struct *cinfo);
int save_from_rgb(
    char *filename,
    int width, int height, int quality,
    unsigned char *image_buffer);
int save_from_dct(
    char *filename,
    char *orifilename,
    PyObject *dctdata);

PyObject *parse(char* filename, int isdct)
{
    FILE *infile = NULL;
    if (NULL == (infile=fopen(filename, "rb"))) {
        // 打开文件失败
        Py_INCREF(Py_None);
        return Py_None;
    }

    struct jpeg_decompress_struct cinfo;
    struct error_mgr_t jerr;
    cinfo.err = jpeg_std_error(&jerr.pub);
    jerr.pub.error_exit = my_error_exit;
    if (setjmp(jerr.setjmp_buffer)) {
        // 设置jpeg异常处理
        jpeg_destroy_decompress(&cinfo);
        fclose(infile);

        Py_INCREF(Py_None);
        return Py_None;
    }
    jpeg_create_decompress(&cinfo);
    jpeg_stdio_src(&cinfo, infile);
    (void) jpeg_read_header(&cinfo, TRUE);

    PyObject *data = PyDict_New();
    // 设置 size:(width, height)
    PyDict_SetItem(data, 
        Py_BuildValue("s", "size"), 
        Py_BuildValue("(ii)", cinfo.image_width, cinfo.image_height));
    // 设置 color_space
    PyDict_SetItem(data, 
        Py_BuildValue("s", "color_space"), 
        Py_BuildValue("i", cinfo.jpeg_color_space));
    // 设置 progressive_mode
    PyDict_SetItem(data,
        Py_BuildValue("s", "progressive_mode"),
        Py_BuildValue("i", cinfo.progressive_mode));

    // 设置 ComponentsInfo
    PyObject *comp_infos = PyList_New(cinfo.num_components);
    PyObject *comp;
    for (int i=0; i!=cinfo.num_components; ++i){
        comp = PyDict_New();
        jpeg_component_info *c_comp = &cinfo.comp_info[i];
        PyDict_SetItem(comp,
            Py_BuildValue("s", "component_id"),
            Py_BuildValue("i", c_comp->component_id));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "h_samp_factor"),
            Py_BuildValue("i", c_comp->h_samp_factor));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "v_samp_factor"),
            Py_BuildValue("i", c_comp->v_samp_factor));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "quant_tbl_no"),
            Py_BuildValue("i", c_comp->quant_tbl_no));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "dc_tbl_no"),
            Py_BuildValue("i", c_comp->dc_tbl_no));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "ac_tbl_no"),
            Py_BuildValue("i", c_comp->ac_tbl_no));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "height_in_blocks"),
            Py_BuildValue("i", c_comp->height_in_blocks));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "width_in_blocks"),
            Py_BuildValue("i", c_comp->width_in_blocks));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "DCT_h_scaled_size"),
            Py_BuildValue("i", c_comp->DCT_h_scaled_size));
        PyDict_SetItem(comp,
            Py_BuildValue("s", "DCT_v_scaled_size"),
            Py_BuildValue("i", c_comp->DCT_v_scaled_size));

        PyList_SetItem(comp_infos, i, comp);
    }

    PyDict_SetItem(data,
        Py_BuildValue("s", "comp_infos"),
        comp_infos);

    // 设置 Quantization Tables
    PyObject *quant_tbls = PyList_New(0);
    for (int i=0; i!=NUM_QUANT_TBLS; ++i){
        // JQUANT_TBL *
        if (cinfo.quant_tbl_ptrs[i] == NULL){continue;}
        PyObject *quant_tbl = PyDict_New();
        PyObject *quantval = PyList_New(DCTSIZE2);
        for (int j=0; j!=DCTSIZE2; ++j){
            PyList_SetItem(quantval, j, 
                Py_BuildValue("i", cinfo.quant_tbl_ptrs[i]->quantval[j])
            );
        }
        PyDict_SetItem(quant_tbl,
            Py_BuildValue("s", "quantval"),
            quantval);
        PyList_Append(quant_tbls, quant_tbl);
    }
    PyDict_SetItem(data,
        Py_BuildValue("s", "quant_tbls"),
        quant_tbls);

    // 设置 Huffman Tables
    PyObject *dc_huff_tables = PyList_New(0);
    PyObject *ac_huff_tables = PyList_New(0);
    PyObject *huff_table, *counts, *symbols;
    for (int i=0; i!= NUM_HUFF_TBLS; ++i){
        // dc
        if (cinfo.dc_huff_tbl_ptrs[i] != NULL){
            huff_table = PyDict_New();

            counts = PyList_New(16);
            for (int j=0; j!=16; ++j){
                PyList_SetItem(counts, j, 
                    Py_BuildValue("i", cinfo.dc_huff_tbl_ptrs[i]->bits[j+1]));
            }
            PyDict_SetItem(huff_table, 
                Py_BuildValue("s", "counts"),
                counts);
            symbols = PyList_New(256);
            for (int j=0; j!= 256; ++j){
                PyList_SetItem(symbols, j, 
                    Py_BuildValue("i", cinfo.dc_huff_tbl_ptrs[i]->huffval[j]));
            }
            PyDict_SetItem(huff_table, 
                Py_BuildValue("s", "symbols"),
                symbols);

            PyList_Append(dc_huff_tables, huff_table);
        }

        // ac
        if (cinfo.ac_huff_tbl_ptrs[i] != NULL){
            huff_table = PyDict_New();

            counts = PyList_New(16);
            for (int j=0; j!=16; ++j){
                PyList_SetItem(counts, j, 
                    Py_BuildValue("i", cinfo.ac_huff_tbl_ptrs[i]->bits[j+1]));
            }
            PyDict_SetItem(huff_table, 
                Py_BuildValue("s", "counts"),
                counts);
            symbols = PyList_New(256);
            for (int j=0; j!= 256; ++j){
                PyList_SetItem(symbols, j, 
                    Py_BuildValue("i", cinfo.ac_huff_tbl_ptrs[i]->huffval[j]));
            }
            PyDict_SetItem(huff_table, 
                Py_BuildValue("s", "symbols"),
                symbols);

            PyList_Append(ac_huff_tables, huff_table);
        }
    }
    PyDict_SetItem(data, 
        Py_BuildValue("s", "dc_huff_tables"),
        dc_huff_tables);
    PyDict_SetItem(data, 
        Py_BuildValue("s", "ac_huff_tables"),
        ac_huff_tables);

    // DCT数据 or RGB数据
    PyObject *rawdata = NULL;
    if ( !isdct ) {
        rawdata = __getdata(&cinfo);
    }else {
        rawdata = __getdct(&cinfo);
    }
    PyDict_SetItem(data, Py_BuildValue("s", "data"), rawdata);

    // 释放资源
    (void) jpeg_finish_decompress(&cinfo);
    jpeg_destroy_decompress(&cinfo);
    fclose(infile);

    return data;
}


static 
PyObject *__getdct(
    struct jpeg_decompress_struct *cinfo)
{
    PyObject *dict = PyDict_New();
    jvirt_barray_ptr *coef_arrays = jpeg_read_coefficients(cinfo);
    PyObject *component, *coef;
    for (int ci=0; ci!=cinfo->num_components; ++ci) {
        // 创建一个新的列表, 存储一个颜色分量所有DCT块
        jvirt_barray_ptr com_coef_array = coef_arrays[ci];
        JBLOCKARRAY block_array = com_coef_array->mem_buffer;
        
        int blocknum = (com_coef_array->rows_in_mem)*(com_coef_array->blocksperrow);
        component = PyList_New(blocknum);

        for (int row=0; row!=com_coef_array->rows_in_mem; ++row) {
            for (int col=0; col!=com_coef_array->blocksperrow; ++col) {
                // 创建一个列表, 存储64个DCT分量
                coef = PyList_New(64);
                JCOEF *pcoef = block_array[row][col];
                for (int i=0; i!=DCTSIZE2; ++i) {
                    PyList_SetItem(coef, i, Py_BuildValue("i", pcoef[i]));
                }
                PyList_SetItem(component, row*(com_coef_array->blocksperrow) + col, coef);
            }
        }
        // 添加到返回的字典中
        PyDict_SetItem(dict, Py_BuildValue("i", ci), component);
    }

    return dict;
}

static PyObject *__getdata(
    struct jpeg_decompress_struct *cinfo)
{
    (void) jpeg_start_decompress(cinfo);
    PyObject *data = PyList_New(0);
    int row_stride;       /* physical row width in output buffer */
    JSAMPARRAY buffer;        /* Output row buffer */
    row_stride = cinfo->output_width * cinfo->output_components;
    buffer = (cinfo->mem->alloc_sarray)
        ((j_common_ptr) cinfo, JPOOL_IMAGE, row_stride, 1);

    while (cinfo->output_scanline < cinfo->output_height) {
        (void) jpeg_read_scanlines(cinfo, buffer, 1);
        for (int cols=0; cols < row_stride; cols+=3){
            PyList_Append(data, 
                Py_BuildValue("(iii)", 
                    (*buffer)[cols], (*buffer)[cols+1], (*buffer)[cols+2])
            );
        }
    }
    return data;
}

int save_from_rgb(
    char *filename,
    int width, int height, int quality,
    unsigned char *image_buffer)
{
    FILE *outfile = NULL;
    if (NULL == (outfile=fopen(filename, "wb"))){
        // 打开文件失败
        return 0;
    }

    struct jpeg_compress_struct cinfo;
    struct error_mgr_t jerr;
    cinfo.err = jpeg_std_error(&jerr.pub);
    jerr.pub.error_exit = my_error_exit;
    if (setjmp(jerr.setjmp_buffer)) {
        // 设置jpeg异常处理
        jpeg_destroy_compress(&cinfo);
        fclose(outfile);
        return 0;
    }
    jpeg_create_compress(&cinfo);
    jpeg_stdio_dest(&cinfo, outfile);

    // 设置图像高宽
    cinfo.image_width = width;
    cinfo.image_height = height;
    // 设置输入为rgb数据流
    cinfo.input_components = 3;
    cinfo.in_color_space = JCS_RGB;
    // 设置默认参数
    jpeg_set_defaults(&cinfo);
    // 设置质量因子
    jpeg_set_quality(&cinfo, quality, TRUE);
    jpeg_start_compress(&cinfo, TRUE);

    int row_stride = width * 3;
    JSAMPROW row_pointer[1];
    while (cinfo.next_scanline < cinfo.image_height) {
        row_pointer[0] = & image_buffer[cinfo.next_scanline * row_stride];
        (void) jpeg_write_scanlines(&cinfo, row_pointer, 1);
    }

    jpeg_finish_compress(&cinfo);
    fclose(outfile);
    jpeg_destroy_compress(&cinfo);

    return 1;
}

typedef enum {
    JCOPYOPT_NONE,      /* copy no optional markers */
    JCOPYOPT_COMMENTS,  /* copy only comment (COM) markers */
    JCOPYOPT_ALL        /* copy all optional markers */
} JCOPY_OPTION;

int save_from_dct(
    char *filename,
    char *orifilename,
    PyObject *dctdata)
{
    FILE *infile=NULL, *outfile=NULL;
    if (NULL == (infile=fopen(orifilename, "rb"))
        || NULL == (outfile=fopen(filename, "wb")) ){
        // 打开文件失败
        return 0;
    }
    struct jpeg_decompress_struct srcinfo;
    struct jpeg_compress_struct dstinfo;
    struct error_mgr_t jsrcerr, jdsterr;

    // Initialize the JPEG decompression object with default error handling.
    srcinfo.err = jpeg_std_error(&jsrcerr.pub);
    jsrcerr.pub.error_exit = my_error_exit;
    if (setjmp(jsrcerr.setjmp_buffer)) {
        // 设置jpeg异常处理
        jpeg_destroy_decompress(&srcinfo);
        jpeg_destroy_compress(&dstinfo);
        fclose(infile);
        fclose(outfile);
        return 0;
    }
    // Initialize the JPEG compression object with default error handling.
    dstinfo.err = jpeg_std_error(&jdsterr.pub);
    jdsterr.pub.error_exit = my_error_exit;
    if (setjmp(jdsterr.setjmp_buffer)) {
        // 设置jpeg异常处理
        jpeg_destroy_decompress(&srcinfo);
        jpeg_destroy_compress(&dstinfo);
        fclose(infile);
        fclose(outfile);
        return 0;
    }

    jpeg_create_decompress(&srcinfo);
    jpeg_create_compress(&dstinfo);

    jpeg_stdio_src(&srcinfo, infile);
    JCOPY_OPTION copyoption = JCOPYOPT_ALL;
    // FIXME: mark数据 
    // jcopy_markers_setup(&srcinfo, copyoption);
    (void) jpeg_read_header(&srcinfo, TRUE);

    jvirt_barray_ptr * src_coef_arrays = jpeg_read_coefficients(&srcinfo);
    // Initialize destination compression parameters from source values
    jpeg_copy_critical_parameters(&srcinfo, &dstinfo);
    jvirt_barray_ptr * dst_coef_arrays = src_coef_arrays;

    PyObject *component, *coef;
    PyObject *index;
    for (int ci=0; ci!=3; ++ci){
        jvirt_barray_ptr com_coef_array = dst_coef_arrays[ci];
        JBLOCKARRAY block_array = com_coef_array->mem_buffer;

        index = Py_BuildValue("i", ci);
        component = PyDict_GetItem(dctdata, index);
        Py_DECREF(index);

        // component 是一个 list, 每一个元素为一个coef
        Py_ssize_t len_component = PyList_GET_SIZE(component);
        for (int row=0; row!=com_coef_array->rows_in_mem; ++row) {
            for (int col=0; col!=com_coef_array->blocksperrow; ++col) {
                // coef 存储64个DCT分量
                coef = PyList_GetItem(component, row*(com_coef_array->blocksperrow) + col);
                JCOEF *pcoef = block_array[row][col];
                for (int i=0; i!=DCTSIZE2; ++i) {
                    PyObject *pyval = PyList_GetItem(coef, i);
                    int val = PyLong_AsLong(pyval);
                    pcoef[i] = val;
                }
            }
        }
    }

    // 关闭读文件
    fclose(infile);

    jpeg_stdio_dest(&dstinfo, outfile);
    // Start compressor (note no image data is actually written here)
    jpeg_write_coefficients(&dstinfo, dst_coef_arrays);
    // FIXME: 保存marker信息
    // Copy to the output file any extra markers that we want to preserve
    // jcopy_markers_execute(&srcinfo, &dstinfo, copyoption);

    // 释放资源
    jpeg_finish_compress(&dstinfo);
    jpeg_destroy_compress(&dstinfo);
    (void) jpeg_finish_decompress(&srcinfo);
    jpeg_destroy_decompress(&srcinfo);
    fclose(outfile);
    return 1;
}
