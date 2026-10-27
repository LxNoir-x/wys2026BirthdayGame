import ctypes

# Windows API 常量
VK_A = 0x41
VK_D = 0x44
VK_W = 0x57
VK_S = 0x53
VK_E = 0x45
VK_X = 0x58
VK_SPACE = 0x20
VK_UP = 0x26
VK_DOWN = 0x28
VK_LEFT = 0x25
VK_RIGHT = 0x27

# 键盘状态缓存
key_states = {}

class KeyboardUtils:
    @staticmethod
    def get_key_state(vk_code):
        """获取指定虚拟键的状态"""
        return ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000
    
    @staticmethod
    def is_key_pressed(vk_code):
        """检查指定虚拟键是否被按下"""
        return KeyboardUtils.get_key_state(vk_code) != 0
    
    @staticmethod
    def get_keys_pressed():
        """获取所有按下的键的状态"""
        keys = {}
        keys['a'] = KeyboardUtils.is_key_pressed(VK_A)
        keys['d'] = KeyboardUtils.is_key_pressed(VK_D)
        keys['w'] = KeyboardUtils.is_key_pressed(VK_W)
        keys['s'] = KeyboardUtils.is_key_pressed(VK_S)
        keys['e'] = KeyboardUtils.is_key_pressed(VK_E)
        keys['x'] = KeyboardUtils.is_key_pressed(VK_X)
        keys['space'] = KeyboardUtils.is_key_pressed(VK_SPACE)
        keys['up'] = KeyboardUtils.is_key_pressed(VK_UP)
        keys['down'] = KeyboardUtils.is_key_pressed(VK_DOWN)
        keys['left'] = KeyboardUtils.is_key_pressed(VK_LEFT)
        keys['right'] = KeyboardUtils.is_key_pressed(VK_RIGHT)
        return keys
