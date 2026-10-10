本文档会随版本更新，部分功能会添加进hud菜单里方便使用

[2.51.0]
新增：VPK Overlay功能
新增：cvar l4n_vm_allow_movex
新增：cvar l4n_vm_allow_vaims
新增：concmd l4n_vm_inspect_config
修复：l4n_analyze_dumps输出的时间不匹配本机时区
修改：l4n插件的hud菜单提供了刷新菜单状态的接口


[2.50.3]
修改：启动时检查启动项的合规性

[2.50.2]
修复：PBR着色器的手电筒光照衰减问题
修复：动画镜头意外应用了开镜fov倍率调整

更多历史更新日志在本文档末尾

免责声明
    本工具使用了内存补丁技术，使用时风险自负，启动项加"-insecure"可以避免进入启用vac的服务器
    本工具的功能主要面向娱乐玩家与mod开发者，在禁用mod的服务器上会限制敏感功能，请勿用于影响他人游戏体验
    本工具能够加载用户提供的三方模块，该功能用来避免各种三方模块的加载点冲突问题，三方模块提供的内容和本工具无关
安装&更新：
    将安装包内所有的文件复制覆盖到游戏根目录即可
    仅安装着色器则跳过复制left4dead.exe文件
卸载：
    在游戏目录里搜索left4dead.exe和game_shader_generic_neko.dll删除即可，staem在启动游戏时会重新下载left4dead.exe
    其它文件不是必须删除的，这些文件不会被游戏使用


l4n是一个客户端补丁，给L4D2带来了大量改进
l4n能对部分引擎bug进行修复，其它已知bug因为触发条件低等，目前没有修复方案
目前只保证游戏版本2.2.4.3的兼容性，系统win10+，不符合该要求的环境可能会有兼容性问题


问题指南：
    确定问题前，请多次测试求平均，控制变量保证客观
    如果是和本工具有关的问题，欢迎对开发者进行反馈
    如果是不明确或无关的问题将不予理睬

    本指南还收录了一些游戏本身或第三方的问题
    游戏崩溃不一定和内存占用高有关，但是遇到崩溃时有必要先排查一下内存占用是否异常，尤其是在加载地图这种内存压力大的场景

    游戏目前还存在许多缺陷和bug，这些缺陷在进行非纯净游戏时会更容易暴漏出来(连接带插件装mod的服务器也不算纯净)
    Valve目前是不管这些bug的，除非是安全性bug
    安全性bug对于游戏公司和用户来说，需要承担的风险很大，对于v社官方的安全性更新请持理性态度
    如果需要避免steam游戏更新带来的麻烦，请直接将游戏文件夹移动到别处来使用

    l4n在游戏崩溃生成mdmp前添加了弹窗提醒，该机制依赖于windows系统的调用
    请客观看待，这能便于了解崩溃时发生了什么
    如果有显示代码，你可以通过观察代码的规律来确定是否是同个问题

    如果对游戏进行了重度修改，如大量mod大量插件dxvk补丁等，很容易遇到兼容性问题
    你的硬件配置，安装的mod，系统版本，驱动版本等影响游戏环境的因素和别人不一定完全相同，不适合套用到自己身上
    到处询问可能无果，不如学会基本的控制变量法自己去排查问题
    本指南可以给你一些排查问题的方向

    渲染相关，大部分涉及底层硬件，兼容性很容易出现问题
        a.尝试按照下方说明清除着色器缓存，有一个未知原因的bug会导致内存帧率异常
        b.切换显卡驱动的版本，如回退到25或24年的版本，用ddu卸载驱动断网重启安装(驱动需要提前下载好)
            显卡驱动更新会带来Vulkan驱动的更新，涉及到这方面的dxvk或者ReShade可能会出现兼容性问题
        c.切换dxvk版本，优先尝试2.3版本
            dxvk每个版本的优化策略不完全相同，在不同配置或驱动版本下可能出现兼容性问题
        d.禁用ReShade
            确定你的ReShade安装方式，然后进入游戏根目录
                如果是vulkan则备份移除ReShade.ini
                如果是dx9模式则备份移除d3d9.dll
        e.字体渲染优化补丁MacType
            字体替换只是它的一个小小功能，部分人使用该补丁来修改字体
            某些配置下会导致dxvk画面卡顿
        f.录屏工具、性能指示器、RTX Remix、小黄鸭等其它和画面渲染有关的修改
            这些修改会在游戏渲染管线里插入自己的功能，可能会出现兼容性问题
            你可以尝试禁用这些修改来排查问题
            如果使用了DXVK，禁用方法参考config_template.vdf里环境变量的示例参数

    已安装的MOD
        如果遇到了一些奇奇怪怪的小问题，这是最有必要排查的因素
        不要依赖游戏内的冲突检测和(附加内容)列表，参考下方话题
        创意工坊订阅像三方图这种文件大小很大的，貌似有内存异常占用的bug(来自一个罕见案例)
        不要忘记检查需要修改gameinfo.txt的mod，例如额外的武器音频

    检查其它让游戏变得不纯净的修改，如sourcemod插件平台，或其它在addons目录下的插件，xx补丁等

    检查启动项，或尝试使用“left4dead2 no-insecure.bat”来启动游戏

    你要是没招了，可以将游戏文件夹备份，steam重新下载最新版游戏，在纯净的环境下重新开始，慢慢把自己想要的修改加入进去并注意观察

    在steam游戏启动项里加上"-hide_neko"可以禁用l4n
    尝试使用不同的游戏启动方式时，你可能需要检查或迁移启动项，steam游戏属性里的启动项能生效的前提是需要通过steam启动游戏，bat或者快捷方式启动也是同理
    l4n目前不兼容HLAE
    添加-dev启动项可以在屏幕左上角查看控制台输出

    有些情况下需要明确区分服务端/主机是谁
        自己作为服务端的典型情况有：本地单人，本地多人联机(自己作为房主)
        他人作为服务端的典型情况有：连接官方/三方服务器，进入好友的联机房间
        vscript脚本是运行在服务端的，自己非主机的情况下，自己安装的此类mod会失效(ai增强、Admin System等)
        sourcemod插件运行在服务端

    贴花生成在高面数模型上的崩溃：
        贴花是一种贴在表面的效果，弹孔血迹喷漆等都是用贴花实现的，人物模型在受伤时会生成血迹贴花
        贴花在生成时会复制目标表面的网格，默认的缓冲区大小有限，遇到超过一定面数的网格时会出现内存溢出导致崩溃
        模型作者应避免单个$bodygroup/$body/$model里每个材质的面数不超过特定大小(大概是65536)
        可通过在材质里添加$nodecal 1禁止在该材质表面生成贴花
        可在启动项里加-lv启用低血腥模式，这会禁止一些血液贴花的生成
        可以在l4n菜单里找到禁用贴花的细致选项

    退出游戏时有概率崩溃
        已知NVIDIA 610版本的驱动和DXVI有兼容性问题
        在不使用l4n的情况下没有崩溃弹窗，可以通过检查游戏根目录有无生成新mdmp崩溃文件来确定

    在某些地图关卡加载时崩溃，有小概率能加载成功进图：
        例如：earlydays第一关、deadecho第二关
        禁用影响血液贴花效果的mod，此类mod和某些三方图关卡有兼容性问题，具体原因未知

    捡起武器后闪退：
        控制台会输出：Infinite origin/angles from vphysics!
        触发根源在掉落中的武器模型，其物理效果触发了bug
        崩溃点在服务端与vphysics.dll，自己以非主机的形式游玩，如连接服务器等不会遇到该问题
        该bug貌似和w模的形状和体积有关(注意这里说的不是碰撞体模型)
        貌似还有另一种因素会导致同样的闪退

    进图后突然退回到大厅：
        检查音频脚本的数量是否过多，通常在安装过多社区称为“音频库”的mod过多时发生
        控制台会输出：Host_Error: CEngineSoundServer::PrecacheSound...overflow

    Too many xx for xx buffer引擎错误弹窗：
        这和单帧里突然出现的几何体数量有关，尤其是生成贴花时会复制网格(如果贴花目标表面的面数很大)
        或者突然出现特别复杂的特效，一瞬间在画面里生成大量三角形，例如某些武器mod切换的粒子效果或者地图上的爆炸特效
        https://developer.valvesoftware.com/wiki/Too_many_indices_for_index_buffer
        可以通过修改l4n配置文件(convif.vdf)里的index_buffer_size或vertex_buffer_size来提高缓冲区大小
        修改会有屏幕炸面花屏的风险(此时本该弹窗)，引擎内部的逻辑不能妥善处理大于32768的缓冲区大小，目前的补丁只是为了防止触发错误弹窗

    L4D2是32位程序，实际只能使用3gb左右的内存，接近上限时游戏会越来越不稳定直到崩溃
    控制台命令l4n_game_usage 1可以监视内存占用(av项是游戏的可用内存大小，越低越危险，dc是datacache占用，ents是实体数量峰值)
    注意：dxvk/dx9和起源引擎的其它模块、游戏客户端服务端实体、引擎datacache等是会挤占内存的

    贴图占用大量内存：
        引擎在提交贴图数据给dx9时，使用了默认的内存管理，此时dx9在上传贴图到gpu显存时会留一份副本在cpu内存上，这会导致内存占用特别高(贴图是mod里最占空间的资产)
        要避免该问题请使用dxvk来代替原生dx9，dxvk对这种情况有特殊优化
        无法使用dxvk的情况下，可以进视频设置里将"模型/纹理细节"和"可用的页池内存"调为低，游戏将加载低分辨率的贴图来减少内存占用


    DXVK安装:
        首选：
            将dxvk安装包内d3d9.dll(32)复制到游戏主程序旁边
            确保没有-vulkan启动项
        次选：
            除非首选方法失败，否则不建议使用-vulkan启动项
            -vulkan启动项的DXVK dll位置在bin/dxvk_d3d9.dll，版本很老，可以手动替换成新版dxvk的dll
            steam可能会自动验证完整性导致dxvk_d3d9.dll被覆盖回去
        注意：
            使用dxvk后，Reshade的安装要选择Vulkan
            如果dxvk不能正常使用，如全屏模式出现异常，无法识别独显等，尝试去修改dxvk的配置文件
            安装的mod里如果贴图占用很高，你的显存应该要大于4gb
        确定dxvk是否生效：
            控制台运行l4n_env_report
            如果是-vulkan启动项，可以在任务管理器里看到游戏的标题里是否带了vulkan
            删除游戏根目录下的left4dead2_d3d9.log，启动游戏能否看到该文件的生成

    着色器缓存：
        不同版本的l4n着色器功能会有差别，安装/更新/切换版本后可能会触发着色器缓存编译
        切换显卡驱动版本或者dxvk版本时，包括第一次使用dxvk，可能触发着色器重编译(包括引擎自带的着色器)
        着色器编译时可能出现掉帧，内存占用高的情况，如果很长一段时间后问题依旧，尝试按照以下指南清除着色器缓存
            控制台运行l4n_open_shader_cache_dir打开着色器缓存目录后关闭游戏
            如果是550文件夹，删除目录下的所有文件夹
            如果是AMD或NVIDIA文件夹，某些厂商的命名会有出路，删除所有Cache结尾的文件夹最稳妥
            打开失败或其它GPU核心厂商的情况下，请自行搜索方法

    mod检查的注意事项：
        地图类mod可能会有模型、材质、cvar、脚本污染冲突的问题，这类mod带有战役标签，冲突检测会忽略这类mod
        污染的例子：London Calling、New York、Go Postal Postal 3
        如果是创意工坊订阅的mod，引擎会使用创意工坊的信息来代替addoninfo的部分参数
        某些mod因为bug不会显示在游戏内的mod管理列表里
        bug mod出现的可能原因有：mod没有提供info；mod文件名或路径过长或者出现特定字符
        mod挂载和mod列表显示是两套逻辑，bug mod能够正常生效，这也意味着也bug mod能够和正常mod产生文件冲突
        冲突检测只在mod列表里显示的mod之间检测和提示，bug mod可能会产生隐患或不必要的困扰
        已知冲突检测不会检测addonimage.jpg/addoninfo.txt/sound.cache等
        addons目录下的某个文件夹里如果有addoninfo.txt，该文件夹会被文件系统挂载，你可能在解包vpk时不经意留下了这种文件夹
        因为以上种种原因，不能完全信任mod列表和冲突检测结果
        mod管理推荐：
            使用资源管理器
            打开bin\neko\other_tools.7z\vpkshellextensions文件夹(游戏根目录或l4n安装包)，获取vpk的资源管理器插件还有安装教程
            打开详细信息窗格，用于显示info信息(作者、标题、地图代码、封面、描述等)
            可以根据info信息排序，搜索(和mp3、doc这类资源管理器默认支持的文件使用是一样的)
            通过将文件移动到别处的方式来禁用mod
        更彻底的冲突检测：
            在控制台运行l4n_force_dummy_addoninfo
            打开内游戏内mod列表
            发现冲突后打开控制台，查看哪些文件冲突了
            注意：冲突检测只检测资产路径冲突，能过冲突检测不能代表和其它mod之间一定没有兼容性问题
        查看实际挂载的mod：
            默认情况下，起源文件系统在读取资产时，遵循以下2点：
                1.先从排名第一的挂载点开始读取文件
                2.遵循第一点的情况下，vpk优先级比文件夹高
            在控制台里查看起源文件系统的挂载点：
                查看vpk运行：show_addon_load_order
                查看文件夹运行：path

    材质透明效果：
        第一种透明过渡效果最好，但是可能会出现深度缓冲问题导致前后关系错乱
        第二种只有完全透明和完全不透明两种状态，性能最好
        第三种依赖MSAA抗锯齿，质量与MSAA等级成正比
        MSAA透明的具体效果可能和硬件或图形接口有关，例如在某型号的gpu上，dx9会出现过渡断层，dxvk(2.7.1)则是过渡效果更好的抖动透明
        因此需要明确的是(尤其是mod作者)：你看到的MSAA透明效果可能和别人看到的不一样
        使用Reshade的情况下，一般是要关闭MSAA的

    模型边缘抖动鬼畜穿模面闪烁：
        在世界坐标绝对值很大的区域，如官图c8m3_sewers开局安全屋里会遇到, 控制台运行status能看到x坐标的数值特别大有1w左右，这是3d游戏会面临的坐标精度问题，地图作者做图时应避免此类问题

    动态光源：
        https://developer.valvesoftware.com/wiki/Light_dynamic
        引擎对动态光源的优化不是特别好，在某些复杂场景下会导致帧数爆降

    datacache(dc)：
        默认情况下引擎的dc内存上限是256mb
        达到dc上限后可能出现音频卡顿无声、帧数爆降、游戏不稳定崩溃等问题
        一些三方图自带的资产比较大，会直接把256吃满，如黎明或切尔诺贝利
        通过添加-heapsize启动项来修改上限，单位是kb，有数值溢出的bug，不合适的数值大小可能会出现问题
        使用l4n时会被强制锁定到2048MB，这个大小一般是吃不满的，不必过多担忧
        
        // 控制台运行"mem_dump"或者"cache_print_summary"可以查看dc的详细占用以及实际上限，最后一行可以看到所有dc项的内存占用总和
        // 以下是"Datacache reports"的说明：
        //      [WaveData]是音频缓存，满了会自动清理旧音频数据。
        //      当前l4n版本将上限锁定到512mb，太高会导致无用的音频数据一直堆积，挤占浪费内存空间
        //      里面会有角色语音、枪声、音乐、等..

        //      [AnimBlock]是模型动画的缓存
        //      如果占用特别高(如200mb)的话，可能是装了跳舞相关的动画mod，已知此类mod最高能包含100个舞蹈左右，
        //      一个舞蹈大概1到2分钟，加起来内存占用非常的直观，建议在不需要时禁用此类mod
        
        //      [Modelxxxx]是模型的缓存，大小主要和模型的面数有关
        //      用于存放当前地图要用到的模型，如幸存者、武器、车辆、盆栽、感染者等...
        //      进地图后在控制台运行"cache_print"输出内存占用最高的模型
        //      路径里带survivor或infected的是角色模型，一般排最前面（角色模型的体积大，精度要求会比较高）
        //      路径里带w_models或者v_models则是武器的第三人称或第一人称模型
        // 其它没提到的项目是无关紧要的

    "no free edicts"错误弹窗：
        https://developer.valvesoftware.com/wiki/Entity_limit
        游戏中实体的数量达到2048会触发，目前没有有效的非官方措施对这个上限进行修补
        -num_edicts启动项是属于金源引擎的启动项，在起源上没有任何作用
        除非v社官方出手，第三方想解决该问题的工作量和难度很大，实体是客户端/服务端逻辑里最常见的对象，第三方需要要找出大量的点位进行修补，客户端和服务端都要一并修补，因为实体是需要在客户端和服务端之间进行网络同步的
        某些地图开局占用能到1700左右，加上服务器插件或者vscript脚本一般会生成一些功能性实体，这会增加遇到该问题的风险

    地图曝光过暗：
        某些gpu硬件会遇到这样的问题，例如Intel的一些型号，通过修改video.txt可以解决
        如果使用l4n，在控制台运行mat_tonemapping_occlusion_use_stencil 1即可

    模型不可见：
        这种情况下控制台会有：CUtlLinkedList overflow! (exhausted index range)
        具体原因未知

    BindVertexTexture失效问题：
        该问题会导致描边蒙版失效，从2.47.1版本的l4n起有专门的补丁修复
        问题出现在引擎内部的CommitVertexTextures()里
        函数内使用了(textreHandle>=0)来判断贴图有效性
        由于handle(int类型)实际为内部对象的指针裸包装(bit_cast)，如果内部对象分配在高位内存区域，handle的值会变成负数
        结果是顶点着色器无法正常采样贴图，渲染结果异常
        在发现原因之前，通过改变安装的mod数量，进入不同的地图，有概率触发
        启用mimalloc的情况下能够稳定复发，因为mimalloc喜欢从高位布局开始分配内存

