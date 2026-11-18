"""应用逻辑：ui.json 里事件写的函数名，就是这里的同名函数。"""

from m20app import every, on_ready, run, ui

@on_ready
def init():
    """界面打开时调用：清空零位偏移、熄灯带、注册退出清理、把初值推给表盘与图标。"""
    st = _st()
    st["zx"] = 0.0
    st["zy"] = 0.0
    _strip_off()
    _arm_exit_cleanup()
    ui.set("gauge", ax=0.0, ay=0.0, angle=0.0, flat=False, range=8.0)
    ui.set("app_icon", ax=0.0, ay=0.0, flat=True, range=6.0)
    ui.set("icon_big", ax=0.0, ay=0.0, flat=True, range=6.0)

def _st():
    """应用内共享状态：零位偏移 + 灯带开关。"""
    g = globals()
    if "_level_state" not in g:
        g["_level_state"] = {"zx": 0.0, "zy": 0.0, "led": True}
    return g["_level_state"]

@every(0.1)
def level_tick():
    """10Hz 读取板载 IMU，驱动机械表盘气泡、读数、图标气泡与灯带指示。"""
    import math

    st = _st()
    try:
        from pinpong.extension.unihikerM20 import imu
        ax, ay, az = imu.read_accel()
    except Exception as e:
        ui.set("sub_label", text=("IMU 读取失败：" + str(e))[:60])
        return

    ax = ax - st["zx"]
    ay = ay - st["zy"]

    p = math.hypot(ax, ay)
    flat = p < 1.2
    angle = math.degrees(math.atan2(p, max(abs(az), 0.05)))

    ui.set("gauge", ax=round(ax, 2), ay=round(ay, 2),
           angle=round(angle, 1), flat=flat, range=8.0)
    # 标题旁的小图标与应用图标页的大图标同步显示真实姿态
    ui.set("app_icon", ax=round(ax, 2), ay=round(ay, 2), flat=flat, range=6.0)
    ui.set("icon_big", ax=round(ax, 2), ay=round(ay, 2), flat=flat, range=6.0)
    ui.set("x_val", text="{:+.2f}".format(ax))
    ui.set("y_val", text="{:+.2f}".format(ay))
    ui.set("angle_val", text="{:.1f}°".format(angle))
    ui.set("status_badge", text="水平 ◆" if flat else "倾斜 ◆")

    if st["led"]:
        try:
            from pinpong.extension.unihikerM20 import strip
            if flat:
                strip.fill(0, 210, 120, brightness=40)
            else:
                strip.fill(255, 170, 0, brightness=28)
        except Exception:
            pass

def on_zero(*_args):
    """归零校准：把当前姿态记为参考零位，并在表盘上给出提示。"""
    st = _st()
    try:
        from pinpong.extension.unihikerM20 import imu
        ax, ay, _az = imu.read_accel()
    except Exception as e:
        ui.toast(("归零失败：" + str(e))[:60])
        return
    st["zx"] = ax
    st["zy"] = ay
    ui.send("gauge", {"cmd": "zeroed"})
    ui.toast("已归零：当前姿态设为参考零位")

def on_led(value, event=None):
    """灯带联动开关：水平亮绿、倾斜亮琥珀；关闭立即熄灭。"""
    st = _st()
    st["led"] = bool(value)
    if not st["led"]:
        _strip_off()
    ui.toast("灯带联动：开" if st["led"] else "灯带联动：关")

def on_gauge(value, event=None):
    """点按表盘即归零校准。"""
    if event and event.get("type") not in (None, "tap"):
        return
    on_zero()

def _strip_off():
    """统一熄灭 8 颗灯带（任何异常都不外抛，退出路径里也安全）。"""
    try:
        from pinpong.extension.unihikerM20 import strip
        strip.off()
    except Exception:
        pass

def _arm_exit_cleanup():
    """注册退出清理：正常退出、点 Home 关闭、或进程被终止时都要熄灯带。"""
    g = globals()
    if g.get("_exit_armed"):
        return
    g["_exit_armed"] = True
    # 1) 正常退出 / 解释器收尾
    try:
        import atexit
        atexit.register(on_exit)
    except Exception:
        pass
    # 2) 被系统或调试器 SIGTERM / SIGINT 结束
    try:
        import signal

        def _sig_cleanup(signum, _frame):
            on_exit()
            try:
                signal.signal(signum, signal.SIG_DFL)
                import os
                os.kill(os.getpid(), signum)
            except Exception:
                pass

        for _name in ("SIGTERM", "SIGINT", "SIGHUP"):
            _sig = getattr(signal, _name, None)
            if _sig is not None:
                try:
                    signal.signal(_sig, _sig_cleanup)
                except Exception:
                    pass
    except Exception:
        pass

def on_exit(value=None, event=None):
    """退出清理：熄灭灯带并记住灯带联动已关闭，避免退出后板子还亮着。"""
    try:
        _st()["led"] = False
    except Exception:
        pass
    _strip_off()

def on_app_icon(value=None, event=None):
    """点按标题旁的小图标 → 打开应用图标规范页。"""
    if event and event.get("type") not in (None, "tap"):
        return
    ui.navigate("icon")

run()
