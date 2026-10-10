// 适配l4n的一些qc命令示例，请灵活变通

$Attachment "l4n_inspect" "定义武器的l4n_vm_inspect_mode原点" 0 0 0 rotate 0 0 0

$NekoModel "Head" {
    studio "my_head_model.gltf"
    // .......
    // $Attachment "eyes" 是眼球中心，不合理的位置会导致追踪不准确
    flex "eye_look_up" // 对应gltf文件里四个方向的形态键名称
    flex "eye_look_down"
    flex "eye_look_左"
    flex "eye_look_right"
    // 新增的flexcontroller需要添加到已有的底部，避免破坏原有的排序导致表情联机同步问题
    flexcontroller eyes range -1 1 l4neyes_updown
    flexcontroller eyes range -1 1 l4neyes_rightleft
    "%eye_look_up" = max(-l4neyes_updown, 0) // flex与flexcontroller绑定
    "%eye_look_down" = max(l4neyes_updown, 0)
    "%eye_look_right" = max(-l4neyes_rightleft, 0)
    "%eye_look_左"      = max(l4neyes_rightleft, 0)

    // l4n的模型选项会显示分组名为l4n的控制器
    flex "my_flex1"
    flexcontroller l4n range 0 1 "形态键控制器1"
    "%my_flex1" = "形态键控制器1"

    flex "my_flex2"
    flexcontroller l4n range 0 1 "形态键控制器2"
    "%my_flex2" = "形态键控制器2"
}

$Model "Head" "my_head_model.smd" {
    // ...
    flexfile "my_head_model.vta" {
        defaultflex frame 0
        // .....
        flex "eye_look_up"      frame 41 // 匹配形态键在vta里的位置
        flex "eye_look_down"    frame 42
        flex "eye_look_left"    frame 43
        flex "eye_look_right"   frame 44

        flex "my_flex1"         frame 45
        flex "my_flex2"         frame 46
    }
    // .....
    flexcontroller eyes range -1 1 l4neyes_updown
    flexcontroller eyes range -1 1 l4neyes_rightleft
    "%eye_look_up"    = max(-l4neyes_updown, 0)
    "%eye_look_down"  = max(l4neyes_updown, 0)
    "%eye_look_right" = max(-l4neyes_rightleft, 0)
    "%eye_look_left"  = max(l4neyes_rightleft, 0)


    flexcontroller l4n range 0 1 "形态键控制器1"
    "%my_flex1" = "形态键控制器1"

    flexcontroller l4n range 0 1 "形态键控制器2"
    "%my_flex2" = "形态键控制器2"
}

// 因为引擎的局限，所有BodyGroup选项的排列组合情况不能超过2147483647
// $Model/$Body/$NekoModel是$BodyGroup的不同写法

$BodyGroup "鞋子" {
    studio "高跟鞋.smd"
    blank
}

// 超过两个需要带⭐前缀，这样设计是为了防止静态表情被意外接管
$BodyGroup "⭐服装" {
    studio "衣服1.smd"
    studio "衣服2.glb"
    studio "衣服3.gltf"
    blank
    studio "衣服4.fbx"
}


$KeyValues // MDL备注信息
{
    "left4neko" {
        "name" "mdl的用户友好型名称，请务必提供此配置"
        "name_suffix" "弗兰嘻嘻"
        "player_foot" {
            "body_group" "鞋子"
            "0" "0.0,0.0"
            "1" "-2.1,-60.0"
        }
        // 默认缩放，仅支持角色模型
        "scale" "0.5"   // (将自定义模型缩放到接近动画骨骼的大小，再通过此功能来缩小模型可以获得更好的动画效果)
    }
}


$TextureGroup "材质预设"
{ 
	{ "Body"        "Face"          } 
	{ "skin1\Body"  "skin1\Face"    }
    { "Body2"       "Face2"         }
    { ..... }
}
// 1: Body.vmt -> Body.vmt          Face.vmt -> Face.vmt
// 2: Body.vmt -> skin1\Body.vmt    Face.vmt -> skin1\Face.vmt
// 3: Body.vmt -> Body2.vmt         Face.vmt -> Face2.vmt

// 需要使用nekomdl才能支持多$TextureGroup
$TextureGroup "衣服颜色" {...}
$TextureGroup "头发颜色" {...}


$Sequence "item_extend" {
    // ....
    keyvalues { // Sequence备注信息
        "l4n_lookat" { // +l4n_lookat的提示信息
            // 可通过删除"_RETRACT_LAYER"和"_EXTEND_LAYER"activity来达到只播放LOOP_LAYER的目的
            // 只有LOOP_LAYER的情况下可以添加以下信息来标记循环区间，这样可以避免随机和循环播放的匹配问题(extend1意外接上了loop2)
            // 不建议将比较长的动画放到Extend或Retract里，联机使用服务器的触发方式会被强制打断
            "loop_start"    "0.25203"   // 算法：目标帧除以总帧数，计算总帧数需要注意把第0帧算进去
            "loop_end"      "0.65853"
        }
    }
}

