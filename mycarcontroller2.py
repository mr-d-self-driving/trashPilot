# publishes carstate and takes input from car control
import time
import zmq
import capnp
import can
import cantools

def convert_torque(msg):
    val = msg.carControl.actuators.torque
    effort = abs(int((val / 12 * 250)))
    effort = max(0, min(110, effort))
    return effort

def convert_direction(msg):
    val = msg.carControl.actuators.torque
    dir = 2 if val > 0 else 1
    return dir

example_capnp = capnp.load('experiments/messaging/example.capnp')
ctx = zmq.Context()
# SUB: torque commands
sub = ctx.socket(zmq.SUB)
sub.connect("tcp://localhost:5558")
sub.setsockopt_string(zmq.SUBSCRIBE, "")

pub = ctx.socket(zmq.PUB)
pub.bind("tcp://*:5556")

db = cantools.database.load_file("assets/samples/hyundai_elantra_2006.dbc")

# bus = can.interface.Bus(
#         channel='can0',
#         interface='socketcan',
#         can_filters=[{"can_id": 0x440, "can_mask": 0x7FF}]
#     )

messages = [
    [db.get_message_by_name("STEER_CMD"),
     {"steering_torque": convert_torque,
      "steering_direction": convert_direction}]
    # add more messages if needed [name,{}]
]

while True:
    raw = sub.recv() 
    with example_capnp.Event.from_bytes(raw) as msg:
        for name, sigdict in messages:
            message = can.Message(
                arbitration_id=name.frame_id,
                is_extended_id=False,
                data = name.encode({k: fn(msg) for k, fn in sigdict.items()})
            )
            # bus.send(message)
            # print(message)