制作用于NekoSky的天空盒叠加纹理：https://rafradek.github.io/Mishcatt/
    背景需纯黑，建议使用RGB888的格式，DXT系列不适合带线条的插画
    vtf文件放在游戏根目录的left4dead2/materials里，控制台设置贴图示例：mat_nekosky_overlay_lf "vtf文件名或留空取消设置"

===========基本功能==========
    主菜单(l4n_menu)默认按"\"显示，"-"上一页 "+"下一页
    默认解锁-heapsize的512mb上限，该上限与声音卡顿丢失、部分闪退、帧数爆降有关
    使-heapsize的大小能够完整传递到引擎的datacache模块，该模块的接口接收uint的字节数单位(b)数值，引擎在调用前使用了int来计算字节数，导致实际数值不可控，如2097152kb因为int溢出实际为1kb
    玩家模型身高调整
    字体替换
    为addoninfo出现问题的mod添加元数据
    强制幸存者手模与第三人称模型同步
    玩家模型死亦瞑目
    修复了客户端预测播放了空数据的动画导致闪退（使用xdReanimsBase时可能会遇到这种bug）
    游戏崩溃前的问题检测和提示，有助于找到崩溃原因
    RestrictAddons禁用的情况下，使sv_consistency 1的作用失效
    scheme_overrides
    sequence_event
    exe导出用于AMD和NVIDIA显卡的全局变量，能够帮助DXVK识别到独显
    有关(convar/concmd/控制台命令)的详细说明在下方，ctrl+f以快速定位

======== ReShade Bridge ========
    此功能的兼容性不是很高，不建议使用，已经停止维护
    ReShade Bridge能够将ReShade滤镜集成到L4D2的渲染管线里
    该功能需要Addon版的ReShade，如果ReShade插件管理里显示"只提供有限的插件功能"，则该ReShade版本是非Addon版
    ReShade插件管理里确保"L4N ReShade Bridge"已经启用，如果没有该项目，请检查ReShade.log
    控制台运行"l4n_reshade_draw 1"后，可以在游戏渲染HUD前渲染ReShade效果
    因涉及底层渲染，ReShade Bridge在某些环境下可能无法正常工作，可能的因素有：dxvk版本、ReShade版本、驱动版本、硬件配置、有无dxvk，有无MSAA抗锯齿等
    d3d9不能读取启用了MSAA抗锯齿的深度缓冲区，Generi Depth插件在这种情况下不能正常工作，考虑禁用MSAA抗锯齿或者使用dxvk让ReShade运行在vulkan模式下
    ReShade Bridge会自动锁定Generic Depth的设置，可在启动项添加"+l4n_reshade_depth_resolve 0"来禁用该特性
    在使用本功能的情况下，存在一些未知因素，可能会导致内存占用异常，请尝试使用config_template.vdf里的示例参数

======== l4n survivor ========
    此功能也可称为"l4ns"或"扩展幸存者模型"
    普通幸存者mod是通过替换八个幸存者的模型文件来实现的，只能在那八个文件里做文章
    l4ns则是使用扩充的模型文件，主动修改客户端玩家实体要使用的模型，效果取决于玩家数量或已安装适配mod的数量
    l4ns还支持(头像/倒地图标/Bot名字)的替换，当前版本需要将l4n_patch_team_player_display设置为1才能生效
    注意事项：
        此功能的使用与传统角色mod的使用是冲突的，避免混合使用以免造成不必要的困扰
        l4ns生效的情况下，普通幸存者角色mod没有机会正常使用，因游戏的底层机制，八个幸存者的模型会被强制加载，此时禁用普通幸存者角色mod可以节省内存占用
        模型是动态加载的，无用的角色模型会释放内存占用，新玩家加入时分配新模型可能会卡顿
        以玩家实体为单位会遇到一些问题
            大部分非玩家实体在客户端看来是不知道和哪个玩家有关联的，例如tumtara测试图里展示角色模型的实体
            对于和玩家有视觉关联的非玩家实体，l4n对部分情况做了有限的猜测和适配，如：能被电击的幸存者死亡实体，第一人称腿插件生成的实体，倒地爬行插件生成的实体
            多人联机可能会出现多个玩家都是zoey模型的情况，不应该通过实体所用的幸存者模型来判定所属玩家，这样又会被困到八个的维度里
    安装包里的to_l4n_survivor工具使用说明
        用于将普通角色mod转换成支持l4n_survivor的mod
        推荐使用八人包，同时选中八人包里的替换八个幸存者角色的vpk，一同拖动到to_l4n_survivor.exe上即可开始转换
        没有条件的情况下，用替换某个幸存者角色的vpk也可以转换，此功能目前是实验性的
        材质vpk或其它依赖性vpk也可以一并拖进去合并
        注意不要混合别的mod同时转换，比如拿a角色替换bill和b角色替换zoey(以此类推)的vpk一起
        转换前的文件请确保必要的文件名前缀一致，例如AA_bill、AA_bill、AABB_xxx转换后的文件名会是AA，或者手动解包合并打包后转换
        如果转换后的文件，和已经安装的mod文件命名冲突了，请重命名原始文件后再重新转换，而不是重命名转换后的文件
    相关cvar
        l4nsurvivor                       是否启用，参数2则不替换队友模型
        l4nsurvivor_allocation_algorithm  给队友分配模型的算法(0按uid，1根据steamid，2随机，3随机不重复)
        l4nsurvivor_allow_bot             是否允许bot使用
        l4nsurvivor_trace                 输出调试信息

======== Neko_Engine_Post着色器 ======
    添加“-l4n_use_neko_engine_post”启动项来使用，l4n将接管引擎的后处理渲染
    提供以下功能：
        色调映射：能够使画面亮处不会过曝丢失太多细节，脱离老引擎的刻板印象
        伽马调整(gamma)：和视频设置里亮度滑块类似的作用，可以在非独占全屏时生效
        泛光(NekoBloom)：使画面亮处更有氛围感

========以下功能需要MOD适配========
    l4nscope，武器模型为单位的自定义开镜效果
    形态键眼追
    PBR着色器(有功能可以自动适配)
    NekoToon着色器(有功能可以自动适配)
    NekoSky着色器(有功能可以自动适配)
    vpk音频库与pcf粒子的额外加载，无需mainfest依赖
    模型的组件切换与材质切换
    动画实体的足IK修正
    新增的材质代理
    l4n_survivor

