#!/usr/bin/env python2

import sys
from configuration import patterns


def with_rbx(i, rbx):
    offset = patterns.ngOffset
    prefix, side, number = patterns.prefix_side_number(rbx)
    i = i << offset
    i |= (number & 0xff) << (8 + offset)
    i |= (patterns.side_code(side) & 0xf) << (16 + offset)
    i |= (patterns.subdetector_code(prefix) & 0xf) << (20 + offset)
    return i


def fiberid_hehb(rbx, qiecard, rm):
    i = qiecard & 0xf
    i |= (rm & 0xf) << 4
    return with_rbx(i, rbx)


def fiberid_hf(rbx, slot):
    i = slot & 0xff
    return with_rbx(i, rbx)


def formatted(fiberid):                    
    return "0x%04x 0x%08x 0x%08x" % ((fiberid >> 64) & 0xffff,
                                     (fiberid >> 32) & 0xffffffff,
                                     (fiberid >>  0) & 0xffffffff,
                                    )


def mode3_command_string(rbxes=[]):
    commands = []
    for rbx in rbxes:
        if rbx.startswith("HE"):
            for rm in range(1, 6):
                for qiecard in range(1, 5):
                    if rm == 5:
                        if qiecard != 1:
                            continue
                        stem = "%s-calib-i" % rbx
                    else:
                        stem = "%s-%d-%d-i" % (rbx, rm, qiecard)
                    data = formatted(fiberid_hehb(rbx, qiecard, rm))
                    for iLink in [1, 2]:
                        commands.append("put %s_FiberID%d %s" % (stem, iLink, data))
                    commands.append("put %s_LinkTestMode 3" % stem)

        elif rbx.startswith("HB"):
            for rm in range(1, 6):
                for qiecard in range(1, 5):
                    for fpga in ["iTop", "iBot"]:
                        if rm == 5:
                            if qiecard != 1:
                                continue
                            stem = "%s-calib-%s" % (rbx, fpga)
                        else:
                            stem = "%s-%d-%d-%s" % (rbx, rm, qiecard, fpga)
                        data = formatted(fiberid_hehb(rbx, qiecard, rm))
                        iLink = 1 # HB only uses iLink = 1
                        commands.append("put %s_FiberID%d %s" % (stem, iLink, data))
                        commands.append("put %s_LinkTestMode 3" % stem)
        
            
        elif rbx.startswith("HF"):
            for slot in range(1, 14):
                for fpga in ["iTop", "iBot"]:
                    stem = "%s-%d-%s" % (rbx, slot, fpga)
                    data = formatted(fiberid_hf(rbx, slot))
                    for iLink in [1, 2, 3]:
                        commands.append("put %s_FiberID%d %s" % (stem, iLink, data))
                    commands.append("put %s_LinkTestMode 3" % stem)

        else:
            # print rbx_prefix, rbx_side, rbx_num
            sys.exit("How shall I handle RBX '%s'?" % rbx)

    return "\n".join(commands)


def exercise_bits(stem=""):
    lines = []
    for iBit in range(80):
        if not iBit:
            lines.append("put %s_LinkTestMode 3" % stem)
        lines += ["FiberId_%d : 100" % iBit,
                  "  put %s-i_FiberID1 %s" % (stem, formatted(1 << iBit)),
                  ]
    return "\n".join(lines)


if __name__ == "__main__":
    # print "\n", exercise_bits("HE16-3-1-i")
    # print "\n", mode3_command_string(["HE%d" % i for i in range(20)])
    # print "\n", mode3_command_string(["HFP%02d" % i for i in range(1, 2)])
    print "\n", mode3_command_string(["HB%d" % i for i in range(20)])
    print "\n", mode3_command_string(["HBP%02d" % i for i in range(1, 19)])
    print "\n", mode3_command_string(["HBM%02d" % i for i in range(1, 19)])
