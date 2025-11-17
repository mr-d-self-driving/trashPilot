# publishes carstate and takes input from car control
import time
import zmq
import capnp
import can
import cantools
import threading
import random
def start_fake_can_sender():
    # Use python-can virtual bus
    tx_bus = can.interface.Bus(channel='virtual', bustype='virtual')

    def sender_loop():
        while True:
            # Random speed 0–150 km/h
            speed = random.randint(0, 150)

            # Random brake signal 0–3 (2-bit)
            brake = random.randint(0, 3)

            # Build CAN data frame (8 bytes)
            data = [0] * 8

            # speed: 23|8 -> byte index 2
            data[2] = speed

            # brake_pressed: 27|2 -> byte index 3, bits 0-1
            data[3] = brake & 0b11

            msg = can.Message(
                arbitration_id=0x440,
                data=data,
                is_extended_id=False
            )

            try:
                tx_bus.send(msg)
            except can.CanError:
                print("Send failed")

            time.sleep(0.1)  # send at 10 Hz

    thread = threading.Thread(target=sender_loop, daemon=True)
    thread.start()
    print("⚡ Fake CAN sender running on virtual bus (speed + brake)")


# Call this once at the top of your program
start_fake_can_sender()
example_capnp = capnp.load('experiments/messaging/example.capnp')
ctx = zmq.Context()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://*:5556")

# Load DBC
db = cantools.database.load_file("assets/samples/hyundai_elantra_2006.dbc")

# Identify the message
msg_440 = db.get_message_by_name("NEW_MSG_440")

# Setup CAN bus
bus = can.interface.Bus(
    channel='virtual',
    interface='virtual',
    #can_filters=[{"can_id": 0x440, "can_mask": 0x7FF}]
)

while True:
    m = bus.recv(timeout=0.0)
    if m is None:
        continue

    # Decode using DBC
    decoded = msg_440.decode(m.data)

    # Extract signals
    speed = decoded.get("speed", 0.0)          # Already in km/h, scale applied
    brake = decoded.get("brake_pressed", 0)    # 0–3

    # Create message
    msg = example_capnp.Event.new_message()
    msg.logMonoTime = int(time.monotonic() * 1000)
    car_state = msg.init('carState')

    # Fill in values
    car_state.vEgo = float(speed) / 3.6   # convert km/h → m/s if desired
    car_state.brakePressed = brake

    # Publish
    pub.send(msg.to_bytes())