========l4n lookat========
    +l4n_lookat [itempickup/helpinghand/fidget]
    触发物品伸手动画的绑定：bind v "+l4n_lookat itempickup"
    触发队友伸手动画的绑定：bind v "+l4n_lookat helpinghand"
    触发Fidget动画的绑定：bind v "+l4n_lookat fidget"
    随机触发两种动画的绑定：bind v "+l4n_lookat"
    循环动画默认只播放一次，长按则保持播放循环动画
    mdl可添加备注来提高使用体验(详见mdl_extension.qc)
    concmd l4n_lookat_vmconfig的参数信息
        itempickup_onlyloop     0或1, -1切换
        helpinghand_onlyloop    0或1, -1切换
        itempickup              0或1, -1切换
        helpinghand             0或1, -1切换
        fidget                  0或1, -1切换

======== 第一人称模型(v模)展示模式 ========
    mdl可定义名为l4n_inspect的Attachment作为默认原点
    convar l4n_vm_inspect_mode              启用后按住1到9之间的数字键，再配合鼠标滚轮来调整旋转/平移/原点的xyz分量
    concmd l4n_vm_inspect_config
        无参数打印当前的设置
        reset: 清除保存的设置

========== VPK Overlay ==========
    能够在每次加载地图时，自动从备选库中为你随机、顺序挑选或指定挂载不同的VPK模组，无需重启游戏
    例如：每次换地图自动换一把不同皮肤的枪，或切换不同的幸存者模型
    更多信息在config_template.vdf里

部分cvar(convar)的值是没有启用保存功能的，可以把cvar带上期望值写进autoexec.cfg里
如果停用l4n或回退l4n版本，保存的值可能会丢失，通过事先备份config.cfg文件，之后在控制台运行exec并指定备份的cfg文件还原设置
控制台运行"l4n_revert_cvar cvar_name"可以将指定cvar恢复到默认值，或者控制台输cvar的名字并运行来查看默认值

此列表包含了一些上面没提到的功能：
【ConVar】
    l4n_allow_flashlightmuzzleflash 1   是否允许第一人称手电筒火光
    l4n_game_hud_visible 1，            控制游戏HUD的显示与隐藏；
    l4n_specialinfected_randommodel 0   特感随机使用一二代模型的开关
    l4n_vm_sway 1                       v模视角转动滞后开关
    l4n_vm_sway_interp 0.1,             v模随视角转动滞后恢复时间，设置为0则禁用v模随视角转动的滞后(sway)效果
    l4n_vm_sway_scale 1.6,              v模随视角转动滞后幅度
    l4n_vm_sway_ignore_helpinghand 1    是否在触发伸手动画时禁用sway效果，启用后可能会导致一些插件的动画(如ADS)没有sway效果，禁用后可能会导致武器高频抖动
    l4n_vm_offset_y 0,                  全局v模位置偏移y
    l4n_vm_offset_z 0,                  全局v模位置偏移z
    l4n_vm_offset_x 0;                  全局v模位置偏移x
    l4n_vm_allow_camera_animation       允许v模动画驱动摄像机
    l4n_vm_allow_movex                  允许v模移动动画
    l4n_vm_allow_vaims                  允许v模上下瞄准动画
    l4n_menu_offset_x 0, 
    l4n_menu_offset_y 0;                控制l4n_menu显示的位置
    l4n_menu_font_size 32，             l4n_menu的字体大小
    l4n_commoninfected_noragdoll 0，    大于零禁用普通感染者死亡时的布娃娃效果，可以提供更清爽的清怪体验(需搭配-lv启动项使用)
    l4n_mat_colorcorrection 1，         是否允许色彩校正(颜色滤镜)
    l4n_tonemap_scale 1,                控制hdr的曝光强度，不支持禁用hdr的地图
    l4n_survivor_stylized_amibentlight 0，幸存者实体使用风格化环境光的开关
    l4n_survivor_lighting_scale 1,        控制幸存者实体的光照倍率
    l4n_game_usage 0,                   hud显示和引擎稳定性有关的数据(datacache，ents是实体峰值数量，av是游戏进程的可用内存)
    l4n_game_usage_pos 32，             控制l4n_game_usage显示的位置
    l4n_game_usage_padding 24，         控制l4n_game_usage距屏幕边缘的位置
    l4n_survivor_sequence_strip         是否修复幸存者mod的动画数量，修改后需重启游戏，更多信息查看config_template.vdf
    l4n_prevent_varms_stretching 0      是否禁止第一人称手模动画里部分骨骼的拉伸
    l4n_player_list_show_steam_avatar 1         +l4n_player_list显示steam玩家头像
    l4n_player_list_vomitjar_icon_clip 0        +l4n_player_list裁剪胆汁图标
    l4n_engine_post_allow_local_contrast 1      是否允许使用局部对比度(-1仅负, 0完全禁用, 1正负, 2仅正)
    l4n_engine_post_allow_vomit 1               是否允许胆汁模糊视线效果
    l4n_survivor_scale 1.0                      全局修改幸存者的大小
    l4n_enhanced_material_pxory 1               是否增强部分材质代理，如EntityRandom会同步第一人称和第三人称
    l4n_proxy_entity_random_seed_offset 0.0     EntityRandom的随机数种子偏移
    l4n_force_skyname ""                        覆盖天空盒材质，使用参数""还原
    l4n_disable_survivor_bandage 1              是否禁用生还者模型的绷带粒子，原版的绷带粒子会和生还者模型缩放冲突
    l4n_auto_flush_unused_models 1              是否自动清理无用模型的缓存，参数0、1或2
    l4n_player_identity_render_color 0          是否禁止玩家相关实体的染色
    l4n_mat_specular 1                          是否允许环境反射，相比mat_specular，此方法更加严格且快速
    l4n_env_cubemap_redirect 0                  启用时会尝试将env_cubemap的加载如"c1841_-940_69.hdr.vtf"重定向到"c1841_-940_69_hdr.pwl.vtf"
    l4n_use_nekosky 1                           是否使用l4n的nekosky着色器来渲染天空
    l4n_proxy 1                                 是否启用l4n的材质代理
    l4n_ambient_darkness_limit 0.0              环境光的暗度限制
    l4n_lightmap_darkness_limit 0.0             光照贴图的暗度限制
    l4n_vm_pin 0                                固定viewmodel实体
    l4n_allow_hud_team_player_display 1         允许HUD显示队友状态
    l4n_flashlight_factor 1.0                   手电筒亮度倍率
    l4n_flashlight_r 1.0                        手电筒颜色R倍率
    l4n_flashlight_g 1.0                        手电筒颜色G倍率
    l4n_flashlight_b 1.0                        手电筒颜色B倍率
    l4n_allow_lobby_cheats 0                    Can't use cheats now; please exit to main menu and start your own listen server with "map mapname" so that you could enable cheats.
    l4n_force_dummy_addoninfo 0                 参考上方mod检查的注意事项
    l4n_patch_team_player_display               是否接管HUD BOT名字和头像的显示，数值2则忽略BOT名字
    l4n_max_background_bik 5                    大厅背景视频的数量，如果你只有一个，不想要复制4遍并节省空间，可以设置为1，如果你不满足5个随机，可设置为大于5的数值
    l4n_to_nekotoon_allow_outline 1             l4n_to_nekotoon转nekotoon时是否启用描边
    l4n_allow_consistency_check                 禁用则跳过一致性检查，无论sv_consistency的值如何
    l4n_thirdpersion_crosshair_alpha            精确第三人称准星透明度
    l4n_thirdpersion_crosshair_scale            精确第三人称准星缩放
    l4n_thirdpersion_crosshair_dynamic          精确第三人称准星动态缩放
    l4n_allow_draw_sprite 1                     是否允许渲染Sprite，常用于在光源处模拟光芒或光晕效果，关闭后可能影响某些关卡的机关状态提示
    l4n_dlight_muzzleflash 0                    是否启用第一人称枪火光源，可选值0(禁用),1(遵守消音),2(不遵守消音)
    l4n_dlight_muzzleflash_brightness           第一人称枪火光源亮度
    l4n_dlight_muzzleflash_distance             第一人称枪火光源最大发光距离
    l4n_dlight_muzzleflash_prevent_tonemapscale 抑制曝光影响亮度
    l4n_server_filter 1                         服务器过滤
    l4n_thirdperson_fire_sound_fix              修复第三人称开火声音
    l4n_reshade_draw                            是否在hud之前渲染reshade效果
    l4n_scripted_hud_allow                      是否允许脚本化HUD渲染
    l4n_scripted_hud_allow_slot[1~15]           是否允许脚本化HUD某个slot的渲染，15个slot可选
    l4n_allow_entity_dissolve                   是否允许实体消逝效果
    l4n_decal_allow_staticprop 1                是否允许静态道具贴花效果
    l4n_decal_allow_entity 1                    是否允许实体贴花效果
    l4n_decal_allow_special_infected 1          是否允许特殊感染者贴花效果
    l4n_decal_allow_survivor 1                  是否允许幸存者贴花效果
    l4n_decal_allow_common_infected 1           是否允许普通感染者贴花效果
    l4n_hudmenu_offset_x                        Hud菜单的x位置偏移
    l4n_hudmenu_offset_y                        Hud菜单的y位置偏移
    l4n_view_punch_scale                        受击晃动强度
    l4n_screen_shake_scale                      屏幕震动强度
    l4n_hudscope_draw_override                  是否接管开镜HUD的渲染，关闭会影响l4n与hud开镜有关功能的正常运行
    l4n_hudscope_draw_padding_block             HUD开镜黑边填充
    l4n_hudscope_draw                           HUD开镜渲染
    l4n_vm_addon_fix                            是否强制手模匹配玩家模型，这可以解决一代图使用二代角色的手模不匹配问题
    l4n_specialinfected_random_scale            非零启用特感模型随机缩放，绝对值为缩放范围
    l4n_survivor_random_scale                   非零启用幸存者模型随机缩放，绝对值为缩放范围
    l4n_commoninfected_random_scale             非零启用普感模型随机缩放，绝对值为缩放范围
    l4n_scope_fov_scale                         开镜fov缩放
    l4n_scope_fov                               开镜fov
    l4n_scope_fov_adjust                        开镜fov缩放调整(滚轮，蹲下微调)
    l4n_vm_dual_quaternion_skinning             为v模材质添加"$DualQuatSkinning 1"
    l4nsv_steam_auth_bypass                     是否绕过玩家的steam验证，可以避免"No Steam Logon"问题
【ConCommand】
    l4n_vm_offset2 [x/dx/y/dy/z/dz/reset] [value], 为当前使用的v模设置位置偏移，带d的是增量；参数reset归零xyz
    l4n_menu                                显示l4n主菜单
    l4n_survivor_sequence_test，            检查场景里幸存者模型的动画有无问题，一般是和动画mod有关
    +l4n_player_list，                      显示更多玩家信息的面板；添加参数1来bind后，则双击才能显示，单击显示原版计分板
    l4n_placelight exponent 1 radius 2000   放置动态环境光源，添加参数“remove”或绑定按键双击则移除。此功能适用于室内补光，动态光源的性能不好，可能会出现大幅掉帧
    l4n_vm_selfillum                        调整当前v模的自发光强度，有正负号时数值代表增量
    l4n_mat_showtextures                    相比mat_showtextures多了字符串匹配的功能
    l4n_vm_2pbr                             将当前v模的材质转换为PBR材质，适用于PBR2Source工具生成的材质；参数0还原材质
    l4n_print_launch_options                输出当前能被游戏识别的启动项
    l4n_reset_player_render_color           重置玩家实体的颜色
    l4n_env_report                          输出游戏运行环境的信息
    l4n_flush_unused_models                 立即清理无用模型的缓存
    l4n_random_player_render_color          随机玩家实体颜色
    l4n_to_nekotoon                         无参将自己的模型材质转为NekoToon，参数pickplayer针对准星处玩家，参数varms针对当前手模
    l4n_nekook_path_append "c:/test"        添加一个高优先级资产搜索路径，比VPK内的文件优先级高
    l4n_nekook_path_remove "c:/test"        移除一个高优先级搜索路径
    l4n_cvar                                输出或设置convar的值，主要用于控制台无法直接访问的convar
    l4n_revert_cvar "cvar_name"             使指定的convar恢复到默认值
    l4n_buildcubemaps                       一键配置好环境然后编译cubemaps，添加allow_specular参数则不禁用反射并编译；https://developer.valvesoftware.com/wiki/Cubemaps
    l4n_fast_record                         开始录制demo，自动命名
    l4n_refresh_entity_random               刷新所有实体的随机数
    l4n_clear_datacache                     清理datacache
    l4n_is_proxy_exist "proxy name"         检查材质代理是否存在
    l4n_open_shader_cache_dir               打开着色器缓存目录
    l4n_print_environment_variables         打印游戏进程的环境变量
    l4n_reload_vgui_schemes                 重载vgui，可用于替代mat_setvideomode修改分辨率触发重载的方法
    l4n_print_particles_manifest            输出particles_manifest的内容
    l4nsurvivor_roll                        切换到下一个l4nsurvivor模型，无参数为自己，参数teammate则为所有队友切换
    l4n_custom_command_menu                 加载配置文件并显示自定义命令菜单
    l4n_reload_sequence_event_vdf
    l4n_reload_config
    l4n_analyze_dumps
