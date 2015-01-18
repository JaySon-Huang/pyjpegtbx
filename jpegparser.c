#include <stdlib.h>
#include <stdio.h>
#include <jpeglib.h>
#include <setjmp.h>
#include <Python/Python.h>
#include <assert.h>

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
    PyDict_SetItem(data, 
        Py_BuildValue("s", "size"), 
        Py_BuildValue("(ii)", cinfo.image_width, cinfo.image_height));
    PyDict_SetItem(data, 
        Py_BuildValue("s", "color_space"), 
        Py_BuildValue("i", cinfo.jpeg_color_space));

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

int save_from_dct()
{
    return 1;
}
