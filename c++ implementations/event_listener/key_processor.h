#ifndef KEY_PROCESSOR_H
#define KEY_PROCESSOR_H

#include <string>
#include <unordered_set>
#include <unordered_map>
#include <vector>
#include <set>

// A simple struct to represent a key
struct Key {
    std::string name;
    char character = '\0';
};

class KeyProcessor {
private:
    std::unordered_set<std::string> pressed_keys;
    double last_hotkey_time = 0;
    double hotkey_timeout = 0.1;
    double typing_timeout = 0.5;
    double last_key_time = 0;
    bool is_typing_mode = false;
    std::unordered_set<std::string> sent_hotkeys;
    std::unordered_map<std::string, double> key_press_times;
    std::string typed_characters;

    std::unordered_set<std::string> modifier_keys;
    std::unordered_set<std::string> control_keys;
    std::unordered_map<char, char> ctrl_map;

    std::string get_key_string_internal(const Key& key);
    
public:
    KeyProcessor();
    ~KeyProcessor();

    void add_pressed_key(const Key& key);
    void remove_released_key(const Key& key);
    
    // Public methods equivalent to the Python class
    std::string get_key_string(const Key& key);
    std::string format_hotkey_combination();
    bool is_hotkey_combination();
    bool should_send_hotkey(const Key& pressed_key);
    void add_typed_character(const Key& key);
    std::string flush_typing();
    void reset_state();
    
    // Public getters for Python
    std::unordered_set<std::string> get_pressed_keys() const;
    std::unordered_set<std::string> get_sent_hotkeys() const;
    double get_last_hotkey_time() const;
    double get_last_key_time() const;
    bool get_is_typing_mode() const;
    double get_typing_timeout() const;
    
};

#endif // KEY_PROCESSOR_H