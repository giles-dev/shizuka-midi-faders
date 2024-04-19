import storage, usb_cdc, usb_hid
import board

from digitalio import DigitalInOut, Pull

# We never want to present as a HID
usb_hid.disable()

# This is a jumper that should be closed to ground for "debug mode"
button = DigitalInOut(board.D24)
button.pull = Pull.UP

# If high, jumper is OPEN (not debug), so disable the USB drive and the COM port
if button.value:
    storage.disable_usb_drive()
    usb_cdc.disable()


