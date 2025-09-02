#include "key_processor.h"
#include <iostream>
#include <algorithm>
#include <chrono>

KeyProcessor::KeyProcessor() {
    modifier_keys = {
        "ctrl_l", "ctrl_r", "alt_l", "alt_r", "shift_l", "shift_r",
        "cmd_l", "cmd_r", "tab", "esc", "f1", "f2", "f3", "f4", "f5",
        "f6", "f7", "f8", "f9", "f10", "f11", "f12"
    };
    control_keys = {
        "enter", "backspace", "delete", "home", "end", "page_up",
        "page_down", "up", "down", "left", "right", "insert"
    };
    ctrl_map = {
        {'\x01', 'a'}, {'\x02', 'b'}, {'\x03', 'c'}, {'\x04', 'd'},
        {'\x05', 'e'}, {'\x06', 'f'}, {'\x07', 'g'}, {'\x08', 'h'},
        {'\x09', 'i'}, {'\x0a', 'j'}, {'\x0b', 'k'}, {'\x0c', 'l'},
        {'\x0d', 'm'}, {'\x0e', 'n'}, {'\x0f', 'o'}, {'\x10', 'p'},
        {'\x11', 'q'}, {'\x12', 'r'}, {'\x13', 's'}, {'\x14', 't'},
        {'\x15', 'u'}, {'\x16', 'v'}, {'\x17', 'w'}, {'\x18', 'x'},
        {'\x19', 'y'}, {'\x1a', 'z'}
    };
}

KeyProcessor::~KeyProcessor() {
    // Destructor
}

// Public getters to access private members from Python
std::unordered_set<std::string> KeyProcessor::get_pressed_keys() const { return pressed_keys; }
std::unordered_set<std::string> KeyProcessor::get_sent_hotkeys() const { return sent_hotkeys; }
double KeyProcessor::get_last_hotkey_time() const { return last_hotkey_time; }
double KeyProcessor::get_last_key_time() const { return last_key_time; }
bool KeyProcessor::get_is_typing_mode() const { return is_typing_mode; }
double KeyProcessor::get_typing_timeout() const { return typing_timeout; }

void KeyProcessor::add_pressed_key(const Key& key) {
    if (pressed_keys.find(key.name) == pressed_keys.end()) {
        pressed_keys.insert(key.name);
        key_press_times[key.name] = static_cast<double>(std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count()) / 1000000.0;
        last_key_time = key_press_times[key.name];
    }
}

void KeyProcessor::remove_released_key(const Key& key) {
    pressed_keys.erase(key.name);
    key_press_times.erase(key.name);
}

std::string KeyProcessor::get_key_string(const Key& key) {
    std::string key_name = key.name;
    if (key_name == "ctrl_l" || key_name == "ctrl_r") return "ctrl";
    if (key_name == "alt_l" || key_name == "alt_r") return "alt";
    if (key_name == "shift_l" || key_name == "shift_r") return "shift";
    if (key_name == "cmd_l" || key_name == "cmd_r") return "cmd";
    return key_name;
}

std::string KeyProcessor::format_hotkey_combination() {
    std::vector<std::string> modifiers;
    std::vector<std::string> regular_keys;

    for (const auto& key_str : pressed_keys) {
        if (modifier_keys.count(key_str)) {
            modifiers.push_back(get_key_string({key_str}));
        } else {
            regular_keys.push_back(key_str);
        }
    }
    
    std::unordered_set<std::string> unique_modifiers_set;
    std::vector<std::string> unique_modifiers_vec;
    std::vector<std::string> modifier_order = {"ctrl", "alt", "shift", "cmd"};

    for(const auto& mod : modifier_order) {
        if (std::find(modifiers.begin(), modifiers.end(), mod) != modifiers.end() && unique_modifiers_set.find(mod) == unique_modifiers_set.end()) {
            unique_modifiers_vec.push_back(mod);
            unique_modifiers_set.insert(mod);
        }
    }
    for (const auto& mod : modifiers) {
        if (unique_modifiers_set.find(mod) == unique_modifiers_set.end()) {
            unique_modifiers_vec.push_back(mod);
        }
    }

    std::sort(regular_keys.begin(), regular_keys.end());
    unique_modifiers_vec.insert(unique_modifiers_vec.end(), regular_keys.begin(), regular_keys.end());

    std::string result = "";
    for (size_t i = 0; i < unique_modifiers_vec.size(); ++i) {
        result += unique_modifiers_vec[i];
        if (i < unique_modifiers_vec.size() - 1) {
            result += "+";
        }
    }
    return result;
}

bool KeyProcessor::is_hotkey_combination() {
    if (pressed_keys.empty()) {
        return false;
    }
    if (pressed_keys.size() == 1) {
        const auto& key_str = *pressed_keys.begin();
        if (key_str == "enter") return true;
        if (key_str == "backspace") return false;
        if (modifier_keys.count(key_str)) return false;
        if (control_keys.count(key_str)) return true;
    }
    bool has_modifier = false;
    bool has_non_modifier = false;
    for (const auto& key_str : pressed_keys) {
        if (modifier_keys.count(key_str)) has_modifier = true;
        else has_non_modifier = true;
    }
    if (has_modifier && has_non_modifier && pressed_keys.size() > 1) return true;
    if (pressed_keys.size() > 1 && !has_modifier) return true;
    return false;
}

bool KeyProcessor::should_send_hotkey(const Key& pressed_key) {
    std::string key_str = get_key_string_internal(pressed_key);
    if (key_str == "enter") return true;
    
    if (pressed_keys.size() == 1 && modifier_keys.count(key_str)) return false;
    if (pressed_keys.size() == 1 && !modifier_keys.count(key_str)) return true;

    bool has_modifier = false;
    bool has_non_modifier = false;
    for (const auto& k : pressed_keys) {
        if (modifier_keys.count(k)) has_modifier = true;
        else has_non_modifier = true;
    }
    if (has_modifier && has_non_modifier) {
        if (!modifier_keys.count(key_str)) return true;
        else return true;
    }
    return false;
}

void KeyProcessor::add_typed_character(const Key& key) {
    if (key.name == "backspace") {
        if (!typed_characters.empty()) typed_characters.pop_back();
    } else if (key.name == "space") {
        typed_characters += ' ';
    } else {
        if (key.character != '\0' && key.character >= 32) typed_characters += key.character;
    }
}

std::string KeyProcessor::flush_typing() {
    std::string text = typed_characters;
    typed_characters.clear();
    return text;
}

void KeyProcessor::reset_state() {
    pressed_keys.clear();
    sent_hotkeys.clear();
    key_press_times.clear();
    typed_characters = "";
    is_typing_mode = false;
}

std::string KeyProcessor::get_key_string_internal(const Key& key) {
    if (key.character != '\0') {
        if (key.character >= 32) return std::string(1, key.character);
        else {
            auto it = ctrl_map.find(key.character);
            if (it != ctrl_map.end()) return std::string(1, it->second);
            return std::string(1, key.character);
        }
    } else {
        std::string key_name = key.name;
        if (key_name == "ctrl_l" || key_name == "ctrl_r") return "ctrl";
        if (key_name == "alt_l" || key_name == "alt_r") return "alt";
        if (key_name == "shift_l" || key_name == "shift_r") return "shift";
        if (key_name == "cmd_l" || key_name == "cmd_r") return "cmd";
        return key_name;
    }
}