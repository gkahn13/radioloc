import time
import sys
from rflib import *

import argparse


FREQ = 910e6 # Set my frequency to the gate remote
PKTLEN = 6       # Set my packet length to 6 as I am sending
                 # 6 bytes in each packet
DRATE = 1000     # baud rate of 1000 means that a 1ms pulse
                 # can be counted as a bit

packet = [
    # '10101010'
            '00010001', '00010111', '01110001',
            '01110011', '01110001', '00110000'
           ]
# packet_2 = [
#             '00010001', '00100100', '01100111',
#             '01001010', '00001111', '00011110'
           # ]
data_hex = [ chr(int(x, 2)) for x in packet]


def send_data(d, data, repeat=4):
    # PCM'ify the packets
    for i in range(0,repeat):
        for packet in data:
            d.RFxmit(packet)

def transmit(dongle_index, fc):
    d = RfCat(dongle_index)
    # d.setFreq(FREQ)
    d.setFreq(fc)
    d.setMdmModulation(MOD_MSK)
    # d.setMdmModulation(MOD_ASK_OOK)
    d.makePktFLEN(PKTLEN)
    d.setMdmDRate(DRATE)
    d.setMdmSyncMode(0) # disable syncword and preamble as this is not used
    # by the remote.
    d.setMaxPower()    #imma chargin' mah lazer
    while True:
        try:
            send_data(d, ["".join(data_hex)])

        except Exception, e:
            sys.exit("Error %s" % str(e))
            # TODO implement software reset in case of USB timeout


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='dongle index.')

    parser.add_argument("-dongle_index", type=int, help="Dongle index", default=0)
    parser.add_argument("frequency", type=float, help="Center frequency", default=910e6)

    args = parser.parse_args()
    print args.dongle_index

    transmit(args.dongle_index, args.frequency)
