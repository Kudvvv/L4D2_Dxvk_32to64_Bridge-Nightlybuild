#pragma once
#include <cstdint>


class IL4NPluginV1 {
public:

	virtual ~IL4NPluginV1() = default;

	virtual unsigned int GetInterfaceVersion() { return 2; }
	virtual const char* GetName() { return "MyPlugin"; }
	virtual const char* GetVersion() { return "1.0"; }

	virtual void OnModuleLoaded(const char* module_name, std::uintptr_t handle) {};
	virtual void OnGameLaunch() {};

	virtual void OnD3DCreated(void* d3d) {};
	virtual void OnD3DDeviceCreated(void* d3d_device, bool is_dxvk) {};
};


class IL4NPlugin : public IL4NPluginV1 {

public:	// version 2
	/*
		title为真时返回标题字符串，明确该插件需要HUD菜单入口，否则返回nullptr
		提供标题之后，当用户请求进入菜单，会再次调用，用于返回菜单结构
		title为假时，返回定义菜单结构的KeyValues字符串，格式基于neko/config_template.vdf里的custom_commands
		额外添加了callback键来提供回调函数功能，也可以用来实现子菜单
		回调函数的定义如下：
			chost char* my_callback(void* user_data) {
				返回nullptr或者子菜单的KeyValues字符串
			}
		示例KeyValues字符串：
			"我的标题" {
				"项目1" { "cvar" "my_cvar_name" }
				"使用回调函数的项目" { 
					"callback" "0x12345"
					"user_data"	"0x12345"	// 可选键
				}
			}
	*/
	virtual const char* RequestHudMenu(bool request_title) {
		return nullptr;
	}
};

typedef IL4NPlugin* (*GetL4NPluginInstanceFunc)();

/*
	// bin/neko/plugins/MyPlugin.dll

	class MyPlugin : public IL4NPlugin {
	public:
		void OnModuleLoaded(const char* module_name, std::uintptr_t handle) override {
			std::string_view name = module_name;

			auto hModule = std::bit_cast<HMODULE>(handle);
			if (name == "client") {
				// do some thing...
			} else if (name == "engine") {
				// do some thing...
			}
		}
	};

	extern "C" __declspec(dllexport) IL4NPlugin* GetL4NPluginInstance() {
		static MyPlugin instance;
		return &instance;
	}

*/