"""Suppression of Playwright Inspector, recorder, and debug mode.

This module guarantees that Playwright never pauses or opens the Playwright Inspector GUI
by:
1. Setting PWDEBUG="0" (which coreBundle.js checks to explicitly disable debugMode).
2. Setting PW_CODEGEN_NO_INSPECTOR="1" (which instructs RecorderApp.show to immediately return).
3. Monkey-patching playwright._impl.utils.debug.debug_mode to always return "".
4. Monkey-patching playwright._impl._driver.get_driver_env so the spawned Node.js driver
   receives clean, non-debug environment variables.
"""

import os
import sys


def suppress_playwright_inspector() -> None:
    """Enforce complete suppression of Playwright Inspector, recorder, and debug pauses."""
    os.environ["PWDEBUG"] = "0"
    os.environ["PW_CODEGEN_NO_INSPECTOR"] = "1"
    os.environ["PLAYWRIGHT_INSPECT"] = "0"
    os.environ["PW_TEST_DEBUG"] = "0"
    os.environ.pop("npm_config_pwdebug", None)
    os.environ.pop("npm_package_config_pwdebug", None)

    try:
        import playwright._impl.utils.debug as _pw_debug
        _pw_debug._debug_mode = "0"
        _pw_debug.debug_mode = lambda: ""
    except Exception:
        pass

    try:
        import playwright._impl._driver as _pw_driver
        _orig_get_driver_env = _pw_driver.get_driver_env

        def _safe_get_driver_env() -> dict:
            env = _orig_get_driver_env()
            env["PWDEBUG"] = "0"
            env["PW_CODEGEN_NO_INSPECTOR"] = "1"
            env["PLAYWRIGHT_INSPECT"] = "0"
            env["PW_TEST_DEBUG"] = "0"
            for k in list(env.keys()):
                if "PWDEBUG" in k.upper() or "INSPECT" in k.upper():
                    if k not in ("PWDEBUG", "PW_CODEGEN_NO_INSPECTOR"):
                        env.pop(k, None)
            return env

        _pw_driver.get_driver_env = _safe_get_driver_env
    except Exception:
        pass


# Run suppression automatically on module import
suppress_playwright_inspector()
