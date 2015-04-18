#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
#include <assert.h>
#include <setjmp.h>

#include <jpeglib.h>

#include <Python/Python.h>
#include <structmember.h>

#ifndef bool
#define bool int
#endif

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
    boolean pre_zero;         /* pre-zero mode requested? */
    boolean dirty;            /* do current buffer contents need written? 是否"脏"数据,需要写回? */
    boolean b_s_open;         /* is backing-store data valid? 有没有恢复的数据 */
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

// struct & functions for handling error.
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


/*
 *
 * 利用 Python - C API进行整合
 */

typedef struct {
    PyObject_HEAD
    char *_filename;        // filename in C 
    PyObject *filename;     // filename in Python
    bool isDCT;             // bool True读取DCT数据, False读取RGB数据
    PyObject *size;         // tuple (width, height)
    int color_space;        // int color space
    bool progressive_mode;  // bool progressive mode
    PyObject *data;         // ? DCT/RGB图像数据
    PyObject *comp_infos;   // tuple 
    PyObject *quant_tbls;   // tuple
    PyObject *ac_huff_tables;// tuple
    PyObject *dc_huff_tables;// tuple
    bool optimize_coding;   // bool 默认为False
} JPEGImageClassObject;

// declaration of functions
static bool __parse(JPEGImageClassObject *obj);
static bool __saveRGB(
    const char *filename,
    JPEGImageClassObject *obj,
    int quality);
static bool __saveDCT(
    const char *filename,
    JPEGImageClassObject *obj);
static void __getDCT(
    struct jpeg_decompress_struct *cinfo,
    JPEGImageClassObject *obj);
static void __getRGB(
    struct jpeg_decompress_struct *cinfo,
    JPEGImageClassObject *obj);

// Members of JPEGImage
static struct PyMemberDef JPEGImageMembers[] = {
    // {"name of member", "type of member", "offset of C structure", "READONLY flag", "doc string"}
    {"filename",        T_OBJECT, 
     offsetof(JPEGImageClassObject, filename),           0,
     "filename of opened file"},
    {"isDCT",           T_BOOL, 
     offsetof(JPEGImageClassObject, isDCT),              0, 
     "DCT/RGB mode"},
    {"size",            T_OBJECT, 
     offsetof(JPEGImageClassObject, size),               0, 
     "size => (width, height)"},
    {"_color_space",    T_BOOL, 
     offsetof(JPEGImageClassObject, color_space),        0, 
     "color_space"},
    {"isProgressive",   T_BOOL, 
     offsetof(JPEGImageClassObject, progressive_mode),   0, 
     "progressive mode"},
    {"data",            T_OBJECT, 
     offsetof(JPEGImageClassObject, data),               0, 
     "data of image"},
    {"comp_infos",      T_OBJECT, 
     offsetof(JPEGImageClassObject, comp_infos),         0, 
     "comp_infos"},
    {"quant_tbls",      T_OBJECT, 
     offsetof(JPEGImageClassObject, quant_tbls),         0, 
     "quant_tbls"},
    {"ac_huff_tables",  T_OBJECT, 
     offsetof(JPEGImageClassObject, ac_huff_tables),     0, 
     "ac_huff_tables"},
    {"dc_huff_tables",  T_OBJECT, 
     offsetof(JPEGImageClassObject, dc_huff_tables),     0, 
     "dc_huff_tables"},
    {"isOptimize",      T_BOOL, 
     offsetof(JPEGImageClassObject, optimize_coding),    0, 
     "optimize coding"},

    {NULL, 0, 0, 0, NULL},
};

/* Methods of JPEGImage */

// static bool JPEGImage_init(JPEGImageClassObject *self, PyObject *args){
//     self->filename = NULL;
//     self->isDCT = TRUE;

