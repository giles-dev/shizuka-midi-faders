# Shizuka v1.0
# A DIY MIDI Fader controller
# Giles Moss giles@digitalchild.co.uk
#
# Based entirely on https://github.com/adafruit/Adafruit_Learning_System_Guides/blob/main/Grand_Central_MIDI_Knobs/code.py
# Thanks.
#

import board
import time
from simpleio import map_range
from analogio import AnalogIn
from digitalio import DigitalInOut, Direction
import usb_midi
import adafruit_midi  # MIDI protocol encoder/decoder library
from adafruit_midi.control_change import ControlChange

# pick your USB MIDI out channel here, 1-16
MIDI_USB_channel = 1

midi_usb = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1], out_channel=MIDI_USB_channel - 1
)

led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT

knob_count = 4      # Set the total number of potentiometers used
num_samples = 5     # How many samples to average over
hyst_window = 300   # Hysteresis window

# Create the input objects list for potentiometers
knob = []
for k in range(knob_count):
    knobs = AnalogIn(
        getattr(board, "A{}".format(k))
    )  # get pin # attribute, use string formatting
    knob.append(knobs)

#  assignment of knobs to cc numbers
cc_number = [
    11,  # knob 1, expression
    1,   # knob 2, mod wheel
    12,  # knob 3, effect controller 1
    13,  # knob 4, effect controller 2
]

# CC range list defines the characteristics of the potentiometers
#  This list contains the input object, minimum value, and maximum value for each knob.
#   example ranges:
#   0 min, 127 max: full range control voltage
#   36 (C2) min, 84 (B5) max: 49-note keyboard
#   21 (A0) min, 108 (C8) max: 88-note grand piano
cc_range = [
    (0, 127),  # knob 0
    (0, 127),  # knob 1
    (0, 127),  # knob 2
    (0, 127),  # knob 3
]


print("---Shizuka v1.0: MIDI Fader Controller---")
print(f"   USB MIDI channel: {MIDI_USB_channel}")

for i in range(knob_count):
    print(f"   MIDI Fader {i + 1}: CC{cc_number[i]}")

# Initialize cc_value list with current sample placeholders - this is a 2D array
cc_value = []
for i in range(knob_count):
    col = []
    for j in range(num_samples):
        col.append(0)
    cc_value.append(col)

# The value that last exceeded the hysteresis window
last_cc_value = []
for _ in range(knob_count):
    last_cc_value.append(0)

# The value we last sent out as MIDI
last_midi_value = []
for _ in range(knob_count):
    last_midi_value.append(-1)

sample_counter = 0
cts = False

while True:
    # Loop through all knobs
    for aknob in range(knob_count):
        
        # Sample the Fader
        cc_value[aknob][sample_counter] = knob[aknob].value

        # Average the sample
        averaged_sample = 0
        for j in range(num_samples):
            averaged_sample += cc_value[aknob][j]
        averaged_sample = averaged_sample / num_samples

        # Check averaged sample against hysteresis window
        if cts and abs(averaged_sample - last_cc_value[aknob]) > hyst_window:
            last_cc_value[aknob] = averaged_sample

            # Finally, as MIDI is only 7 bits, we can have the case where two different samples map to the same
            # MIDI value. De-dupe these as a final, ultra-dumb, step
            midival = int(map_range(last_cc_value[aknob], 300, 65000, cc_range[aknob][0], cc_range[aknob][1]))
            if last_midi_value[aknob] != midival:
                last_midi_value[aknob] = midival
                led.value = True
                midi_usb.send(ControlChange(cc_number[aknob], midival))

        #print(f"{sample_counter}: {cc_value[aknob][sample_counter]} ave:{averaged_sample} last:{last_cc_value[aknob]} MIDI:{midival}")

    sample_counter += 1
    if sample_counter >= num_samples:
        sample_counter = 0
        # cts stops us sending values until the sample averaging buffer is full
        if not cts:
            cts = True

    time.sleep(0.01)
    led.value = False

    