【NekoShaders】
    mat_outline_thickness_scale 1.0     描边粗细倍率，0则关闭描边
    mat_pbr_where 0                     设置1则高亮闪烁PBR材质，用于查找哪些材质使用了PBR着色器
    mat_nekosky_overlay_                设置贴图路径，作为NekoSky天空盒某个面的叠加纹理，六个面的后缀是rt,bk,lf,ft,up,dn
    mat_nekosky_overlay_strength 1.0    NekoSky叠加纹理的强度
    mat_neko_allow_invert_tonemap 1     是否抑制某些色调映射曲线对颜色的影响(仅支持部分着色器如nekotoon)，数值2则允许在nekobloom启用的情况下生效
    mat_nekorefract_color_invert_exponent
    mat_neko_dual_quaternion_skinning
    nekotoon:
        mat_nekotoon_allow_lightwarp 1      是否使用非平展渲染
        mat_nekotoon_lambert_factor 1       环境或手电筒光照的阴影强度
        mat_nekotoon_lighting_scale 1.0     光照倍率
        mat_nekotoon_rimlight_boost 3.0     $rimlightboost的倍率
        mat_nekotoon_rimlight_viewmodel_boost 1
        mat_nekotoon_brightness_limit 1.0   渲染结果的亮度限制，用于避免模型过曝
        mat_nekotoon_darkness_limit 0.02    渲染结果的暗度限制
        mat_nekotoon_lazy_texture_load 0    是否在渲染时才加载对应材质的贴图
        mat_nekotoon_ignore_flat_normal 1   是否禁止使用"flat_normal"以提升性能，数值2则更严格
        mat_nekotoon_normalized_lightwarp   统一lightwarp的最大亮度，可用于解决不同mod作者间光照标准不统一的问题
    neko_engine_post:
        mat_neko_tonemapping_algorithm 6    ToneMapping曲线(0:Linear/1:Reinhard/2:Filmic(神秘海域2)/3:CE(CryEngine2)/4:ACES(UE4默认)/5:GranTurismo/6:Neutral(Unity)/7:NAES/8:LOG2(终末地)/9:AgX)，需添加-l4n_use_neko_engine_post启动项才能使用
        mat_neko_tonemapping_force_linear 0 强制使用linear tonemapping，用于调试
        mat_neko_gamma 2.2                  和视频设置里亮度类似的效果，可以在非独占全屏时生效
        mat_neko_engine_post_after 0        对比原始画面的比例
        mat_nekobloom_luminance_threshold  NekoBloom激发亮度
        mat_nekobloom_scale                NekoBloom强度
        mat_nekobloom_max_brightness       NekoBloom亮度限制
        mat_nekobloom_radius               NekoBloom模糊半径
        mat_nekobloom_maptex_strength      NekoBloom蒙版强度
        mat_nekobloom_maptex_weight        NekoBloom蒙版权重
        mat_nekobloom_blend_mode           NekoBloom混合模式(1add,2screen,3softlight,4replace)
        mat_neko_pre_tonemapping           是否在更早的时机应用tonemapping曲线(启用reshade bridge时会自动启用，不兼容部分配置)

l4n各种配置文件的模版(使用记事本打开来查看具体作用)：
    scheme_overrides_template.vdf
    localize_overrides.vdf
    config_template.vdf
    server_name_filter_template.txt

【other_tools.7z/VPKShellExtensions】
    Windows资源管理器显示vpk文件略缩图和mod标题元信息的插件



============For Modder==========
【neko_proxy.vmt】
    平台扩充的材质代理文档，目前有获取弹药数量和备用弹药数量的代理

声音脚本加载:
    "l4n/scripts/sound"目录下的txt文件会当做声音脚本加载，用于扩充声音事件(vpk里需要带sound.cache)。
    示例：
        - l4n/scripts/sound/my_script.txt
        - sound/aaaa/ohhh.wav
        - sound/sound.cache
    pcf和声音脚本的命名应该以“作者名_AK47.txt”或类似的思路，减少文件冲突的可能性；
    其它文档：
        https://developer.valvesoftware.com/wiki/Looping_a_sound
        https://developer.valvesoftware.com/wiki/Soundscripts

【source_nekomimi.exe】        
    音频工具，用于在wav语音之间复制口型数据，或者生成sound.cache(目前不支持带口型数据的sound.cache生成)

pcf粒子文件加载:
    "l4n/particles"目录下的任意的pcf文件会被粒子系统加载(文件名"!"前缀有对应的效果)，用于扩充粒子特效。

【mdl_extension.qc】            
    mdl适配l4n的qc示例

【other_tools.7z/nekomdl.exe】  
    更好，更快，更强大的mdl编译器

【other_tools.7z/nekook.exe】   
    根据配置启动游戏或者引擎工具，同时将当前目录挂载到引擎的文件系统里，使当前目录的游戏资产能以最高优先级被引擎读取

【copy_sentence.bat】
    从游戏原版语音文件复制口型数据到自定义语音文件的预设

【build_sound_cache.bat】
    用于快速生成sound.cache，主要用于音效，不适合带口型数据的语音


===========历史更新日志==========
[2.50.1]
新增：convar l4nsurvivor_trace
修复：上个版本带来的栈异常问题

[2.50.0]
修改：将游戏日志系统的所有通道都保存到logging_system.log里
新增：concmd l4n_analyze_dumps
修复：l4n_vm_dual_quaternion_skinning打开后需要重新刷新手模才能看到效果
修改：改进崩溃处理，使用crashpad来生成崩溃转储，保存位置位于crash_dumps/reports
修改：崩溃时将游戏日志保存到crash_dumps/attachments文件夹内
修改：更新l4n插件接口到版本2，公开了hud菜单的访问

[2.49.1]
修复：+l4n_lookat遇到没有loop动画的模型不会触发extend动画
修改：to_l4n_surrivor输出的文件使用更短的前缀"[l4ns]"

[2.49.0] 2026-09-26
修改：left4dead.exe导出用于AMD和NVIDIA显卡的全局变量，帮助DXVK识别到独显
修改：l4nsurvivor_allocation_algorithm新增不重复随机选项
新增：concmd l4n_lookat_vmconfig
移除：+l4n_lookat的双击功能
修复：l4n_survivor选择准星处玩家功能在未命中实体时的崩溃问题
新增：cvar l4nsv_steam_auth_bypass，用于避免自己为主机时遇到"No Steam Logon"

[2.48.1]
修复：上个版本的一个崩溃bug

[2.48.0]
修改：非站立状态下不会应用player_foot效果
新增：convar mat_neko_dual_quaternion_skinning
新增：convar l4n_vm_dual_quaternion_skinning
新增：nekotoon参数$DualQuatSkinning
新增：nekotoon参数$BackFaceShade
修改：l4n_vm_inspect_mode会尝试使用名为l4n_inspect的Attachment作为原点

[2.47.2]
修复：nekotoon的$BaseTexture2在自发光通道的混合问题

[2.47.1]
修复：引擎CommitVertexTextures的handle判断问题，该问题会导致描边蒙版失效
修改：readme_l4n增加了CommitVertexTextures的细节说明
修改：config_template增加了mimalloc的细节说明

[2.47.0]
新增：nekotoon参数$RimShade等
新增：nekotoon参数$BaseTexture2Transform, $BaseTexture2BlendMode, $BaseTexture2Panosphere等
新增：outline参数$OutlineViewModelFactor
修改：convar l4n_scope_fov_scale_adjust改名为l4n_scope_fov_adjust

[2.46.0]
新增：convar l4n_scope_fov_scale
新增：convar l4n_scope_fov
新增：convar l4n_scope_fov_scale_adjust
修复：l4n hud菜单返回上一菜单后页面重置

[2.45.1]
移除：convar l4n_charactor_model_random_scale
新增：convar l4n_specialinfected_random_scale
新增：convar l4n_survivor_random_scale
新增：convar l4n_commoninfected_random_scale

[2.45.0]
修复："l4n_vm_allow_camera_animation 0"导致某些v模动画的手臂出现问题
修改：+l4n_look_at使用ACT_VM_FIDGET作为备选动画
修改：移除config.vdf的key_bind_acts配置项，使用key_bind_acts.vdf文件替代
新增：nekotoon参数$LightingSaturation
修改：$EmissionTonemapScaleAmount在$EmissionTint小于0.05的时候会被设置为0，除非显式声明

[2.44.2]
修复：l4n_patch_team_player_display对非正方形倒地hud的判断问题

[2.44.1]
新增：convar l4n_vm_addon_fix
修改：将convar l4nsurvivor设置为可保存
修改：l4n_patch_team_player_display会根据倒地hud元素的尺寸来显示倒地图或或头像
修改：将convar l4n_pin_viewmodel改名为l4n_vm_pin
修改：优化l4n_vm_inspect_mode的体验，新增了shift微调与按0键保存当前参数的功能
修复：l4n_vm_allow_camera_animation关闭时可能的视角颠倒问题

[2.44.0]
修复：+l4n_lookat触发动画期间切换武器再切换回来导致其它动画停止的问题
修复：l4ngui本地化文件加载时机过早的问题，该问题由2.43版本更新带来，会导致之后autoexec被运行的阶段里设置的cl_language没有效果
新增：convar l4n_vm_inspect_mode
新增：convar l4n_vm_allow_camera_animation
修改：优化l4n_menu的UI

[2.43.1]
修改：尽量避免hudmenu的闪烁问题
修复："+l4n_player_list"的一个闪退bug
修改：convar l4n_patch_hud_scope改名为l4n_hudscope_draw_override, 默认值设置为0
修改：convar l4n_hud_scope_draw_padding_block改名为l4n_hudscope_draw_padding_block
新增：convar l4n_hudscope_draw

[2.43.0]
修改：l4n菜单里新增了NekoShaders的设置，新增的"统一lightwarp"功能可用于解决不同mod作者间光照标准不统一的问题
新增：convar mat_nekotoon_normalized_lightwarp
修改：将mat_outline_thickness_scale设置为可保存
修复：l4n_view_punch_scale的失效问题
修复：服务器浏览器本地化文本加载失败导致的l4n本地化功能失效

[2.42.1]
修复：l4nsurvivor随机分配算法在实体随机数生成前就已经生效的问题

[2.42.0]
修复：l4nsurvivor随机分配算法在玩家进入闲置时的卡顿问题
修改：转换NekoToon菜单新增了描边选项
新增：convar l4n_to_nekotoon_outline_type
移除：convar l4n_survivor_model_use_nekotoon
移除：convar l4n_to_nekotoon_allow_outline

[2.41.1] 2026-08-12
修复：l4n_view_punch_scale为零时，客户端预测导致的视角抖动
修改：优先使用cl_language来确定l4ngui的显示语言

[2.41.0]
新增：convar l4n_screen_shake_scale
新增：convar l4n_view_punch_scale
新增：convar l4n_hudmenu_offset_x, l4n_hudmenu_offset_y
修复：survivor_vpk_gen生成的addoninfo全是"(bill)"后缀的问题

[2.40.2]
移除：replace_memory_allocator配置项，目前该功能不能替换dxvk的内存分配，容易与dxvk冲突

[2.40.1]
修改：l4n_game_usage新增了mimalloc的current commit
修复：+l4n_lookat触发的动画有概率丢失event的问题
修复：+l4n_lookat播放动画期间，触发原生伸手动画时的视角卡顿

[2.40.0]
修改：移除存在缺陷的l4n_survivor_model_nodecal，此版本提供了更好更细致的方案来禁用贴花，可以在l4n菜单的实体选项里访问
新增：convar l4n_decal_allow_staticprop
新增：convar l4n_decal_allow_entity
新增：convar l4n_decal_allow_special_infected
新增：convar l4n_decal_allow_survivor
新增：convar l4n_decal_allow_common_infected
修复：launch_options里值的空格转义问题

