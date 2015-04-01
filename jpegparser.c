#include <stdlib.h>
#include <stdio.h>
#include <setjmp.h>
#include <assert.h>

#include <jpeglib.h>

#include <Python/Python.h>

#define MIN(a,b) (a)<(b)?(a):(b)

long jround_up (long a, long b)
/* Compute a rounded up to next multiple of b, ie, ceil(a/b)*b */
/* Assumes a >= 0, b > 0 */
{
  a += b - 1L;
  return a - (a % b);
}

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
typedef enum {          /* Operating modes for buffer controllers */
    JBUF_PASS_THRU,     /* Plain stripwise operation */
    /* Remaining modes require a full-image buffer to have been created */
    JBUF_SAVE_SOURCE,   /* Run source subobject only, save output */
    JBUF_CRANK_DEST,    /* Run dest subobject only, using saved data */
    JBUF_SAVE_AND_PASS  /* Run both subobjects, save output */
} J_BUF_MODE;
/* Coefficient buffer control */
struct jpeg_c_coef_controller {
  JMETHOD(void, start_pass, (j_compress_ptr cinfo, J_BUF_MODE pass_mode));
  JMETHOD(boolean, compress_data, (j_compress_ptr cinfo,
                   JSAMPIMAGE input_buf));
};
/* Private buffer controller object */
typedef struct {
  struct jpeg_c_coef_controller pub; /* public fields */

  JDIMENSION iMCU_row_num;  /* iMCU row # within image */
  JDIMENSION mcu_ctr;       /* counts MCUs processed in current row */
  int MCU_vert_offset;      /* counts MCU rows within iMCU row */
  int MCU_rows_per_iMCU_row;    /* number of such rows needed */

  /* Virtual block array for each component. */
  jvirt_barray_ptr * whole_image;

  /* Workspace for constructing dummy blocks at right/bottom edges. */
  JBLOCKROW dummy_buffer[C_MAX_BLOCKS_IN_MCU];
} my_coef_controller;
typedef my_coef_controller * my_coef_controller_ptr;

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
    PyObject *dctdata,
    int width, int height, int color_space,
    int progressive_mode, int optimize_coding,
    PyObject *comp_infos,
    PyObject *quant_tbls,
    PyObject *ac_huff_tables,
    PyObject *dc_huff_tables);

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
    PyObject *component, *coef;
    jvirt_barray_ptr *coef_arrays = jpeg_read_coefficients(cinfo);
    jpeg_component_info *compptr;
    for (int ci=0; ci!=cinfo->num_components; ++ci) {
        // 创建一个新的列表, 存储一个颜色分量所有DCT块
        jvirt_barray_ptr com_coef_array = coef_arrays[ci];
        JBLOCKARRAY block_array = com_coef_array->mem_buffer;
        compptr = &cinfo->comp_info[ci];
        
        int blocknum = (compptr->height_in_blocks)*(compptr->width_in_blocks);
        component = PyList_New(blocknum);
        for (int blk_y=0; blk_y<compptr->height_in_blocks; ++blk_y){
            for (int blk_x=0; blk_x<compptr->width_in_blocks; ++blk_x){
                coef = PyList_New(64);
                JCOEF *pcoef = block_array[blk_y][blk_x];
                for (int i=0; i!=DCTSIZE2; ++i){
                    PyList_SetItem(coef, i ,Py_BuildValue("i", pcoef[i]));
                }
                PyList_SetItem(component, blk_y*(compptr->width_in_blocks)+blk_x, coef);
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
    PyObject *dctdata,
    int width, int height, int color_space,
    int progressive_mode, int optimize_coding,
    PyObject *comp_infos,
    PyObject *quant_tbls,
    PyObject *ac_huff_tables,
    PyObject *dc_huff_tables)
{
    char err_msg[1024];
    memset(err_msg, 0, sizeof(err_msg));

    FILE *outfile;
    if (NULL == (outfile=fopen(filename, "wb"))){
        printf("File '%s' Open Failed!\n", filename);
        return 0;
    }
    struct jpeg_compress_struct cinfo;
    struct error_mgr_t jerr;

    cinfo.err = jpeg_std_error(&jerr.pub);
    jerr.pub.error_exit = my_error_exit;
    if (setjmp(jerr.setjmp_buffer)) {
        // handle libjpeg error
        (jerr.pub.format_message)((j_common_ptr)&cinfo, err_msg);
        printf("Error happened while handling jpeg data.\n");
        printf("libjpeg(Library errors): '%s'\n", err_msg);
        printf("Global state: %d\n", cinfo.global_state);

        jpeg_destroy_compress(&cinfo);
        fclose(outfile);

        return 0;
    }

    jpeg_create_compress(&cinfo);
    jpeg_stdio_dest(&cinfo, outfile);

    // set fields of cinfo 
    cinfo.image_width = width;
    cinfo.image_height = height;
    cinfo.jpeg_color_space = color_space;
    cinfo.input_components = PyList_Size(comp_infos);
    // printf("cinfo.input_components: %d\n", cinfo.input_components);
    cinfo.optimize_coding = optimize_coding;

    jpeg_set_defaults(&cinfo);

    // these should be cacl from above params....
    cinfo.in_color_space = 3;
    cinfo.num_components = cinfo.input_components;
    cinfo.jpeg_width = cinfo.image_width;
    cinfo.jpeg_height = cinfo.image_height;

    if ( progressive_mode == 1){
        jpeg_simple_progression(&cinfo);
    }

    int min_h=16, min_v=16;
    for (int i=0; i!=cinfo.num_components; ++i){
        PyObject *component = PyList_GetItem(comp_infos, i);

        jpeg_component_info *compptr = &cinfo.comp_info[i];
        compptr->component_index = i;
        compptr->component_id = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "component_id")));
        compptr->quant_tbl_no = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "quant_tbl_no")));
        compptr->ac_tbl_no = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "ac_tbl_no")));
        compptr->dc_tbl_no = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "dc_tbl_no")));
        compptr->h_samp_factor = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "h_samp_factor")));
        compptr->v_samp_factor = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "v_samp_factor")));

        compptr->DCT_h_scaled_size = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "DCT_h_scaled_size")));
        compptr->DCT_v_scaled_size = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "DCT_v_scaled_size")));
        compptr->width_in_blocks = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "width_in_blocks")));
        compptr->height_in_blocks = PyLong_AsLong(
            PyDict_GetItem(component, Py_BuildValue("s", "height_in_blocks")));

        min_h = MIN(min_h, compptr->DCT_h_scaled_size);
        min_v = MIN(min_v, compptr->DCT_v_scaled_size);
    }
    // these params...
    cinfo.min_DCT_h_scaled_size = min_h;
    cinfo.min_DCT_v_scaled_size = min_v;

    jvirt_barray_ptr *coef_arrays = (jvirt_barray_ptr *)
        (cinfo.mem->alloc_small)(
            (j_common_ptr)&cinfo, JPOOL_IMAGE,
            sizeof(jvirt_barray_ptr)*cinfo.num_components
        );

    jpeg_component_info *compptr;
    for (int ci=0; ci!=cinfo.num_components; ++ci){
        compptr = &cinfo.comp_info[ci];
        coef_arrays[ci] = (cinfo.mem->request_virt_barray)
            ((j_common_ptr)&cinfo, JPOOL_IMAGE, TRUE,
             (JDIMENSION) jround_up((long) compptr->width_in_blocks, (long)compptr->h_samp_factor),
             (JDIMENSION) jround_up((long) compptr->width_in_blocks, (long)compptr->h_samp_factor),
             (JDIMENSION) compptr->v_samp_factor
            );
    }

    printf("block size: %d -> %d\n", cinfo.block_size, cinfo.min_DCT_h_scaled_size);
    for (int ci=0;ci!=cinfo.num_components; ++ci){
        printf("index, id, h_samp, v_samp: %d, %d, %d, %d\n",
            cinfo.comp_info[ci].component_index,
            cinfo.comp_info[ci].component_id,
            cinfo.comp_info[ci].h_samp_factor,
            cinfo.comp_info[ci].v_samp_factor);
        printf("DCT_h_scaled, DCT_v_scaled: %d, %d\n",
            cinfo.comp_info[ci].DCT_h_scaled_size,
            cinfo.comp_info[ci].DCT_v_scaled_size);
        printf("quant_tbl, ac_tbl, dc_tbl: %d, %d, %d\n",
            cinfo.comp_info[ci].quant_tbl_no,
            cinfo.comp_info[ci].ac_tbl_no,
            cinfo.comp_info[ci].dc_tbl_no);
        printf("blocks height, width: %d, %d\n",
            cinfo.comp_info[ci].height_in_blocks,
            cinfo.comp_info[ci].width_in_blocks);
    }

    // realize virtual block arrays
    printf("before jpeg_write_coefficients\n");
    jpeg_write_coefficients(&cinfo, coef_arrays);
    printf("after jpeg_write_coefficients\n");

    printf("block size: %d -> %d\n", cinfo.block_size, cinfo.min_DCT_h_scaled_size);
    for (int ci=0;ci!=cinfo.num_components; ++ci){
        printf("index, id, h_samp, v_samp: %d, %d, %d, %d\n",
            cinfo.comp_info[ci].component_index,
            cinfo.comp_info[ci].component_id,
            cinfo.comp_info[ci].h_samp_factor,
            cinfo.comp_info[ci].v_samp_factor);
        printf("DCT_h_scaled, DCT_v_scaled: %d, %d\n",
            cinfo.comp_info[ci].DCT_h_scaled_size,
            cinfo.comp_info[ci].DCT_v_scaled_size);
        printf("quant_tbl, ac_tbl, dc_tbl: %d, %d, %d\n",
            cinfo.comp_info[ci].quant_tbl_no,
            cinfo.comp_info[ci].ac_tbl_no,
            cinfo.comp_info[ci].dc_tbl_no);
        printf("blocks height, width: %d, %d\n",
            cinfo.comp_info[ci].height_in_blocks,
            cinfo.comp_info[ci].width_in_blocks);
    }
    
    // populate the array with the DCT coefficients
    printf("before getCoefArrays\n");
    for (int i=0; i!=cinfo.num_components; ++i){
        PyObject *component, *coef;
        component = PyDict_GetItem(dctdata, Py_BuildValue("i", i));
        compptr = &cinfo.comp_info[i];
        JBLOCKARRAY blockArray = coef_arrays[i]->mem_buffer;
        for(int row=0; row!=compptr->height_in_blocks; ++row){
            for (int col=0; col!=compptr->width_in_blocks; ++col){
                coef = PyList_GetItem(component, 
                        row*(compptr->width_in_blocks)+col);
                for (int j=0; j!=DCTSIZE2; ++j){
                    blockArray[row][col][j] = PyLong_AsLong(
                        PyList_GetItem(coef, j));
                }
                // printf("%d,", col);
            }
            // printf("\nrow: [%d]\n", row);
        }
    }
    printf("after getCoefArrays\n");

    // get the quantization tables
    Py_ssize_t sz_qtbls = PyList_Size(quant_tbls);
    for (Py_ssize_t i=0; i!=NUM_QUANT_TBLS; ++i){
        if (i < sz_qtbls){
            PyObject *quant_tbl = PyList_GetItem(quant_tbls, i);
            if (NULL == cinfo.quant_tbl_ptrs[i]){
                cinfo.quant_tbl_ptrs[i] = 
                    jpeg_alloc_quant_table((j_common_ptr)&cinfo);
                printf("New qtbl:[%zd]\n", i);
            }
            PyObject *quantval = PyDict_GetItem(quant_tbl, Py_BuildValue("s", "quantval"));
            for(int j=0; j!=DCTSIZE2; ++j){
                cinfo.quant_tbl_ptrs[i]->quantval[j] = PyLong_AsLong(
                    PyList_GetItem(quantval, j));
            }
        }else{
            cinfo.quant_tbl_ptrs[i] = NULL;
        }
    }

    // Get the AC and DC huffman tables but check for optimized coding first
    if (cinfo.optimize_coding == FALSE){
        Py_ssize_t sz_hufftbls;
        PyObject *huff_tbl, *counts, *symbols;

        sz_hufftbls = PyList_Size(ac_huff_tables);
        for (Py_ssize_t i=0; i!=NUM_HUFF_TBLS; ++i){
            if (i < sz_hufftbls){
                huff_tbl = PyList_GetItem(ac_huff_tables, i);
                if (NULL == cinfo.ac_huff_tbl_ptrs[i]){
                    cinfo.ac_huff_tbl_ptrs[i] = 
                        jpeg_alloc_huff_table((j_common_ptr)&cinfo);
                }
                counts = PyDict_GetItem(huff_tbl, Py_BuildValue("s", "counts"));
                for (int j=0; j!=16; ++j){
                    cinfo.ac_huff_tbl_ptrs[i]->bits[j+1] = PyLong_AsLong(
                        PyList_GetItem(counts, j));
                }
                symbols = PyDict_GetItem(huff_tbl, Py_BuildValue("s", "symbols"));
                for (int j=0; j!=256; ++j){
                    cinfo.ac_huff_tbl_ptrs[i]->huffval[j] = PyLong_AsLong(
                        PyList_GetItem(symbols, j));
                }
            }else{
                cinfo.ac_huff_tbl_ptrs[i] = NULL;
            }
        }

        sz_hufftbls = PyList_Size(dc_huff_tables);
        for (Py_ssize_t i=0; i!=NUM_HUFF_TBLS; ++i){
            if (i < sz_hufftbls){
                huff_tbl = PyList_GetItem(dc_huff_tables, i);
                if (NULL == cinfo.dc_huff_tbl_ptrs[i]){
                    cinfo.dc_huff_tbl_ptrs[i] = 
                        jpeg_alloc_huff_table((j_common_ptr)&cinfo);
                }
                counts = PyDict_GetItem(huff_tbl, Py_BuildValue("s", "counts"));
                for (int j=0; j!=16; ++j){
                    cinfo.dc_huff_tbl_ptrs[i]->bits[j+1] = PyLong_AsLong(
                        PyList_GetItem(counts, j));
                }
                symbols = PyDict_GetItem(huff_tbl, Py_BuildValue("s", "symbols"));
                for (int j=0; j!=256; ++j){
                    cinfo.dc_huff_tbl_ptrs[i]->huffval[j] = PyLong_AsLong(
                        PyList_GetItem(symbols, j));
                }
            }else{
                cinfo.dc_huff_tbl_ptrs[i] = NULL;
            }
        }
    }

    // TODO: copy markers

    // release resources
    jpeg_finish_compress(&cinfo);
    jpeg_destroy_compress(&cinfo);
    fclose(outfile);
    return 1;
}
