// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

/*
 * Wraps the PDQ hashing algorithm so that it can be accessed from Python.
 * See `pdq_test.py` for example usage from Python.
 */

#include "common/encode/Base64.h"
#include "common/logging/logging.h"
#include "pdq/common/pdqhashtypes.h"
#include "pdq/io/pdqio.h"

#include <Python.h>
#include <folly/CppAttributes.h>
#include <folly/Format.h>
#include <istream>

namespace facebook {
namespace pdq {
namespace python {

PyObject* FOLLY_NULLABLE to_py_list(hashing::Hash256& hash) {
  PyObject* hash_obj = PyList_New(hash.getNumWords());
  for (auto i = 0; i < hash.getNumWords(); i++) {
#if PY_MAJOR_VERSION >= 3
    PyList_SetItem(hash_obj, i, PyLong_FromLong(hash.w[i]));
#else
    PyList_SetItem(hash_obj, i, PyInt_FromLong(hash.w[i]));
#endif // PY_MAJOR_VERSION >= 3
  }
  return hash_obj;
}

bool from_py_list(PyObject* l, hashing::Hash256& hash) {
  if (!PyList_Check(l)) {
    PyErr_SetString(PyExc_ValueError, "invalid argument; expected a list");
    return false;
  }
  if (PyList_Size(l) != hash.getNumWords()) {
    auto fmt_string = folly::format(
        "got invalid length {}; hashes must be {} integers",
        PyList_Size(l),
        hash.getNumWords());
    PyErr_SetString(PyExc_ValueError, fmt_string.str().c_str());
    return false;
  }

  for (auto i = 0; i < hash.getNumWords(); i++) {
#if PY_MAJOR_VERSION >= 3
    hash.w[i] = PyLong_AsLong(PyList_GetItem(l, i));
#else
    hash.w[i] = PyInt_AsLong(PyList_GetItem(l, i));
#endif // PY_MAJOR_VERSION >= 3
  }
  PyObject* exception = PyErr_Occurred();
  if (exception != nullptr) {
    auto fmt_string = folly::format(
        "error parsing pdq hash: {}",
        PyUnicode_AsUnicode(PyObject_Repr(exception)));
    PyErr_SetString(PyExc_ValueError, fmt_string.str().c_str());
    return false;
  }
  return true;
}

PyObject* FOLLY_NULLABLE py_get_hash(PyObject* /* unused */, PyObject* args) {
  const char* file_path;
  hashing::Hash256 hash;
  int quality;
  if (!PyArg_ParseTuple(args, "s", &file_path)) {
    auto fmt_string = folly::format(
        "invalid arguments; expected a file path, got {}",
        PyUnicode_AsUnicode(PyObject_Repr(args)));
    PyErr_SetString(PyExc_ValueError, fmt_string.str().c_str());
    return nullptr;
  }

  // Gets the file pointer.
  FILE* fp;
  fp = fopen(file_path, "rb");
  if (!fp) {
    PyErr_SetString(
#if PY_MAJOR_VERSION >= 3
        PyExc_FileNotFoundError,
#else
        PyExc_IOError,
#endif
        folly::format("file not found: {}", file_path).str().c_str());
    return nullptr;
  }

  // Gets the PDQ hash and quality.
  try {
    pdqHash256FromFile(file_path, fp, hash, quality);
  } catch (const std::exception& e) {
    PyErr_SetString(
        PyExc_RuntimeError,
        folly::format("error getting hash: {}", e.what()).str().c_str());
    fclose(fp);
    return nullptr;
  }
  fclose(fp);

  PyObject* result = PyTuple_New(2);
  PyTuple_SetItem(result, 0, to_py_list(hash));
#if PY_MAJOR_VERSION >= 3
  PyTuple_SetItem(result, 1, PyLong_FromLong(quality));
#else
  PyTuple_SetItem(result, 1, PyInt_FromLong(quality));
#endif // PY_MAJOR_VERSION >= 3

  return result;
}

PyObject* FOLLY_NULLABLE
py_get_all_hashes(PyObject* /* unused */, PyObject* args) {
  const char* file_path;
  hashing::Hash256 hash, hash_rotate_90, hash_rotate_180, hash_rotate_270,
      hash_left_right, hash_top_bottom, hash_transpose, hash_transverse;
  int quality;
  if (!PyArg_ParseTuple(args, "s", &file_path)) {
    auto fmt_string = folly::format(
        "invalid arguments; expected a file path, got {}",
        PyUnicode_AsUnicode(PyObject_Repr(args)));
    PyErr_SetString(PyExc_ValueError, fmt_string.str().c_str());
    return nullptr;
  }

  // Gets the file pointer.
  FILE* fp;
  fp = fopen(file_path, "rb");
  if (!fp) {
    PyErr_SetString(
#if PY_MAJOR_VERSION >= 3
        PyExc_FileNotFoundError,
#else
        PyExc_IOError,
#endif
        folly::format("file not found: {}", file_path).str().c_str());
    return nullptr;
  }

  // Gets the PDQ hash and quality.
  try {
    pdqDihedralHash256esFromFile(
        file_path,
        fp,
        &hash,
        &hash_rotate_90,
        &hash_rotate_180,
        &hash_rotate_270,
        &hash_left_right,
        &hash_top_bottom,
        &hash_transpose,
        &hash_transverse,
        quality);
  } catch (const std::exception& e) {
    PyErr_SetString(
        PyExc_RuntimeError,
        folly::format("error getting hash: {}", e.what()).str().c_str());
    fclose(fp);
    return nullptr;
  }
  fclose(fp);

  PyObject* result = PyTuple_New(9);
  PyTuple_SetItem(result, 0, to_py_list(hash));
  PyTuple_SetItem(result, 1, to_py_list(hash_rotate_90));
  PyTuple_SetItem(result, 2, to_py_list(hash_rotate_180));
  PyTuple_SetItem(result, 3, to_py_list(hash_rotate_270));
  PyTuple_SetItem(result, 4, to_py_list(hash_left_right));
  PyTuple_SetItem(result, 5, to_py_list(hash_top_bottom));
  PyTuple_SetItem(result, 6, to_py_list(hash_transpose));
  PyTuple_SetItem(result, 7, to_py_list(hash_transverse));
#if PY_MAJOR_VERSION >= 3
  PyTuple_SetItem(result, 8, PyLong_FromLong(quality));
#else
  PyTuple_SetItem(result, 8, PyInt_FromLong(quality));
#endif // PY_MAJOR_VERSION >= 3

  return result;
}

PyObject* FOLLY_NULLABLE py_distance(PyObject* /* unused */, PyObject* args) {
  PyObject *a_list, *b_list;
  if (!PyArg_ParseTuple(args, "OO", &a_list, &b_list)) {
    auto fmt_string = folly::format(
        "invalid arguments; expected two lists, got {}",
        PyUnicode_AsUnicode(PyObject_Repr(args)));
    PyErr_SetString(PyExc_ValueError, fmt_string.str().c_str());
    return nullptr;
  }
  hashing::Hash256 a, b;
  if (!from_py_list(a_list, a) || !from_py_list(b_list, b)) {
    return nullptr;
  }
  int result = a.hammingDistance(b);
#if PY_MAJOR_VERSION >= 3
  return PyLong_FromLong(result);
#else
  return PyInt_FromLong(result);
#endif // PY_MAJOR_VERSION >= 3
}

PyObject* FOLLY_NULLABLE py_norm(PyObject* /* unused */, PyObject* args) {
  PyObject* a_list;
  if (!PyArg_ParseTuple(args, "O", &a_list)) {
    auto fmt_string = folly::format(
        "invalid arguments; expected a list, got {}",
        PyUnicode_AsUnicode(PyObject_Repr(args)));
    PyErr_SetString(PyExc_ValueError, fmt_string.str().c_str());
    return nullptr;
  }
  hashing::Hash256 a;
  if (!from_py_list(a_list, a)) {
    return nullptr;
  }
  int result = a.hammingNorm();
#if PY_MAJOR_VERSION >= 3
  return PyLong_FromLong(result);
#else
  return PyInt_FromLong(result);
#endif // PY_MAJOR_VERSION >= 3
}

static PyMethodDef _PDQMethods[] = {
    {"get_hash", py_get_hash, METH_VARARGS, "Gets PDQ hash from a given file"},
    {"get_all_hashes",
     py_get_all_hashes,
     METH_VARARGS,
     "Gets all PDQ hashes from a given file"},
    {"distance", py_distance, METH_VARARGS, "Gets hashes Hamming distance"},
    {"norm", py_norm, METH_VARARGS, "Gets hash Hamming norm"},
    {nullptr, nullptr, 0, nullptr}};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef _PDQDef = {
    PyModuleDef_HEAD_INIT,
    "pdq",
    "PDQ hashing function callers",
    -1,
    _PDQMethods,
};
#endif // PY_MAJOR_VERSION >= 3

#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC PyInit_pdq() {
  return PyModule_Create(&_PDQDef);
}
#else
PyMODINIT_FUNC initpdq() {
  Py_InitModule("pdq", _PDQMethods);
}
#endif // PY_MAJOR_VERSION >= 3

} // namespace python
} // namespace pdq
} // namespace facebook