[2.39.0]
新增：可选的咪内存分配器(mimalloc)，通过config.vdf配置来开启，能减少内存碎片
修复：+score无法显示自定义头像
修复：上个版本带来的+l4n_lookat触发问题

[2.38.0] 2026-08-03
新增：convar l4n_allow_entity_dissolve
新增：convar l4n_scripted_hud_allow
新增：15个前缀为"l4n_scripted_hud_allow_slot"的convar
修复：+l4n_lookat在手枪上的状态问题
修复：+l4n_lookat在没有extern动画的模型上不能触发loop的问题
修复：+l4n_lookat进入loop动画的衔接问题
修改：优化l4nsurvivor对bot的处理，减少触发模型加载的情况

[2.37.0]
新增：convar l4n_reshade_draw
新增：convar l4n_thirdperson_fire_sound_fix
修复："l4n_dynamic_light_muzzleflash 1"在类似ak这种射速下的闪烁问题
新增：convar l4n_player_list_vomitjar_icon_clip
移除：convar l4n_player_list_clipped_item_icons
新增：convar l4n_dlight_muzzleflash_prevent_tonemapscale
修改：将"l4n_dynamic_light_"开头的convar重命名为"l4n_dlight_"

[2.36.4] 2026-07-23
修改：config_template.vdf里提供了示例参数来解决ReShade Bridge的内存占用问题
修改：config.vdf提供了设置环境变量的参数
修复：l4nsurvivor的一些问题
修改：l4n gui的一些体验优化
新增：convar mat_neko_pre_tonemapping
修改：默认使用旧版本的渲染管线，避免新管线在部分配置下泛光和色调映射失效

[2.36.3]
修复：ReShade Bridge在某些dxvk版本下失效的问题

[2.36.2]
修改：将convar l4n_survivor_sequence_fix 改名为 l4n_survivor_sequence_strip
新增：convar l4n_thirdpersion_crosshair_dynamic
新增：convar l4n_dynamic_light_muzzleflash_brightness
新增：convar l4n_dynamic_light_muzzleflash_distance

[2.36.1]
修复：上个版本后处理流程里的一些色彩问题

[2.36.0]
修复：hud队友信息接管启用的情况下，某些脚本生成自定义bot时崩溃，例如ColdFront第三关的Mike
修改：ReShade Bridge在默认设置下会锁定Generic Depth的设置
修改：为了更好集成ReShade以及优化自动曝光的效果，对游戏的渲染流程做出了一些修改，最终的主要流程为(功能全开的情况)：3DScene(f16 hdr)->NekoBloom:Garb->ApplyTonemapCurve(ldr)->ReShade->AutoExposure->NekoEnginePost(NekoBloom:Apply)->HUD
修复：l4n_magic_converter在使用vpk自带的vgui vmt时，$basetexture路径没有被正确转换的bug

[2.35.6]
修复：ReShade Bridge不强制在进图后才启用滤镜渲染

[2.35.5]
修复：一个ReShade Bridge导致驱动程序崩溃的问题

[2.35.4]
修复：在某些配置上使用dxvk和ReShade Bridge时，驱动程序崩溃的bug

[2.35.3]
新增：nekotoon材质参数$emissionTonemapScaleAmount
修复：l4n菜单里禁用l4nsurvivor后，重新打开菜单后没有选项可以启用回来的问题
修复：禁用l4nsurvivor后，与玩家模型相关的实体没有同步的问题

[2.35.2]
修复：ReShade Bridge偶然失效的bug
修改：默认禁用ReShade Bridge

[2.35.1]
修改：优化ReShade Bridge的兼容性，如果还会遇到问题，请在ReShade的插件管理里禁用“Left For Neko”

[2.35.0]
新增：readme_l4n新增ReShade Bridge的使用说明
新增：convar l4n_server_filter
新增：convar l4n_patch_hud_scope
修复：自动曝光过于迟滞的问题
修复：l4n_magic_converter的一个转换失败bug
新增：convar l4n_thirdpersion_crosshair_scale

[2.34.1]
修复：导致reshade获取depth缓冲区闪烁的bug

[2.34.0]
修复：to_l4n_survivor生成mod不显示模型的bug
修改：l4n_survivor_sequence_fix能够截断扩充的动画，防止自己为主机时一些人物mod出现随地大小变
修改：config.vdf配置文件新增用于l4n_survivor_sequence_fix的参数
修改：l4n_survivor_sequence_fix默认值设置为0
修改：优化l4nsurvivor对幸存者死亡实体的所属玩家判定
修改：to_l4n_survivor支持单个幸存者角色mod的输入
修改：更新l4n_survivor功能的说明
修改：修复l4nsurvivor的一些小bug
修改：+l4n_player_list能够提示幸存者玩家处于黑白状态
修复：模型选项的$TextureGroup生效异常bug
移除：convar mat_nekosprite_draw
新增：convar l4n_allow_draw_sprite
新增：convar l4n_dynamic_light_muzzleflash
新增：convar l4n_thirdpersion_crosshair_alpha
新增：服务器名黑名单机制，默认规则在server_name_filter_template.txt里
修复：某些天空盒材质过亮的bug
新增：l4n_magic_converter幸存者模型转换工具
新增：l4nplugin插件系统

[2.33.3]
修复：模型选项里不显示StaticProp的模型

[2.33.2]
修复：模型选项闪退的bug

[2.33.0] 2026-06-08
修改：模型选项支持flexcontroller
修复：l4n_patch_team_player_display的一个bug
修复：模型菜单列表不会更新的bug

[2.32.0]
修改：pbr着色器支持emissiveblend
修复：nekotoon的一个渲染错误
修改：l4n_menu里新增了修改l4n_menu显示位置的选项

[2.31.0]
修改：SkyBox菜单扫描vmt时，能够忽略不合规的vmt
修复：添加-l4n_use_neko_engine_post启动项后，Refract着色器的颜色空间问题
修改：使NekoRefract的反相效果不那么刺眼
修复：l4n_patch_team_player_displayID名修改在第一次进图时失效
修复：l4n_patch_team_player_displayID名截断乱码的问题
修改：l4n_patch_team_player_display支持修改计分板头像
修改：+l4n_player_list能够显示l4nsurvivor头像
修改：l4n_patch_team_player_display增加数值2的选项
新增：convar mat_nekorefract_color_invert_exponent

[2.30.1] 2026-05-29
修复：background bik不匹配对应的mp3
修复：to_l4n_survivor无法处理使用vtf vgui的vpk
修改：启动前会检查游戏版本，不符合预期的版本会弹窗警告

[2.30.0] 2026-05-28
新增：convar l4n_allow_consistency_check
新增：convar l4n_to_nekotoon_allow_outline
修改：菜单里转nekotoon的选项旁边增加禁用描边的选项，该功能有助于避免在不合适的模型上使用描边
修改：to_l4n_survivor能够识别"s_panel*.vmt"和"*incap.vmt"
修改：增加l4n hud菜单的不透明度
修复：sv_consistency默认值不为1

[2.29.1] - 2026-05-27
修复：没有sequence_event.vdf文件的情况下，武器v模调用粒子崩溃的bug

[2.29.0] - 2026-05-27
新增：convar l4n_max_background_bik
修改：将convar mat_tonemapping_occlusion_use_stencil改为控制台可见并启用值储存
修改：RestrictAddons禁用的情况下，使sv_consistency 1的作用失效，跳过检查受限模型的着色器材质和BBox
修复：2.28版本带来的demo播放崩溃
新增：concmd l4n_reload_sequence_event_vdf
新增：v模粒子调用重定向的功能，配置文件sequence_event.vdf
新增：concmd l4n_reload_config

[2.28.1] - 2026-05-25
修改：移除convar l4n_gui_font_fallback
修改：mat_nekobloom_maptex_strength默认值降低为40
修改：RestrictAddons启用时限制部分功能

[2.28.0] - 2026-05-24
新增：convar l4n_custom_command_menu
修改：nekotoon材质在强光处可以与nekobloom产生微妙反应
新增：以v模为单位的武器自定义开镜功能
修改：mat_neko_allow_invert_tonemap默认值改为2
修改：局部对比度不在nekobloom生效处混合
新增：convar mat_nekobloom_maptex_strength
新增：convar mat_nekobloom_maptex_weight
新增：convar mat_nekobloom_blend_mode
新增：convar l4n_patch_team_player_display
新增：convar l4n_hud_scope_draw_padding_block

[2.27.0] - 2026-05-16
新增：vgui主题参数覆盖的功能，使用scheme_overrides.vdf配置文件
修改：l4n_menu里增加了给特定队友指定l4nsurvivor模型的选项
修复：l4nsurvivor的steamid分配算法在人机上不符合预期
修复：没有适配l4n的幸存者模型在转为l4nsurvivor后不支持缩放
修改：问题指南里新增了材质透明的话题
修复：outline着色器在暗处颜色过亮
新增：outline着色器参数$OutlineZOffset
新增：nekotoon着色器参数$emissionStrength
新增：concmd l4nsurvivor_roll

[2.26.0] - 2026-05-12
修改：nekotoon环境光的算法，减小明暗对比
修改：更新readme_l4n的问题指南

[2.25.1]
修改：mat_neko_allow_invert_tonemap的默认值设置为1

[2.25.0]
新增：convar l4n_allow_lobby_cheats
新增：convar mat_neko_allow_invert_tonemap
新增：convar l4n_force_dummy_addoninfo
修改：调整nekobloom的默认参数和算法

[2.24.1]
修改：更新readme_l4n的内容
修复：问题mod的判定能够应对新发现的情况

[2.24.0]
新增：convar l4n_flashlight_r/g/b
修复：l4n_flashlight_factor值超过1时导致某些材质渲染异常
修复：l4n_menu的翻页指示器显示错误
修复：config_template.vdf内sv_cheat的拼写错误
修复：使用l4nsurvivor模型的玩家闲置时，hud头像显示失效的问题

[2.23.0]
新增：config.vdf配置项"custom_commands"
新增：concmd l4n_print_particles_manifest
修复：一些配置的读取能够遵循前后顺序，提升用户使用相关功能的体验
修复：particles_manifest的修补不遵循书写顺序

[2.22.0]
修复：NekoBloom遇到负像素值时出现黑色多边形
修复：一些配置的读取能够遵循前后顺序，提升用户使用相关功能的体验
新增：convar mat_nekosprite_draw

[2.21.0]
新增：concmd l4n_reload_vgui_schemes，重载vgui，可用于替代mat_setvideomode修改分辨率触发重载的方法
新增：concmd l4n_revert_cvar，使指定的convar恢复到默认值
新增：convar mat_nekobloom_radius

[2.20.0]
修改：优化NekoBloom的算法，使效果更自然
新增：convar l4n_flashlight_factor
新增：convar mat_neko_bloom_max_brightness
修改：mat_neko_bloom_luminance_threshold默认值设置为2
修改：mat_neko_bloom_scale的单位
修改：将所有带neko_bloom字符的convar改名为nekobloom，规避scale单位修改带来的兼容性问题

[2.19.3]
修复：NekoBloom出现鬼影的bug

[2.19.2]
修改：优化NekoBloom的默认参数和性能

[2.19.1]
修改：更新版本号

[2.19.0]
新增：neko_engine_post泛光效果(NekoBloom)
新增：convar mat_neko_engine_post_after
新增：convar mat_neko_bloom_luminance_threshold
新增：convar mat_neko_bloom_scale

[2.18.1]
修改：l4n_open_shader_cache_dir能够打开NVIDIA或AMD驱动层的着色器缓存文件夹

[2.18.0]
新增：英语本地化支持 
新增：concmd l4n_is_proxy_exist
新增：材质代理"SelectFirstIfNonZero"
修复：neko_engine_post渲染胆汁效果时的控制台报错
新增：concmd l4n_open_shader_cache_dir
新增：concmd l4n_print_environment_variables
修复：不适配l4n的幸存者模型无法被切换成胆汁污渍材质
修复：l4n_allow_flashlightmuzzleflash的默认值不为1

[2.17.0]
修改：更新l4n survivor的规范，新规范增加了VGUI头像和倒地背景图片的支持（在客户端渲染显示方面，暂时不支持计分板）
修改：to_l4n_survivor.exe能够生成带VGUI头像和倒地背景图片的vpk
新增：convar l4n_allow_hud_team_player_display

