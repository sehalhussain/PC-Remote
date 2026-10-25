import threading
import time

import pygame
import pyautogui


class XboxControllerListener:
    """Read a connected game controller and translate input to desktop actions."""

    DEADZONE = 0.15
    POLL_INTERVAL = 0.01
    MOUSE_SPEED = 900
    SCROLL_MIN_SPEED = 18
    SCROLL_MAX_SPEED = 240
    VOLUME_REPEAT_INTERVAL = 0.12

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._enabled = True
        self._connected = False
        self._controller_name = None
        self._error = None
        self._thread = None

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
        self._thread = threading.Thread(
            target=self._listen, name="XboxControllerListener", daemon=True
        )
        self._thread.start()

    def stop(self):
        with self._lock:
            self._running = False
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=1)

    def enable(self):
        with self._lock:
            self._enabled = True

    def disable(self):
        with self._lock:
            self._enabled = False

    def status(self):
        with self._lock:
            return {
                "connected": self._connected,
                "enabled": self._enabled,
                "controller_name": self._controller_name,
                "error": self._error,
            }

    @staticmethod
    def _axis_value(value):
        value = 0.0 if abs(value) < XboxControllerListener.DEADZONE else value
        if value == 0:
            return 0.0
        magnitude = (abs(value) - XboxControllerListener.DEADZONE) / (
            1 - XboxControllerListener.DEADZONE
        )
        return (1 if value > 0 else -1) * magnitude**1.5

    @staticmethod
    def _scroll_rate(value):
        if value == 0:
            return 0.0
        speed = XboxControllerListener.SCROLL_MIN_SPEED + (
            XboxControllerListener.SCROLL_MAX_SPEED
            - XboxControllerListener.SCROLL_MIN_SPEED
        ) * abs(value) ** 2
        return speed if value > 0 else -speed

    @staticmethod
    def _dpad(controller):
        if controller.get_numhats():
            x, y = controller.get_hat(0)
            return x, y
        buttons = controller.get_numbuttons()
        return (
            int(buttons > 14 and controller.get_button(14))
            - int(buttons > 13 and controller.get_button(13)),
            int(buttons > 11 and controller.get_button(11))
            - int(buttons > 12 and controller.get_button(12)),
        )

    def _set_connection(self, connected, name=None, error=None):
        with self._lock:
            self._connected = connected
            self._controller_name = name
            self._error = error

    def _listen(self):
        joystick = None
        dragging = False

        required_pygame_api = ("init", "quit", "error", "event", "joystick")
        if any(not hasattr(pygame, name) for name in required_pygame_api) or not all(
            callable(getattr(pygame, name, None)) for name in ("init", "quit")
        ):
            message = (
                "Pygame is incomplete. Reinstall project dependencies with "
                "'python -m pip install -r requirements.txt'."
            )
            self._set_connection(False, error=message)
            with self._lock:
                self._running = False
            print(f"Controller listener error: {message}")
            return

        try:
            pygame.init()
            pygame.joystick.init()
            previous_buttons = set()
            previous_dpad = (0, 0)
            repeat_direction = 0
            next_volume_repeat = 0.0
            mouse_x_remainder = 0.0
            mouse_y_remainder = 0.0
            scroll_x_remainder = 0.0
            scroll_y_remainder = 0.0

            while True:
                with self._lock:
                    running = self._running
                    enabled = self._enabled
                if not running:
                    break

                pygame.event.pump()
                if joystick is not None and (
                    pygame.joystick.get_count() == 0 or not joystick.get_init()
                ):
                    if joystick.get_init():
                        joystick.quit()
                    joystick = None
                    if dragging:
                        pyautogui.mouseUp(button="left")
                        dragging = False
                    self._set_connection(False)

                if joystick is None:
                    if pygame.joystick.get_count() == 0:
                        self._set_connection(False)
                        time.sleep(0.5)
                        continue
                    joystick = pygame.joystick.Joystick(0)
                    joystick.init()
                    previous_buttons.clear()
                    previous_dpad = (0, 0)
                    repeat_direction = 0
                    mouse_x_remainder = 0.0
                    mouse_y_remainder = 0.0
                    scroll_x_remainder = 0.0
                    scroll_y_remainder = 0.0
                    self._set_connection(True, joystick.get_name())

                try:
                    now = time.monotonic()
                    button_count = joystick.get_numbuttons()
                    buttons = {
                        button
                        for button in range(button_count)
                        if joystick.get_button(button)
                    }
                    dpad = self._dpad(joystick)
                    if enabled:
                        left_x = self._axis_value(joystick.get_axis(0))
                        left_y = self._axis_value(joystick.get_axis(1))
                        right_x = self._axis_value(joystick.get_axis(2))
                        right_y = self._axis_value(joystick.get_axis(3))
                        left_trigger = (
                            joystick.get_numaxes() > 4
                            and joystick.get_axis(4) > 0.5
                        )
                except pygame.error as error:
                    joystick = None
                    if dragging:
                        pyautogui.mouseUp(button="left")
                        dragging = False
                    self._set_connection(False, error=str(error))
                    time.sleep(0.5)
                    continue

                if not enabled:
                    if dragging:
                        pyautogui.mouseUp(button="left")
                        dragging = False
                    previous_buttons = buttons
                    previous_dpad = dpad
                    repeat_direction = 0
                    time.sleep(self.POLL_INTERVAL)
                    continue

                delta_time = self.POLL_INTERVAL
                mouse_x_remainder += left_x * self.MOUSE_SPEED * delta_time
                mouse_y_remainder += left_y * self.MOUSE_SPEED * delta_time
                move_x = int(mouse_x_remainder)
                move_y = int(mouse_y_remainder)
                if move_x or move_y:
                    pyautogui.moveRel(move_x, move_y)
                    mouse_x_remainder -= move_x
                    mouse_y_remainder -= move_y

                scroll_x_remainder += self._scroll_rate(right_x) * delta_time
                scroll_y_remainder -= self._scroll_rate(right_y) * delta_time
                scroll_x = int(scroll_x_remainder)
                scroll_y = int(scroll_y_remainder)
                if scroll_y:
                    pyautogui.scroll(scroll_y)
                    scroll_y_remainder -= scroll_y
                if scroll_x:
                    pyautogui.hscroll(scroll_x)
                    scroll_x_remainder -= scroll_x

                if left_trigger and not dragging:
                    pyautogui.mouseDown(button="left")
                    dragging = True
                elif not left_trigger and dragging:
                    pyautogui.mouseUp(button="left")
                    dragging = False

                button_actions = {
                    0: ("click", "left"),
                    1: ("click", "right"),
                    2: ("key", "playpause"),
                    3: ("key", "volumemute"),
                    5: ("key", "nexttrack"),
                    6: ("hotkey", ("win", "d")),
                    7: ("key", "f11"),
                }
                for button, action in button_actions.items():
                    if button in buttons and button not in previous_buttons:
                        if action[0] == "click":
                            pyautogui.click(button=action[1])
                        elif action[0] == "hotkey":
                            pyautogui.hotkey(*action[1])
                        else:
                            pyautogui.press(action[1])

                for direction, key_name in ((-1, "left"), (1, "right")):
                    if (
                        dpad[0] == direction
                        and previous_dpad[0] != direction
                    ):
                        pyautogui.press(key_name)

                volume_direction = 1 if dpad[1] > 0 else -1 if dpad[1] < 0 else 0
                if volume_direction != repeat_direction:
                    if volume_direction:
                        pyautogui.press(
                            "volumeup" if volume_direction > 0 else "volumedown"
                        )
                        next_volume_repeat = now + self.VOLUME_REPEAT_INTERVAL
                    repeat_direction = volume_direction
                elif volume_direction and now >= next_volume_repeat:
                    pyautogui.press(
                        "volumeup" if volume_direction > 0 else "volumedown"
                    )
                    next_volume_repeat = now + self.VOLUME_REPEAT_INTERVAL

                previous_buttons = buttons
                previous_dpad = dpad
                time.sleep(self.POLL_INTERVAL)
        except (pygame.error, ImportError) as error:
            self._set_connection(False, error=str(error))
            print(f"Controller listener error: {error}")
        finally:
            if dragging:
                pyautogui.mouseUp(button="left")
            if joystick is not None and joystick.get_init():
                joystick.quit()
            pygame.quit()
            self._set_connection(False, error=self._error)
            with self._lock:
                self._running = False


if __name__ == "__main__":
    listener = XboxControllerListener()
    listener.start()
    print("Controller listener running. Press Ctrl+C to stop.")
    last_status = None
    try:
        while True:
            status = listener.status()
            if status != last_status:
                print(status)
                last_status = status
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
