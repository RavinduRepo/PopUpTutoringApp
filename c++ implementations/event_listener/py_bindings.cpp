#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "key_processor.h"

namespace py = pybind11;

PYBIND11_MODULE(key_processor_cpp, m) {
    m.doc() = "Python wrapper for KeyProcessor C++ class";

    py::class_<Key>(m, "Key")
        .def(py::init<const std::string&, char>(), py::arg("name") = "", py::arg("character") = '\0')
        .def_readwrite("name", &Key::name)
        .def_readwrite("character", &Key::character);

    py::class_<KeyProcessor>(m, "KeyProcessor")
        .def(py::init<>())
        .def("add_pressed_key", &KeyProcessor::add_pressed_key)
        .def("remove_released_key", &KeyProcessor::remove_released_key)
        .def("get_key_string", &KeyProcessor::get_key_string)
        .def("format_hotkey_combination", &KeyProcessor::format_hotkey_combination)
        .def("is_hotkey_combination", &KeyProcessor::is_hotkey_combination)
        .def("should_send_hotkey", &KeyProcessor::should_send_hotkey)
        .def("add_typed_character", &KeyProcessor::add_typed_character)
        .def("flush_typing", &KeyProcessor::flush_typing)
        .def("reset_state", &KeyProcessor::reset_state)
        .def("get_pressed_keys", &KeyProcessor::get_pressed_keys)
        .def("get_sent_hotkeys", &KeyProcessor::get_sent_hotkeys)
        .def("get_last_hotkey_time", &KeyProcessor::get_last_hotkey_time)
        .def("get_last_key_time", &KeyProcessor::get_last_key_time)
        .def("get_is_typing_mode", &KeyProcessor::get_is_typing_mode)
        .def("get_typing_timeout", &KeyProcessor::get_typing_timeout);
}