[2.16.2]
修复：添加-l4n_use_neko_engine_post启动项后，实体外描边颜色空间不正确的问题

[2.16.1]
新增：启动游戏的bat脚本，如果遇到内存问题可尝试使用该脚本启动游戏
修改：使mat_neko_gamma能够保存状态

[2.16.0]
修复：neko_engine_post的负局部对比度效果异常
修改：l4n_menu新增更多控制局部对比度的选项

[2.15.0]
修改：mat_neko_gamma的单位
修改：neko_engine_post使用标准曲线进行srgb输出而非近似曲线
修复：l4n_game_usage计算datacache时溢出的bug

[2.14.1]
修复：neko_engine_post晕影和胆汁模糊效果颜色空间异常
修复：添加-use_neko_engine_post启动项后，nightvision滤镜过亮

[2.14.0]
修复：neko_engine_post晕影效果异常
修改：neko_engine_post支持局部对比度

[2.13.0]
修改：neko_engine_post着色器支持胆汁效果

[2.12.0]
修改：使色调映射在不带hdr光照数据的地图里正常工作
删除：convar l4n_force_hdr_enable

[2.11.0]
新增：convar l4n_pin_viewmodel
新增：nekotoon参数$BaseTexture2BackFace
修改：nekotoon参数$BaseTexture2Tint的w值含义
修复：Refract着色器与NekoEnginePost的兼容性问题
修复：l4n_prevent_varms_stretching与部分mod的兼容性问题
修改：启用l4n_tonemap_scale的convar值保存

[2.10.1]
新增：l4n_menu项目“禁止动画拉伸手指”

[2.10.0]
新增：l4n_menu选项“刷新实体随机数”, "模型随机缩放增量"，"NekoSky叠加纹理强度"，"允许第一人称手电筒火光"
新增：concmd l4n_refresh_entity_random
新增：convar l4n_charactor_model_random_scale 0.0
新增：convar mat_nekosky_overlay_strength 1.0
修改：convar l4n_flashlightmuzzleflash 改名为 l4n_allow_flashlightmuzzleflash
修复：Sequence代理获取的值不正确的问题
修复：lock_datacache_size不够严格的问题
新增：concmd l4n_clear_datacache

[2.9.9]
修复：模型选项切换时卡顿的问题
修改：NekoSky的叠加纹理不受曝光控制
修改：convar l4n_tonemap_scale的最低值为0.001
修复：添加-l4n_use_neko_engine_post启动项后，狙击枪开镜的颜色异常
修复：添加-l4n_use_neko_engine_post启动项后，实体外描边效果的颜色异常
新增：l4n_menu提供禁用或启用实体外描边效果的选项

[2.9.8]
修改：l4n_menu里的“设置场景暗处增亮”增加更多选项
新增：concmd l4n_fast_record
新增：l4n_menu选项“快速录制DEMO”
修改：优化检测环境反射问题的算法

[2.9.7]
修改：l4n_menu里的色调映射设置能够显示当前HDR渲染的状态
修改：添加-l4n_use_neko_engine_post启动项后，不再强制启用HDR渲染，避免某些不支持HDR渲染的地图光照出现问题
修改：l4n_tonemap_scale在HDR渲染关闭时能够生效
新增：l4n_menu选项“强制启用HDR渲染”

[2.9.6]
修复：添加-l4n_use_neko_engine_post启动项后，在某些环境反射损坏的地图里一些材质出现渲染异常
修复：添加-l4n_use_neko_engine_post启动项后，某些材质渐变效果颜色异常鲜艳
新增：convar l4nsurvivor_allow_bot 1，是否允许bot使用l4nsurvivor
移除：convar l4n_proxy_alpha_clamping
修改：不使用neko_engine_post的情况下，场景暗部增亮功能的情况使用另外的预设参数

[2.9.5]
新增：convar l4n_player_list_clipped_item_icons 1, +l4n_player_list在渲染物品图标时使用游戏默认的裁切比例; 某些hud mod会有自定义的比例，设置为0或许能正确渲染
新增：+l4n_player_list的玩家语音指示

[2.9.4]
修改：l4n_menu新增地图暗部增亮的设置
修复：添加-l4n_use_neko_engine_post启动项后，新增法线贴图的地图材质在渲染时光照异常全亮
新增：convar l4n_ambient_darkness_limit 0.0
新增：convar l4n_lightmap_darkness_limit 0.0
修改：移除neko_engine_post着色器的胆汁效果

[2.9.3]
修复：添加-l4n_use_neko_engine_post启动项后，地图远景雾效渲染异常
修改：neko_engine_post着色器支持了基础的胆汁模糊效果

[2.9.2]
修复：添加-l4n_use_neko_engine_post启动项后，游戏画面闪烁的bug
修改：移除convar mat_nekotoon_allow_flat_bumpmap
新增：convar mat_nekotoon_ignore_flat_normal 1

[2.9.1]
修复：添加-l4n_use_neko_engine_post启动项后，地图远景雾效渲染异常
修改：convar l4n_use_nekosky的默认值变更为1 

[2.9.0]
新增：材质代理Sequence
修改：材质代理Cycle新增参数layer
修复：NekoToon无法正确解析ATI2N法线
新增：convar l4n_proxy 1

[2.8.8]
修复：添加-l4n_use_neko_engine_post启动项时，地图光斑效果的颜色空间异常
修复：nekosky着色器的贴图叠加效果不受曝光影响

[2.8.7]
新增：convar mat_nekotoon_rimlight_viewmodel_boost, mat_nekotoon_lambert_factor
修复：$rimlightViewModelFactor失效的bug
新增：nekotoon着色器参数$rimlightExponent, $rimlightAlbedoTint, $lambertFactor
移除：nekotoon着色器参数$flashLightLambertRange

[2.8.6]
新增：convar l4n_use_nekosky 0，是否使用l4n的NekoSky着色器来渲染天空
新增：六个"mat_nekosky_overlay_"开头，后缀是rt/bk/lf/ft/up/dn的convar，用于设置贴图路径作为NekoSky天空盒某个面的叠加纹理
修复：+l4n_player_list不显示bot的本地化翻译名
新增：pbr着色器参数$BaseTexture2Tint
新增：nekotoon着色器参数$BaseTexture2，$Frame2，$BaseTexture2Tint

[2.8.5]
新增：配置文件localize_overrides.vdf，用于覆盖本地化翻译文本，附带了修改幸存者名称的示例
新增：convar l4n_proxy_alpha_clamping 1，是否禁止材质代理将$alpha的值修改为负数，防止颜色混合异常
修复：添加启动项-l4n_use_neko_engine_post后某些材质颜色出现异常
新增：nekotoon材质参数$MatcapUV
修改：提高l4n着色器获取材质参数的效率

[2.8.4]
修改：l4n菜单里新增地图环境反射的修复教程
新增：convar l4n_player_identity_render_color 0 是否禁止玩家相关实体的染色
新增：配置文件key_bind_acts配置项，用于扩充游戏设置里按键绑定的选项
修复：未适配l4n的幸存者mod无法调整缩放，此bug出现于上个版本
新增：concmd l4n_cvar
新增：concmd l4n_buildcubemaps
新增：convar l4n_env_cubemap_redirect 0
修复：添加启动项-l4n_use_neko_engine_post后某些服务器无法进入的问题

[2.8.3]
修复：convar mat_neko_force_lineay_tonemapping失效的bug，并改名为mat_neko_tonemapping_force_linear
修复：l4n_nekook_path_append和l4n_nekook_path_remove 接受参数的字符编码bug
修改：提高to_l4n_survivor生成结果的兼容性
修复：nekotoon环境光过亮的问题

[2.8.2]
修复：nekotoon手电筒效果失效的bug

[2.8.1]
修复：着色器导致DXVK占用大量内存的BUG
修改：移除FXAA功能

[2.8.0]
修改：l4n_menu模型设置菜单里新增了一些选项和信息
修改：NekoEnginePost着色器新增AgX色调映射
修改：NekoEnginePost着色器新增FXAA抗锯齿技术
新增：convar mat_nekotoon_allow_lightwarp 1
修复：本地mod元数据修复失败的bug
修复：一个pcf粒子扩充失败的bug
修复：描边着色器的一个Z-fighting问题
新增：concmd l4n_nekook_path_append,  添加一个高优先级资产搜索路径，比VPK内的文件优先级高
新增：concmd l4n_nekook_path_remove,  移除一个高优先级搜索路径

[2.7.7]
新增：模型组件菜单里重置的选项
修复：添加-no_l4n_gui后无法进入地图的bug
修改：增加l4nsurvivor在遇到某些版本编译器生成的模型时的兼容性

[2.7.6]
新增：convar mat_neko_gamma 2.2，和视频设置里亮度一样的效果，但是可以在非独占全屏时生效，需要启动项-l4n_use_neko_engine_post
修改：l4n_menu新增gamma调整的选项
新增：nekotoon参数$rimlightViewModelFactor

[2.7.5]
修改：nekotoon着色器新增$NoFlexNormal参数
新增：convar l4n_vm_sway_ignore_helpinghand 1，是否在触发伸手动画时禁用sway效果，启用后可能会导致一些插件的动画(如ADS)没有sway效果，禁用后可能会导致武器高频抖动
修复：一个导致字体渲染错乱的bug
修改：启动项里存在-l4n_use_neko_engine_post时，l4n_tonemap_scale的默认值设置为1.8

[2.7.4]
修复：+l4n_player_list的渲染闪烁

[2.7.3]
修改：将convar l4n_gui_font_fallback的默认值设置为1
修复：PBR着色器的flex无效
修改：主菜单新增了一些选项
修改：+l4n_player_list的渲染

[2.7.2]
修改：l4n_menu新增了许多快捷选项
修改：nekotoon的实体染色使用HSV的色调
修改：+l4n_lookat默认在物品或倒地队友伸手动画之间随机播放，新增了参数用于指定这两种动画
新增：concmd l4n_to_nekotoon
新增：convar l4n_mat_specular 1
新增：convar l4n_gui_font_fallback 0, 是否补足字体不支持的字符(目前只影响+l4n_player_list)，启用会加载更多字体增加内存占用

[2.7.1]
修改：mat_neko_tonemapping_algorithm 默认值设置为6
修改：neko_engine_post新增了三个tonemapping算法(6:Neutral/7:NAES/8:LOG2)
修改：nekotoon在某些tonemapping效果启用时增加饱和度，防止饱和度丢失过多

[2.7.0]
新增：convar mat_neko_tonemapping_algorithm 2，neko_engine_post着色器的tonemapping算法(0:Linear(起源)/1:Reinhard/2:Uncharted2(神秘海域2)/3:CE/4:ACES(UE4默认)/5:GranTurismo)，需添加-l4n_use_neko_engine_post启动项才能使用
新增：启动项"-l4n_use_neko_engine_post"，添加该启动项将使用neko_engine_post替代引擎的engine_post着色器

[2.6.6]
修改：使玩家实体的一些子级能够同步l4nsurvivor模型
修改：+l4n_player显示服务器名称和玩家数量
修改：convar l4n_flush_unused_model更名为l4n_auto_flush_unused_models
新增：concmd l4n_flush_unused_models
修改：concmd l4n_placelight 新增了三个参数

[2.6.5]
修复：NekoToon和Outline的$alpha不生效
修复：着色器在hlmv截图时的渲染错误

[2.6.4]
修改：convar l4n_enhanced_material_pxory 默认值为0
新增：convar l4n_disable_survivor_bandage 1，是否禁用生还者模型的绷带粒子，默认禁用是因为调整身高的功能会和原版绷带粒子冲突
添加：+l4n_player_list的玩家人数显示
修复：游戏启动第一次进图时pbr着色器的渲染错误

[2.6.3]
修改：禁用Shader Model 3.0的检测
修改：convar l4nsurvivor新增参数2，此参数将不替换队友模型
修复：pbr着色器启用描边时出现闪退

[2.6.2]
新增：outline着色器vmt参数"$OutlineHSV"和"$OutlineBaseTextureBlend"
新增：convar l4n_force_skyname
新增：l4n_menu里的SkyBox切换菜单

[2.6.1]
移除：Entity proxy的检测弹窗