//     // Default
//     self->optimize_coding = FALSE;
//     printf("JPEGImage_init\n");
//     return TRUE;
// }
static void JPEGImage_del(JPEGImageClassObject *self){
    printf("JPEGImage_del\n");
    if (self->_filename){
        PyMem_Free(self->_filename);
        self->_filename = NULL;
    }
}
static PyObject* JPEGImage_save(JPEGImageClassObject *self, PyObject *args){
    char *outfile;
    int quality = 75;// 默认参数值
    if (! PyArg_ParseTuple(args, "s|i", &outfile, &quality)){
        Py_INCREF(Py_False);
        return Py_False;
    }

    bool succeed;
    if (self->isDCT){
        succeed = __saveDCT(outfile, self);
    }else{
        succeed = __saveRGB(outfile, self, quality);
    }
    if (succeed){
        Py_INCREF(Py_True);
        return Py_True;
    }else{
        Py_INCREF(Py_False);
        return Py_False;
    }
}
// register method in Python
static PyMethodDef JPEGImageMethods[] = {
    {"save", (PyCFunction)JPEGImage_save, METH_VARARGS, 
     "save as JPEG image."},
    {NULL, NULL, 0, NULL}
};

/* define JPEGImage Type in Python */
static PyTypeObject JPEGImageType = {
    PyObject_HEAD_INIT(NULL)
    0,
    "pyjpegtbx.JPEGImage",              // tp_name
    sizeof(JPEGImageClassObject),       // tp_basicsize
    0,                                  // tp_itemsize

    0,                                  // tp_dealloc
    0,                                  // tp_print
    0,                                  // tp_getattr
    0,                                  // tp_setattr
    0,                                  // tp_compare
    0,                                  // tp_repr

    0,                                  // tp_as_number
    0,                                  // tp_as_sequence
    0,                                  // tp_as_mapping

    0,                                  // tp_hash
    0,                                  // tp_call
    0,                                  // tp_str
    0,                                  // tp_getattro
    0,                                  // tp_setattro

    0,                                  // tp_as_buffer
    Py_TPFLAGS_DEFAULT,                 // tp_flags
    "JPEGImage",                        // tp_doc

    0,                                  // tp_traverse
    0,                                  // tp_clear
    0,                                  // tp_richcompare
    0,                                  // tp_weaklistoffset
    0,                                  // tp_iter
    0,                                  // tp_iternext

    JPEGImageMethods,                   // tp_methods
    JPEGImageMembers,                   // tp_members
    0,                                  // tp_getset
    0,                                  // tp_base
    0,                                  // tp_dict
    0,                                  // tp_descr_get
    0,                                  // tp_descr_set
    0,                                  // tp_dictoffset
    0,                                  // tp_init
    0,                                  // tp_alloc
    0,                                  // tp_new
    0,                                  // tp_free
    0,                                  // tp_is_gc
    0,                                  // tp_bases
    0,                                  // tp_mro
    0,                                  // tp_cache
    0,                                  // tp_subclasses
    0,                                  // tp_weaklist
    (destructor)JPEGImage_del,          // tp_del

    0,                                  // tp_version_tag
};

static PyObject* JPEGImage_new(PyObject *self, PyObject *args){
    JPEGImageClassObject *obj = 
        PyObject_New(JPEGImageClassObject, &JPEGImageType);
    if (obj == NULL)    return NULL;

    // init member of obj
    obj->_filename = NULL;
    obj->filename = NULL;
    obj->isDCT = FALSE;
    obj->size = NULL;
    obj->color_space = 0;
    obj->progressive_mode = FALSE;
    obj->data = NULL;
    obj->comp_infos = NULL;
    obj->quant_tbls = NULL;
    obj->ac_huff_tables = obj->dc_huff_tables = NULL;
    obj->optimize_coding = FALSE;
    
    if (! PyArg_ParseTuple(args, "si", &obj->_filename, &obj->isDCT)){
        return NULL;
    }
    obj->filename = Py_BuildValue("s", obj->_filename);
    
    // parse JPEG file.
    bool succeed = __parse(obj);

    if (succeed){
        return (PyObject*) obj;
    }else{
        Py_INCREF(Py_None);
        return Py_None;
    }
}


