#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

#include <Python/Python.h>

typedef struct {
    PyObject_HEAD
    char *filename;         //
    bool isDCT;             // bool True读取DCT数据, False读取RGB数据
    PyObject *size;         // tuple (width, height)
    int color_space;       // int color space
    bool progressive_mode;  // bool progressive mode
    PyObject *data;         // ? DCT/RGB图像数据
    PyObject *comp_infos;   // tuple 
    PyObject *quant_tbls;   // tuple
    PyObject *ac_huff_tables;// tuple
    PyObject *dc_huff_tables;// tuple
    bool optimize_coding;   // bool 默认为False
} JPEGImageClassObject;


// Members of JPEGImage
static struct PyMemberDef JPEGImageMembers[] = {
    // {"name of member", "type of member", "offset of C structure", "READONLY flag", "doc string"}
    {"filename",        T_STRING, 
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
static int JPEGImage_init(JPEGImageClassObject *self, PyObject *args, PyObject *kw){
    char *filename;
    printf("JPEGImage_init\n");
}
static void JPEGImage_del(JPEGImageClassObject *self){
    printf("JPEGImage_del\n");
    if (self != NULL){
        PyObject_Del(self);
    }
}
static PyObject* JPEGImage_setData(JPEGImageClassObject *self, PyObject *args){
    printf("JPEGImage_setData\n");
    Py_INCREF(Py_True);
    return Py_True;
}
// registe 
static PyMethodDef JPEGImageMethods[] = {
    {"setData", (PyCFunction)JPEGImage_setData, METH_VARARGS, 
     "set the DCT/RGB image data."},
    // {"close", (PyCFunction)Encoder_close, METH_NOARGS, "close the output file."},
    {NULL, NULL, 0, NULL}
};

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
    (initproc)JPEGImage_init,           // tp_init
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

PyMODINIT_FUNC initclame() {
    PyObject* module;
    if (PyType_Ready(&JPEGImageType) < 0) {
        return NULL;
    }
    
    module = Py_InitModule3("pyjpegtbx", clame_methods, "toolbox for image in JPEG format");
    Py_INCREF(&JPEGImageType);
    PyModule_AddObject(module, "JPEGImage", (PyObject*)& JPEGImageType);
}