[2.6.0]
修改：NekoToon的MatCap效果能够被$LightingScale影响(破坏性更新)
新增：pbr着色器支持双材质动态混合
新增：pbr和nekotoond的$hsv参数，通过色相饱和度亮度修改贴图颜色
新增：pbr和nekotoon的许多新特性，参数过多请前往pbr.vmt和nekotoon.vmt里查看
修改：nekotoon的$emission支持遮罩模式
新增：nekotoon材质参数$multiply，可用于实现刘海假阴影
新增：nekotoon材质参数$eyebrow，用于实现眉透
新增：nekotoon支持染色蒙版
新增：nekotoon材质参数$LightWarpExponent，可用于调整阴影的强度
新增：nekotoon材质参数$FakeShadow
新增：材质代理Cycle，用于获取模型动画进度
新增：l4n特有的材质代理PlayerAttachment和PlayerBottom
新增：材质代理RemapValClamp和Modulo，用于简化一些繁杂的数学运算
新增：convar l4n_engine_post_allow_local_contrast 1，是否允许使用一种类似锐化的滤镜效果(肾上腺素或低血量或boomer胆汁消失时出现)
新增：convar l4n_survivor_scale 1.0, 全局设置幸存者的模型大小
新增：convar l4n_enhanced_material_pxory 0，是否增强部分材质代理，如EntityRandom会同步第一人称和第三人称的随机数种子
新增：convar l4n_proxy_entity_random_seed_offset 0.0，EntityRandom的随机数种子偏移
修改：由于"l4n_player_lighting_scale"和"l4n_player_stylized_amibentlight"对特感的支持不够充分，已移除对非幸存者实体的支持，并且改名为"l4n_survivor_lighting_scale"和"l4n_survivor_stylized_amibentlight"
修复：PBR着色器的一个手电筒渲染bug
修改：PBR、NekoToon、Outline着色器的性能优化
修改：删除PBR的$Emission参数
修改：改进NekoToon的RimLight渲染，使其表现得更自然
新增：convar mat_nekotoon_allow_flat_bumpmap

[2.5.0]
修复：l4n_tonemap_scale一个在部分地图上的失效bug
修改：伸手动画播放时禁用4n_vm_sway_

[2.4.9]
修复：l4n_vm_selfillum不会忽略有光照的$DetailBlendMode
修改：更新readme_l4n.txt的一些说明
修改：l4n_survivor_model_use_nekotoon新增参数2，参数2转换后的材质不会启用描边

[2.4.8]
修改：给垃圾模型回收添加一段缓冲时间
修复：dxvk调试层意外显示

[2.4.7]
修改：OutOfMemory弹窗新增对dxvk的检测

[2.4.6]
修复：scheme替换Tahoma字体导致+l4n_player_list的字体错误
新增：启动项“-hide_addons”，用于临时禁用所有addons目录下的mod
新增：nekotoon材质参数"$DarknessLimit"

[2.4.5]
修复：+l4n_player_list在部分系统上的字体丢失
修改：+l4n_player_list添加普感击杀计数
新增：concmd l4n_env_report

[2.4.4]
修改：除非修改配置项，默认将datacache的限制强制设置为2048MB
修复：在更早的时机加载模型配置，防止l4n_vm_2pbr的配置在某些情况下失效
修复：引擎无法正常清空console.log文件
新增：concmd l4n_reset_player_render_color

[2.4.3]
新增：配置文件"disable_chromehtml"参数，用于禁用引擎内置的浏览器内核，可以减少100mb左右的内存占用
新增：convar l4n_flush_unused_model 1
修改：convar l4n_survivor更名为l4nsurvivor
修改：convar l4n_survivor_allocation_algorithm更名为l4nsurvivor_allocation_algorithm

[2.4.2]
修复：一个崩溃问题，受该问题影响的有l4n_vm_2pbr、l4n_vm_selfillum、l4n_survivor_model_use_nekotoon
新增：concmd l4n_print_launch_options，输出当前能被游戏识别的启动项

[2.4.1]
修改：设置l4n_survivor_sequence_fix 默认值为1
修改：设置l4n_player_list_show_steam_avatar 默认值为1
修改：+l4n_player_list的血条显示

[2.4.0]
新增：concmd l4n_vm_2pbr，尝试将当前v模的材质转换为PBR材质；参数0还原材质
修复：l4n_vm_offset2在没使用过该命令的v模上无效果的bug
修改：l4n_vm_offset2新增reset参数，用于归零xyz
新增：convar l4n_player_list_show_steam_avatar 1
新增：convar mat_pbr_where 0

[2.3.3]
修改：nekotoon的手电筒渲染支持亮度限制
修改：Outline着色器完全支持水渲染

[2.3.2]
修改：mdl适配文档里新增了用于vta的眼球追踪示例
修改：nekotoon AOMap的算法
修复：nekotoon和pbr获取错误的水面高度

[2.3.1]
修复：mat_nekotoon_lazy_texture_load关闭时贴图错误

[2.3.0]
新增：nekotoon材质参数："$bumpstrength"、"$bumpmap2"、"$bumpstrength2"、"$bumptransform2"
新增：nekotoon AOMap支持，使用$mask1的a通道
修复：nekotoon和pbr着色器的水下渲染问题
移除：nekotoon和pbr的材质参数$dxt5nm
新增：convar mat_nekotoon_lazy_texture_load 0
新增：convar l4n_game_usage_padding 24
新增：concmd l4n_mat_showtextures

[2.2.8]
修复：第一次使用l4n的用户，模型配置无法正常保存

[2.2.7]
修改：优化幸存者死亡实体的所属玩家的判定，有助于l4n_survivor生效时赋予正确的模型
修改：readme_l4n的排版
修改：优化config_template里的注释说明
新增：convar l4n_survivor_allocation_algorithm 1，用于设置l4n_survivor给队友分配模型的算法

[2.2.6]
修改：优化了+l4n_player_list的文字渲染，当前字体不支持该字符时，将自动用其它支持该字符的字体来渲染
修复：+l4n_player_list部分条目的字符渲染截断

[2.2.5]
移除：自带的思源黑字体文件
修改：配置添加字体文件路径的参数

[2.2.4]
新增：convar l4n_menu_font_size
新增：modder工具nekook和nekomdl
修改：l4n_vm_selfillum支持正负号，此时数值代表增量
修改：优化l4n_survivor的模型内存释放机制
修改：l4n_menu的交互
修改：nektoon支持$decal

[2.2.3]
修复：l4n_vm_selfillum 在过图后导致自发光变得更亮

[2.2.2]
新增：concmd l4n_vm_selfillum 1，调整当前第一人称武器的自发光强度
新增：nekotoon参数"$flashlightlambertrange"
修复：nekotoon $flipbackfacenormal的过渡bug

[2.2.1]
新增：convar l4n_force_hdr_enable 0，是否强制启用HDR渲染，在不支持HDR渲染的地图上可能导致部分模型光照出现问题
修复：l4n_tonemap_scale在一些支持HDR渲染的地图上无作用
新增：convar l4n_prevent_varms_stretching 0

[2.2.0]
新增：形态键眼追功能

[2.1.9]
修复：上个版本带来的部分模型组件切换失效bug

[2.1.8]
修复：nekotoon的$lightingscale无效
修改：新算法使受mat_nekotoon_brightness_limit限制的像素更自然
修改：+l4n_player_list在双击时显示游戏计分板
移除：convar mat_nekotoon_min_ambient_luminance
添加：convar mat_nekotoon_darkness_limit
修复：nekotoon $emission的颜色不准确

[2.1.7]
新增：concmd l4n_vm_offset2
移除：convar l4n_vm_offset2_x, l4n_vm_offset2_y, l4n_vm_offset2_z
修复：skin切换在某些实体上失效的bug

[2.1.6]
新增：convar mat_nekotoon_brightness_limit 1.0, 控制nekotoon渲染结果的最大亮度，避免过曝
新增：nekotoon材质参数$flipbackfacenormal 1, 是否修正背面的法向(可以让背面被手电筒照亮)

[2.1.5]
修改：nekotoon rimlight的可视方向和其它参数，使其看起来更自然
新增：convar mat_nekotoon_rimlight_boost 4，进一步调整nekotoon里$rimlightboost的强度

[2.1.4]
新增：convar l4n_survivor_sequence_fix 1，是否修复幸存者动画的潜在问题，修改后需重启
新增：concmd l4n_survivor_sequence_test，检查幸存者动画有无问题，一般是和动画mod有关
修复：着色器里$basetexturetransform的translate无效的问题
修复：描边着色器和某些v模武器一起时出现渲染错误
修改：屏幕空间描边添加一点距离的影响
修改：nekotoon的$rimlight能够被$lightingscale影响
新增：convar mat_outline_thickness_scale 1，控制描边着色器的描边粗细

[2.1.3]
修复：强制使幸存者v模和w模匹配功能失效的bug
修改：l4n_menu的布局
新增：convar l4n_menu_offset_x 和 l4n_menu_offset_y
新增：nekotoon的材质参数$rimlight和$rimlightboost
修改：nekotoon在$nocull开启时，将自动修正背面的法向，防止光照方向变反(手电筒下的光照不亮)

[2.1.2]
修复：模型组件配置概率丢失的bug
修复：l4n_player_list的闪退bug

[2.1.1]
修复：l4n_survivor_model_use_nekotoon部分材质变白
修复：部分模型的组件切换失效的问题
修复：l4n_survivor第一人称腿不同步的bug

[2.1.0]
修复：l4n_survivor_model_use_nekotoon将材质转换到NekoToon材质时，一些透明有关的参数值没有复制的bug
修改：文档里l4n_survivor_model_use_nekotoon的描述（修改后需重启游戏；部分材质转换后的效果可能比不上作者主动适配，尤其是部分模型的脸部）

[2.0.9]
修复：l4n_survivor_model_use_nekotoon在有些材质上贴图变成纯白

[2.0.8]
修复：未进入地图时运行l4n_tonemapping_scale闪退
新增：convar l4n_survivor_model_nodecal，是否禁用幸存者模型的贴花效果（血迹），修改后需重启游戏
新增：convar l4n_survivor_model_use_nekotoon，是否将幸存者模型材质里合适的着色器替换为NekoToon，修改后需重启游戏
修复：客户端预测播放了空数据的手势动画导致闪退（使用xdReanimsBase时可能会遇到这种bug，这种动画的索引是超出服务器索引范围的，不应该被播放；目前的修复不能保证服务器索引范围内的不被播放，服务器索引范围内的也不应该有空动画数据；因为有些客户端预测是通过sequence名称来匹配的，空数据sequence是不会有Activity信息的，此修复只是修改了这些空数据sequence的名字）
修改：崩溃后准备生成mdmp前检查内存占用，有异常将弹出报告

[2.0.7]
添加：convar l4n_game_usage，控制hud显示和游戏稳定性有关的数据
添加：convar l4n_game_usage_pos，控制l4n_game_usage显示的位置
添加：接管mdmp的生成，用于修复某些崩溃不生成mdmp
添加：堆内存申请失败的弹窗
修改：config_template.vdf内有关闪退的说明
修改：优化l4n_survivor对尸体所属玩家的判定

[2.0.6]
添加：datacache内存占用的hud指示器
修复：l4n_menu在切换游戏分辨率后的渲染失效

[2.0.5]
添加：cvar l4n_tonemap_scale, 控制地图hdr的曝光强度
修改：移除配置文件参数lighting_factor_spot, lighting_factor_point, lighting_factor_directional, stylized_amibent_light
添加：convar l4n_player_lighting_scale, 控制玩家模型的光照强度
添加：convar l4n_player_stylized_amibentlight，玩家模型使用风格化环境光的开关

[2.0.4]
修改：+l4n_lookat运行期间，禁用l4n_sway_防止有些武器动画运动摄像机导致抽搐
修复：+l4n_lookat在有些武器上动画时长不正确

[2.0.3]
修复：+l4n_player_list绑定到某些按键上会判定出参数1
修改：配置文件添加参数"wave_cache_max_kilobytes"
修改：安装包附带了资源管理器显示vpk文件略缩图和mod标题信息的插件

[2.0.2]
修改：尝试修复l4n_vm_sway_的动画抽搐问题

[2.0.1]
修改：修改WaveDataCache的内存上限到512mb
修改：默认禁用更新玩家模型后重建武器的bonemergecache

[2.0.0]
修改：战术性调整datacache里WaveData的内存限制
修复：使用l4n_survivor时可能导致的一个闪退bug
修复：legs实体的识别错误导致看到别的玩家身上有两个模型

