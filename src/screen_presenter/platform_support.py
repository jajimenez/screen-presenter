import ctypes
import sys
from pathlib import Path

RESOURCES_PATH = Path(__file__).parent / "resources"

# Never shown to the user, but Qt requires a non-empty value before it requests camera
# access when running the unbundled application (e.g. python -m). The bundled
# application takes its text from permission.camera in pyproject.toml.
CAMERA_USAGE_DESCRIPTION = (
    "Screen Presenter needs camera access to display your camera video on screen."
)


def get_logo_path() -> Path:
    """Return the logo file suited to the current platform."""
    # MacOS icons usually have transparent padding
    name = "logo-macos.svg" if sys.platform == "darwin" else "logo.svg"
    return RESOURCES_PATH / name


def set_up_platform(app_id: str) -> None:
    """Apply the platform-specific settings; call before creating the QApplication."""
    if sys.platform == "win32":
        _set_windows_app_id(app_id)
    elif sys.platform == "darwin":
        _set_camera_usage_description()


def _set_windows_app_id(app_id: str) -> None:
    """Give the process its own ID so the taskbar doesn't group it under python.exe.

    Windows only; must be called before any window is created.
    """
    # Also narrows the platform for type checkers, as ctypes.windll only exists on
    # Windows
    assert sys.platform == "win32"

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


def _set_camera_usage_description() -> None:
    """Add NSCameraUsageDescription to the running process's Info.plist (MacOS only).

    Qt refuses to request camera permission without it, and a plain Python interpreter
    has no bundle, so the permission prompt would never appear.
    """
    # Load the Objective-C runtime, and Foundation, which provides NSBundle and NSString
    objc = ctypes.cdll.LoadLibrary("libobjc.dylib")
    ctypes.cdll.LoadLibrary(
        "/System/Library/Frameworks/Foundation.framework/Foundation"
    )

    # Pointers are returned and passed as c_void_p so they are not truncated to 32 bits
    objc.objc_getClass.restype = ctypes.c_void_p
    objc.objc_getClass.argtypes = [ctypes.c_char_p]
    objc.sel_registerName.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]

    send = objc.objc_msgSend
    send.restype = ctypes.c_void_p

    def call(receiver: int, selector: bytes, *args: int | bytes | None):
        """Send an Objective-C message, i.e. call a method on an object or class."""
        # objc_msgSend is variadic, so its argument types must be set on every call
        arg_types = [
            ctypes.c_char_p if isinstance(a, bytes) else ctypes.c_void_p for a in args
        ]
        send.argtypes = [ctypes.c_void_p, ctypes.c_void_p, *arg_types]

        return send(receiver, objc.sel_registerName(selector), *args)

    def ns_string(text: str) -> int:
        """Create an NSString from a Python string."""
        return call(
            objc.objc_getClass(b"NSString"), b"stringWithUTF8String:", text.encode()
        )

    # [[NSBundle mainBundle] infoDictionary]: the process's Info.plist contents
    bundle = call(objc.objc_getClass(b"NSBundle"), b"mainBundle")
    info = call(bundle, b"infoDictionary")

    # Qt checks for this key before requesting camera permission; the dictionary is
    # mutable in practice despite its declared type
    if info:
        call(
            info,
            b"setObject:forKey:",
            ns_string(CAMERA_USAGE_DESCRIPTION),
            ns_string("NSCameraUsageDescription"),
        )