static PyMethodDef moduleMethods[] = {
    {"JPEGImage", (PyCFunction)JPEGImage_new, METH_VARARGS,
     "JPEGImage(filename, isDCT)\n"
     "Return a JPEGImage object."},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC 
initpyjpegtbx(void) {
    PyObject *module;
    if (PyType_Ready(&JPEGImageType) < 0) {
        return ;
    }
    module = Py_InitModule3(
        "pyjpegtbx", 
        moduleMethods,
        "A toolbox for image in JPEG format"
    );
}

// C functions
static bool __parse(JPEGImageClassObject *obj)
{
    FILE *infile = NULL;
    if (NULL == (infile=fopen(obj->_filename, "rb"))) {
        // open file failed. Raise exception
        PyErr_SetString(PyExc_IOError, "No such file or dierctory.");
        return FALSE;
    }

    struct jpeg_decompress_struct cinfo;
    struct error_mgr_t jerr;
    cinfo.err = jpeg_std_error(&jerr.pub);
    jerr.pub.error_exit = my_error_exit;
    if (setjmp(jerr.setjmp_buffer)) {
        // 设置jpeg异常处理
        jpeg_destroy_decompress(&cinfo);
        fclose(infile);

        // raise exception
        PyErr_SetString(PyExc_Exception, "Error happened in parsing JPEG file.");
        return FALSE;
    }
    jpeg_create_decompress(&cinfo);
    jpeg_stdio_src(&cinfo, infile);
    (void) jpeg_read_header(&cinfo, TRUE);

    // size:(width, height)
    obj->size = Py_BuildValue("(ii)", cinfo.image_width, cinfo.image_height);
    // color_space
    obj->color_space = cinfo.jpeg_color_space;
    // progressive_mode
    obj->progressive_mode = cinfo.progressive_mode;

    // ComponentsInfo
    obj->comp_infos = PyList_New(cinfo.num_components);
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

        PyList_SetItem(obj->comp_infos, i, comp);
    }

    // Quantization Tables
    obj->quant_tbls = PyList_New(0);
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
        PyList_Append(obj->quant_tbls, quant_tbl);
    }

    // Huffman Tables
    obj->dc_huff_tables = PyList_New(0);
    obj->ac_huff_tables = PyList_New(0);
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

            PyList_Append(obj->dc_huff_tables, huff_table);
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

            PyList_Append(obj->ac_huff_tables, huff_table);
        }
    }
    
    // DCT / RGB data
    if ( ! obj->isDCT ) {
        __getRGB(&cinfo, obj);
    }else {
        __getDCT(&cinfo, obj);
    }

    // release resources
    (void) jpeg_finish_decompress(&cinfo);
    jpeg_destroy_decompress(&cinfo);
    fclose(infile);

    return TRUE;
}
static bool __saveRGB(
    const char *filename,
    JPEGImageClassObject *obj,
    int quality)
{
    char err_msg[1024];
    memset(err_msg, 0, sizeof(err_msg));

    FILE *outfile = NULL;
    if (NULL == (outfile=fopen(filename, "wb"))){
        PyErr_SetString(PyExc_IOError, "No such file or dierctory.");
        return FALSE;
    }

    struct jpeg_compress_struct cinfo;
    struct error_mgr_t jerr;
    cinfo.err = jpeg_std_error(&jerr.pub);
    jerr.pub.error_exit = my_error_exit;
    if (setjmp(jerr.setjmp_buffer)) {
        // handle libjpeg error
        (jerr.pub.format_message)((j_common_ptr)&cinfo, err_msg);

        jpeg_destroy_compress(&cinfo);
        fclose(outfile);

        PyErr_SetString(PyExc_Exception, "Error happened in parsing JPEG file.");
        return FALSE;
    }
    jpeg_create_compress(&cinfo);
    jpeg_stdio_dest(&cinfo, outfile);

    // set fields of cinfo 
    PyArg_ParseTuple(obj->size, "ii", 
        &cinfo.image_width, &cinfo.image_height);
    cinfo.input_components = 3;
    cinfo.in_color_space = JCS_RGB;

    jpeg_set_defaults(&cinfo);
    jpeg_set_quality(&cinfo, quality, TRUE);

    jpeg_start_compress(&cinfo, TRUE);

    int row_stride = cinfo.image_width * 3;
    unsigned char row_buf[row_stride];
    JSAMPROW row_ptr[1];row_ptr[0] = row_buf;
    PyObject *rgb=NULL;
    int r,g,b,ind=0;
    while (cinfo.next_scanline < cinfo.image_height) {
        for (int i=0; i<row_stride; /* void */){
            rgb = PyList_GetItem(obj->data, ind++);
            PyArg_ParseTuple(rgb, "iii", &r, &g, &b);
            row_buf[i++] = (unsigned char)(r & 0xff);
            row_buf[i++] = (unsigned char)(g & 0xff);
            row_buf[i++] = (unsigned char)(b & 0xff);
        }
        (void) jpeg_write_scanlines(&cinfo, row_ptr, 1);
    }

    jpeg_finish_compress(&cinfo);
    fclose(outfile);
    jpeg_destroy_compress(&cinfo);

    return TRUE;
}
static bool __saveDCT(
    const char *filename,
    JPEGImageClassObject *obj)
{
    char err_msg[1024];
    memset(err_msg, 0, sizeof(err_msg));

    FILE *outfile;
    if (NULL == (outfile=fopen(filename, "wb"))){
        printf("File '%s' Open Failed!\n", filename);
        return FALSE;
    }
    struct jpeg_compress_struct cinfo;
    struct error_mgr_t jerr;

    cinfo.err = jpeg_std_error(&jerr.pub);
    jerr.pub.error_exit = my_error_exit;
    if (setjmp(jerr.setjmp_buffer)) {
        // handle libjpeg error
        (jerr.pub.format_message)((j_common_ptr)&cinfo, err_msg);
        // printf("libjpeg(Library errors): '%s'\n", err_msg);
        // printf("Global state: %d\n", cinfo.global_state);

        jpeg_destroy_compress(&cinfo);
        fclose(outfile);

        PyErr_SetString(PyExc_Exception, "Error happened in parsing JPEG file.");
        return FALSE;
    }

    jpeg_create_compress(&cinfo);
    jpeg_stdio_dest(&cinfo, outfile);

    // set fields of cinfo 
    PyArg_ParseTuple(obj->size, "ii", &cinfo.image_width, &cinfo.image_height);
    cinfo.jpeg_color_space = obj->color_space;
    cinfo.input_components = PyList_Size(obj->comp_infos);
    // printf("cinfo.input_components: %d\n", cinfo.input_components);
    cinfo.optimize_coding = obj->optimize_coding;

    jpeg_set_defaults(&cinfo);

    // these should be cacl from above params....
    cinfo.in_color_space = 3;
    cinfo.num_components = cinfo.input_components;
    cinfo.jpeg_width = cinfo.image_width;
    cinfo.jpeg_height = cinfo.image_height;

    if ( obj->progressive_mode == 1){
        jpeg_simple_progression(&cinfo);
    }

    jpeg_component_info *compptr;
    int min_h=16, min_v=16;
    for (int ci=0; ci!=cinfo.num_components; ++ci){
        PyObject *component = PyList_GetItem(obj->comp_infos, ci);

        compptr = cinfo.comp_info+ci;
        compptr->component_index = ci;
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

    // set params to alloc coef arrays
    jvirt_barray_ptr *coef_arrays = (jvirt_barray_ptr *)
        (cinfo.mem->alloc_small)(
            (j_common_ptr)&cinfo, JPOOL_IMAGE,
            sizeof(jvirt_barray_ptr)*cinfo.num_components
        );

    for (int ci=0; ci!=cinfo.num_components; ++ci){
        compptr = cinfo.comp_info + ci;
        coef_arrays[ci] = (cinfo.mem->request_virt_barray)
            ((j_common_ptr)&cinfo, JPOOL_IMAGE, TRUE,
             (JDIMENSION) jround_up((long) compptr->width_in_blocks, (long)compptr->h_samp_factor),
             (JDIMENSION) jround_up((long) compptr->height_in_blocks, (long)compptr->v_samp_factor),
             (JDIMENSION) compptr->v_samp_factor
            );
    }

    // realize virtual block arrays
    jpeg_write_coefficients(&cinfo, coef_arrays);

    // populate the array with the DCT coefficients
    for (int ci=0; ci!=cinfo.num_components; ++ci){
        PyObject *component, *coef;

        component = PyDict_GetItem(obj->data, Py_BuildValue("i", ci));
        compptr = cinfo.comp_info + ci;
        int buffer_i=0;
        jvirt_barray_ptr tmp_arrays = coef_arrays[ci];
        JBLOCKARRAY buffer;
        for(int row=0, act_row=0;
            row!=compptr->height_in_blocks; ++row){
            if (row >= (coef_arrays[ci]->rows_in_mem)*(buffer_i+1)){
                fprintf(stderr, "rows_in_array, rows_in_mem: %d, %d"
                    "next array?[%p]\n", 
                    tmp_arrays->rows_in_array, tmp_arrays->rows_in_mem,
                    tmp_arrays->next);
                tmp_arrays = tmp_arrays->next;
                ++buffer_i;
            }
            act_row = row - (buffer_i * (coef_arrays[ci]->rows_in_mem));
            buffer = (cinfo.mem->access_virt_barray)
                ((j_common_ptr)&cinfo, tmp_arrays, act_row, 1, TRUE);

            for (int col=0; col!=compptr->width_in_blocks; ++col){
                coef = PyList_GetItem(component, 
                        row*(compptr->width_in_blocks)+col);
                for (int j=0; j!=DCTSIZE2; ++j){
                    buffer[0][col][j] = PyLong_AsLong(
                       PyList_GetItem(coef, j));
                }
            }
        }
    }

    // get the quantization tables
    Py_ssize_t sz_qtbls = PyList_Size(obj->quant_tbls);
    for (Py_ssize_t i=0; i!=NUM_QUANT_TBLS; ++i){
        if (i < sz_qtbls){
            PyObject *quant_tbl = PyList_GetItem(obj->quant_tbls, i);
            if (NULL == cinfo.quant_tbl_ptrs[i]){
                cinfo.quant_tbl_ptrs[i] = 
                    jpeg_alloc_quant_table((j_common_ptr)&cinfo);
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

        // ac
        sz_hufftbls = PyList_Size(obj->ac_huff_tables);
        for (Py_ssize_t i=0; i!=NUM_HUFF_TBLS; ++i){
            if (i < sz_hufftbls){
                huff_tbl = PyList_GetItem(obj->ac_huff_tables, i);
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

        // dc
        sz_hufftbls = PyList_Size(obj->dc_huff_tables);
        for (Py_ssize_t i=0; i!=NUM_HUFF_TBLS; ++i){
            if (i < sz_hufftbls){
                huff_tbl = PyList_GetItem(obj->dc_huff_tables, i);
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
    return TRUE;
}

static void __getDCT(
    struct jpeg_decompress_struct *cinfo,
    JPEGImageClassObject *obj)
{
    obj->data = PyDict_New();
    PyObject *component, *coef;
    jvirt_barray_ptr *coef_arrays = jpeg_read_coefficients(cinfo);
    jpeg_component_info *compptr;
    for (int ci=0; ci!=cinfo->num_components; ++ci) {
        // Create a new list to save ALL DCT blocks in one component
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
        // add component to object->data
        PyDict_SetItem(obj->data, Py_BuildValue("i", ci), component);
    }
}
static void __getRGB(
    struct jpeg_decompress_struct *cinfo,
    JPEGImageClassObject *obj)
{
    (void) jpeg_start_decompress(cinfo);
    obj->data = PyList_New(0);
    int row_stride;     /* physical row width in output buffer */
    JSAMPARRAY buffer;  /* Output row buffer */
    row_stride = cinfo->output_width * cinfo->output_components;
    buffer = (cinfo->mem->alloc_sarray)
        ((j_common_ptr) cinfo, JPOOL_IMAGE, row_stride, 1);

    while (cinfo->output_scanline < cinfo->output_height) {
        (void) jpeg_read_scanlines(cinfo, buffer, 1);
        for (int cols=0; cols < row_stride; cols+=3){
            PyList_Append(obj->data, 
                Py_BuildValue("(iii)", 
                    (*buffer)[cols], (*buffer)[cols+1], (*buffer)[cols+2])
            );
        }
    }
}
