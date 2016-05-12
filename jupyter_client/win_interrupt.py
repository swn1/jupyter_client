"""Use a Windows event to interrupt a child process like SIGINT.

The child needs to explicitly listen for this - see
ipykernel.parentpoller.ParentPollerWindows for a Python implementation.
"""

import platform
if platform.python_implementation() == 'IronPython':
    import System
    from System.Threading import EventWaitHandle, EventResetMode
    from System.Security.AccessControl import EventWaitHandleSecurity

    class WrappedEventWaitHandle(EventWaitHandle):
        def __new__(cls):
            sa = EventWaitHandleSecurity()
            # the .NET api does not seem to expose the bInheritHandle flag, but it seems to be setting it internally.  ???
            rv,created = EventWaitHandle.__new__(cls, False, EventResetMode.ManualReset, None, sa)
            return rv
        def __str__(self):
            return str(self.Handle)

    def create_interrupt_event():
        return WrappedEventWaitHandle()
    def send_interrupt(interrupt_handle):
        interrupt_handle.Set()
else:
    import ctypes

    def create_interrupt_event():
        """Create an interrupt event handle.

        The parent process should call this to create the
        interrupt event that is passed to the child process. It should store
        this handle and use it with ``send_interrupt`` to interrupt the child
        process.
        """
        # Create a security attributes struct that permits inheritance of the
        # handle by new processes.
        # FIXME: We can clean up this mess by requiring pywin32 for IPython.
        class SECURITY_ATTRIBUTES(ctypes.Structure):
            _fields_ = [ ("nLength", ctypes.c_int),
                         ("lpSecurityDescriptor", ctypes.c_void_p),
                         ("bInheritHandle", ctypes.c_int) ]
        sa = SECURITY_ATTRIBUTES()
        sa_p = ctypes.pointer(sa)
        sa.nLength = ctypes.sizeof(SECURITY_ATTRIBUTES)
        sa.lpSecurityDescriptor = 0
        sa.bInheritHandle = 1

        return ctypes.windll.kernel32.CreateEventA(
            sa_p,  # lpEventAttributes
            False, # bManualReset
            False, # bInitialState
            '')    # lpName

    def send_interrupt(interrupt_handle):
        """ Sends an interrupt event using the specified handle.
        """
        ctypes.windll.kernel32.SetEvent(interrupt_handle)