[1.9.9]
修复：snd_rebuildaudiocache重建音频缓存时闪退
修改：+l4n_lookat时能够推人打断
修改：增加nekotoon补光的亮度
修改：nekotoon $emission启用时不禁用补光
添加：cvar mat_nekotoon_min_ambient_luminance
修改：尝试修复一个导致闪退的bug
修改：尝试修复l4n_vm_sway联机时可能出现的动画卡顿

[1.9.8]
修复：+l4n_lookat双击的动画不会结束
修改：配置文件的一些注释，还有font的默认值

[1.9.7]
修复：在某些服务器上l4n_vm_sway的动画效果卡顿
修复：+l4n_lookat无法打断动画的bug

[1.9.6]
修复：l4n_commoninfected_noragdoll的含义相反

[1.9.5]
修改：解锁-heapsize的512mb上限，更多信息在config_template.vdf里

[1.9.4]
添加：cvar l4n_vm_offset2_x，l4n_vm_offset2_y，l4n_vm_offset2_z；用于单独为第一人称武器模型调整位置偏移
添加：配置文件参数"min_tall"，用于控制字体的最小尺寸
修复：+l4n_lookat在切换武器后不打断的bug，以及动画衔接过快的bug
修改：添加cvar“l4n_commoninfected_noragdoll”，移除配置文件参数“no_common_infected_ragdoll”
修改：添加cvar“l4n_mat_colorcorrection”，移除配置文件参数“no_color_correction”
修改：更新readme_l4n.txt文档
新增：+l4n_player_list的输入参数支持，添加参数1时双击才显示，单击则显示原版计分板
修复：l4n_survivor的第一次切换无效的问题
修复：l4n_survivor给联机队友切换模型时可能的手持武器错位
修复：cvar“l4n_survivor”设置为零时不更新Lux's Survivor Legs的实体模型
添加：build_sound_cache.bat, 用于快速生成sound.cache

[1.9.3]
添加：l4n_survivor对Lux's Survivor Legs的兼容
添加：command +l4n_player_list；显示更多玩家信息
修改：显示更多玩家信息的面板不再通过双击tab显示，请使用控制台命令+l4n_player_list绑定按键的方案
修改：readme_l4n.txt的一些描述

[1.9.2]
修改：发布版启用调试信息，方便bug追踪

[1.9.1]
修复：nekotton着色器matcap的渲染错误

[1.9.0]
新增：cvar l4n_vm_sway_interp, l4n_vm_sway_scale; 用于控制第一人称模型随视角转动滞后效果
新增：cvar l4n_vm_offset_y, l4n_vm_offset_z, l4n_vm_offset_x; 用于控制第一人称模型位置偏移
修改：更新本文档，以减少不必要的困扰
新增：NekoToon着色器参数 $MATCAP2, $MATCAP2TEXTURE, $MATCAP2TINT, $MATCAP2LIGHTING
修改：l4n_survivor切换的性能优化

[1.8.8]
修复：PBR着色器的BRDFLUT颜色空间问题，导致高粗糙度的计算结果错误

[1.8.7]
修复：+l4n_lookat在一些武器上不会触发的问题

[1.8.6]
修复：可能启动闪退的一个bug，对于上个版本遇到该问题的用户，在配置文件里把force_bind_l4n_menu设置为零可规避

[1.8.5]
修复：+l4n_lookat在没有对应序列的模型上闪退
修复：l4n_survivor不更新手模的状态bug
修复：模型组件菜单失效的bug

[1.8.4]
添加：cvar +l4n_lookat，触发物品伸手动画; bind按键后支持长按loop，单击相比双击多了前摇和后摇动画; 快速绑定："bind v +l4n_lookat"
修复：游戏过程中切换l4n_survivor导致的第三人称手持武器错位
添加：nekotoon着色器参数$lightwarpsrgbtexture, $lightwarphalf, $lightwarpscale, $lightwarpmapoffset
修改：nekotoon着色器支持通过$mask1蒙版在一个材质里使用多条lightwarp
移除：配置文件项"random_si_model"
添加：cvar l4n_specialinfected_randommodel, l4n_survivor

[1.8.2]
新增：cli工具用于复制wav语音的口型数据或生成sound.cache，位于"bin/neko/source_nekomimi.exe"
新增：bat脚本用于快速给语音mod复制口型数据，位于"bin/neko/copy_sentence.bat"
修复：文档里"srcipts"的拼写错误，正确的拼写是"scripts"

[1.8.1]
修改：能够完整移除第一人称枪口手电筒火光(联机有效)，使用控制台命令"l4n_flashlightmuzzleflash"来启用或关闭
修改：移除配置文件参数“viewmodel_muzzle_flash”
添加：ConVar"l4n_game_hud_visible"，用于控制游戏HUD的显示与隐藏

[1.8.0]
添加：粒子系统额外加载pcf文件的支持

[1.7.9]
添加：自动更新，需要在创意工坊里订阅L4N后才能生效

[1.7.8]
NekoShaders|新增：vmt参数$outlinefixedthickness，用于启用或禁用描边粗细修正
NekoShaders|新增：PBR着色器的Flex支持
NekoShaders|新增：$matcap两个混合模式，vmt参数"$matcaplighting"
NekoShaders|修复：$emissionflashlighttint强制白色的bug
NekoShaders|新增：NekoToon摄像机AO
新增：控制台命令l4n_placelight, l4n_menu
修改：主菜单L4N Survivor设置的逻辑
新增：addoon vpk声音脚本加载的支持

[1.7.7]
NekoShaders|修复："$emissionflashlighttint"默认启用的bug

[1.7.6]
NekoShaders|新增：用于pbr和nekotoon的vmt参数"$emissionflashlighttint"

[1.7.5]
NekoShaders|优化：描边着色器的z-fighting问题

[1.7.4]
新增：两个材质代理ClipAmmo和RemainingAmmo，用于获取弹药和备用弹药的数量

[1.7.3]
NekoShaders|修复：控制台exit/quit命令导致游戏闪退
NekoShaders|修改：$outlinetexture的格式为ATI1N时，使用r通道作为蒙版
NekoShaders|修改：描边宽度不受透视影响

[1.7.2]
NekoShaders|修复：PBR着色器在地图Brush上光照亮度过低
NekoShaders|添加：数显着色器
NekoShaders|修复：$outlinetexture 控制台报错

[1.7.1]
修改：index_buffer_size的默认值为32768
修改：文档的描述

[1.7.0]
NekoShaders|修改： 描边着色器使用更自然的光照
NekoShaders|修复：第一人称启用了描边的手模导致武器背面剔除出现问题
NekoShaders|修复：nekotoon添加新的参数$lightingscale
NekoShaders|修复：手电筒下的AlphaTest渲染错误

[1.6.9]
修复: 1.6.7出现的tab菜单失效
修改: config.vdf参数的默认值
修复: 增加与其它补丁类的兼容性
NekoShaders|修复: PBR材质开启自发光时控制台报错

[1.6.8]
NekoShaders|修复：NekoToon上个版本出现的光照变黑bug

[1.6.7]
修复：输入法导致的平台相关的按键无响应
NekoShaders|修复：PBR高粗糙度下envmap不够模糊的问题
NekoShaders|修改：PBRShader使用BRDF LUT

[1.6.6]
修复：[1.6.5]版本index_buffer_size失效的问题

[1.6.5]
NekoShaders|添加：DXT5nm和ATI2N法线贴图压缩格式的支持
NekoShaders|修改：视差贴图不再使用法线贴图的a通道

[1.6.4]
NekoShaders|添加：nekotoon的眼追支持
NekoShaders|添加：$outlinelighting参数
NekoShaders|修复：描边着色器在$nocull下的问题
恢复：stylized_amibent_light,lighting_factor_directional,lighting_factor_point,lighting_factor_spot相关的功能
添加：VERTEX_BUFFER_SIZE的修改

[1.6.3]
NekoShaders|修复：NekoToon在HLMV里的一个闪退bug

[1.6.1]
NekoShaders|添加：matcap蒙版
NekoShaders|修复：outline着色器在$nocull启用时的渲染错误
移除：receive_flashlight,stylized_amibent_light,lighting_factor_directional,lighting_factor_point,lighting_factor_spot相关的功能

[1.6.0]
新增：NekoToon着色器，相关参数在nekotoon.vmt文件里

[1.5.3]
新增: pbr着色器参数$emission，用于控制自发光的开启
修改: pbr着色器自发光默认使用$basetextur的颜色
新增: pbr着色器参数$emissiontint，用于控制自发光的强度

[1.5.2]
移除neko着色器对l4n平台的依赖，便于单独安装neko着色器，也有利于着色器被hlmv&hammer等工具加载

[1.5.0]
添加：添加次时代游戏都有的PBR着色器，参数都在pbr.vmt里

[1.4.0]
修复：部分未适配的人物mod无法修改身高的问题
添加：不要把我看扁了

[1.3.9]
给未适配平台的人物mod添加身高调整的支持

[1.3.8]
改进队友的l4n_survivor模型分配
更新自带的字体为思源黑体，减少字体渲染出现？？？的情况

[1.3.7]
禁用绷带特效，防止自定义身高的玩家模型打包时绷带炸顶点花屏

[1.3.6]
死亦瞑目
对于不适用模型缩放的模型，组件菜单将不显示调整缩放的入口
调整模型缩放菜单的预设值
支持mod作者设置默认的缩放

[1.3.5]
config.vdf: 添加“random_si_model”配置项

[1.3.4]
修复多人联机中新计分板虚血进度的计算错误

[1.3.3]
修复一个足ik修正失效的bug

[1.3.2]
修复组件菜单的一个闪退bug
l4n survivor：修复处于闲置状态时，无法及时同步切换模型
l4n survivor: 修复闲置状态阵亡时，所属玩家判定不正确

[1.3.1]
及时保存模型skin的配置
幸存者死亡实体支持缩放
l4n survivor：修复闲置玩家模型替换不正确

[1.3.0]
主菜单部分项目支持状态存储
l4n survivor: 支持无真实玩家托管的bot
l4n survivor: 尝试优化幸存者尸体所属玩家的判定
l4n survivor: 主菜单添加全局的模型切换

[1.2.7]
如果模型配置了$TextureGroup，组件菜单里会提供材质预设的切换。

[1.2.5]
修复组件菜单闪退的问题
一些小bug

[1.2.3]
优化缩放模型的算法
控制缩放数值的上下限

[1.2.2]
修复脚IK高度修正在无缩放时失效的问题

[1.2.1]
修复脚IK高度修正失效的问题

[1.2.0]
添加模型缩放功能
组件配置文件重构，之前保存的配置将会丢失

[1.1.0]
添加足IK优化的MDL扩展
添加面向MOD作者的示例qc

[1.0.2]
大幅缩小动态环境光源的照射范围，防止起源引擎在渲染不擅长的露天场景时fps骤降

[1.0.1]
主菜单添加禁用动态环境光源的选项
自带计分板所需的字体文件

[1.0.0]
新的双击TAB计分板UI

[0.9.1]
瞄准可交互物品时，不会更新动态环境光源
修复上个版本带来的一个闪退bug
尝试优化幸存者尸体所属玩家的判定


[0.9.0]
按E键可以生成动态环境光源
强制所有特感模型上班
更多玩家的面板改成双击TAB键显示
显示玩家面板时，隐藏聊天列表
rebuild_sound_cache_for_addons.bat，完成后自动退出

[0.8.1]
修复进一些图时闪退，这是上个版本带来的bug

[0.8.0]
tab键显示更多玩家信息的面板，双击tab键显示原来的面板

[0.7.0]
破坏性更新，之前的l4n survivor mod需要重新转换或适配
为防止路径过长导致引擎不稳定，l4n survivor模型的根目录改为"models/l4n/s"。
切换l4n survivor的时候，如果之前使用过的模型没有引用，将自动释放内存占用，以减少爆内存闪退的概率

[0.5.0]
添加主菜单，菜单支持翻页
[0.4.1]
l4n_survivor: 修复一个导致控制台一直报错的bug
[0.4.0]
调整风格化环境光的参数
to_l4n_survivor: 修复某些mod出现人物透明的问题
[0.3.9]
更新config.vdf的默认值
[0.3.8]
更新to_l4n_survivor.exe
[0.3.7]
添加配置项：generate_addoninfo
[0.3.6]
修复l4n_survivor第三人称手握武器出现错位