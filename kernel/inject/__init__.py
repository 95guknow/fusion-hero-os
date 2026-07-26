# Kernel inject package — assembly-primary, host-simulated on Windows
try:
    from kernel.inject.inject_host import (  # type: ignore
        CAP_HOOK,
        CAP_ISR,
        CAP_NONE,
        CAP_PRIV,
        CAP_QUANTUM,
        CAP_READ,
        CAP_SWAP,
        InjectHost,
        get_inject_host,
        preload_kernel_inject,
    )
except ImportError:  # package-relative
    from .inject_host import (  # type: ignore
        CAP_HOOK,
        CAP_ISR,
        CAP_NONE,
        CAP_PRIV,
        CAP_QUANTUM,
        CAP_READ,
        CAP_SWAP,
        InjectHost,
        get_inject_host,
        preload_kernel_inject,
    )

__all__ = [
    "InjectHost",
    "get_inject_host",
    "preload_kernel_inject",
    "CAP_NONE",
    "CAP_READ",
    "CAP_HOOK",
    "CAP_SWAP",
    "CAP_ISR",
    "CAP_QUANTUM",
    "CAP_PRIV",
]
