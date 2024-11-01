#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_basic_waveforms.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 01.11.2024
import random
import cocotb
import os
import logging
import pytest
import copy

from random import randrange
from const.const import cfg
from cocotb_test.simulator import run
from cocotb.triggers import ClockCycles
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, First
from cocotb.regression import TestFactory
from cocotb.result import TestFailure
from cocotbext.waves import waveform


def rnd_val(bit: int = 0, zero: bool = True):
    if zero is True:
        return random.randint(0, (2**bit) - 1)
    else:
        return random.randint(1, (2**bit) - 1)


async def setup_dut(dut, cycles):
    cocotb.start_soon(Clock(dut.clk, *cfg.CLK_100MHz).start())

    # Master side
    dut.in_valid_i.value = 0
    dut.in_data_i.value = 0

    # Slave side
    dut.out_ready_i.value = 0

    dut.rst.value = 1
    await ClockCycles(dut.clk, cycles)
    dut.rst.value = 0


async def mon_stable_data(dut, valid, ready, data):
    """Monitor the interface to ensure data stability when valid is asserted."""
    valid_state = 0
    prev_data = 0
    actual_data = 0

    while True:
        await FallingEdge(dut.clk)

        if valid_state == 1:
            if data.value != prev_data:
                raise TestFailure(
                    f"[MONITOR] Data changed from {prev_data} to {data.value} while valid is asserted and ready is not high"
                )

        if (valid.value == 1) and (ready.value == 0):
            valid_state = 1
            # Capture the data value at the time valid is asserted
            prev_data = copy.deepcopy(data.value)
        else:
            valid_state = 0


async def mon_valid(dut, valid, ready):
    """Monitor the interface to ensure valid stability when ready is not asserted."""
    valid_state = 0

    while True:
        await FallingEdge(dut.clk)

        if valid_state == 1:
            if valid.value != 1:
                raise TestFailure(f"[MONITOR] Valid is not stable while ready == 0")
            elif ready.value == 1:
                valid_state = 0

        if (valid.value == 1) and (ready.value == 0):
            valid_state = 1
        else:
            valid_state = 0


async def mon_score(dut, valid, ready, data, scoreboard):
    """Monitor the interface to capture the values that were transfered."""

    while True:
        await FallingEdge(dut.clk)

        if (valid.value == 1) and (ready.value == 1):
            scoreboard.append(data.value)


async def perf_op(dut, N, width):
    # Master side
    dut.in_valid_i.value = 0
    dut.in_data_i.value = 0
    # Slave side
    dut.out_ready_i.value = 0

    diagram = []
    for i in range(3):
        diagram.append(
            waveform(
                clk=dut.clk,
                name="skid_buffer_" + str(i),
                hscale=4,
                debug=True,
                start=False,
            )
        )
        diagram[i].add_signal(
            [
                dut.in_valid_i,
                dut.in_ready_o,
                dut.in_data_i,
            ],
            group="Input",
        )
        diagram[i].add_signal(
            [
                dut.out_valid_o,
                dut.out_ready_i,
                dut.out_data_o,
            ],
            group="Output",
        )


    diagram[0].start()
    await ClockCycles(dut.clk, 2)
    # Master side
    dut.in_valid_i.value = 1

    # Slave side
    dut.out_ready_i.value = 1

    # No back-pressure
    random_data = [rnd_val(width) for _ in range(N)]
    for val in random_data:
        dut.in_data_i.value = val
        await ClockCycles(dut.clk, 1)

    dut.in_valid_i.value = 0
    dut.in_data_i.value = 0
    dut.out_ready_i.value = 1

    diagram[1].start()

    diagram[0].save_svg()

    await ClockCycles(dut.clk, 2)
    # With random back-pressure
    dut.in_valid_i.value = 1
    random_data = [rnd_val(width) for _ in range(N)]
    for val in random_data:
        dut.in_data_i.value = val
        dut.out_ready_i.value = rnd_val(1, True)
        await ClockCycles(dut.clk, 1)

        while dut.in_ready_o.value == 0:
            dut.in_data_i.value = val
            await ClockCycles(dut.clk, 1)
            dut.out_ready_i.value = rnd_val(1, True)

    while dut.in_ready_o.value == 0:
        await ClockCycles(dut.clk, 1)
        dut.out_ready_i.value = rnd_val(1, True)

    dut.in_valid_i.value = 0
    dut.in_data_i.value = 0
    dut.out_ready_i.value = 1
 
    diagram[1].save_svg()

    diagram[2].start()

    await ClockCycles(dut.clk, 1)
    # With interval between txn
    random_data = [rnd_val(width) for _ in range(N)]
    for val in random_data:
        dut.in_valid_i.value = rnd_val(1, True)
        dut.in_data_i.value = val
        dut.out_ready_i.value = rnd_val(1, True)
        await ClockCycles(dut.clk, 1)

        while dut.in_valid_i.value == 0:
            dut.in_valid_i.value = rnd_val(1, True)
            await ClockCycles(dut.clk, 1)

        while dut.in_ready_o.value == 0:
            dut.out_ready_i.value = rnd_val(1, True)
            await ClockCycles(dut.clk, 1)

    while dut.in_ready_o.value == 0:
        await ClockCycles(dut.clk, 1)
        dut.out_ready_i.value = rnd_val(1, True)

    dut.in_valid_i.value = 0
    dut.in_data_i.value = 0
    dut.out_ready_i.value = 1
    await ClockCycles(dut.clk, 2)

    diagram[2].save_svg()


@cocotb.test()
async def run_test(dut):
    config = os.getenv("CONFIG")
    parameters = cfg.OPTIONS_TEST[config]

    scoreboard = []
    ref_data = []

    await setup_dut(dut, cfg.RST_CYCLES)

    mon_data = cocotb.start_soon(
        mon_stable_data(dut, dut.out_valid_o, dut.out_ready_i, dut.out_data_o)
    )
    mon_val = cocotb.start_soon(mon_valid(dut, dut.out_valid_o, dut.out_ready_i))
    mon_scor = cocotb.start_soon(
        mon_score(dut, dut.out_valid_o, dut.out_ready_i, dut.out_data_o, scoreboard)
    )
    mon_in = cocotb.start_soon(
        mon_score(dut, dut.in_valid_i, dut.in_ready_o, dut.in_data_i, ref_data)
    )
    per = cocotb.start_soon(perf_op(dut, 3, parameters["DATA_WIDTH"]))

    # Wait until the "per" task finishes
    done = await First(per, mon_data, mon_val, mon_scor)

    # Cancel the remaining tasks
    mon_data.kill()
    mon_val.kill()
    mon_scor.kill()
    mon_in.kill()

    print(f"Len scoreboard [{len(scoreboard)}], Len ref_data [{len(ref_data)}]")
    # Compare what was transferred vs what was received
    if scoreboard == ref_data:
        print("[Test result] All values transferred are matching! ")
    else:
        raise TestFailure("[Test result] Values transferred are not matching!")

    for index in range(len(ref_data)):
        if scoreboard[index] == ref_data[index]:
            print(f"[{index}] {int(scoreboard[index])} == {int(ref_data[index])}")


@pytest.mark.parametrize("config", cfg.OPTIONS)
def test_basic_waveforms(config):
    """
    Check whether valid / ready can be transfered through the skid buffer.

    Test ID: 1
    """
    module = os.path.splitext(os.path.basename(__file__))[0]
    SIM_BUILD = os.path.join(
        cfg.TESTS_DIR, f"../../run_dir/sim_build_{cfg.SIMULATOR}_{module}_{config}"
    )

    extra_args_sim = cfg.EXTRA_ARGS
    extra_args_sim = cfg._get_cfg_args(config)
    cfg.EXTRA_ENV["CONFIG"] = config

    run(
        python_search=[cfg.TESTS_DIR],
        includes=cfg.INC_DIR,
        verilog_sources=cfg.VERILOG_SOURCES,
        toplevel=cfg.TOPLEVEL,
        timescale=cfg.TIMESCALE,
        module=module,
        extra_args=extra_args_sim,
        extra_env=cfg.EXTRA_ENV,
        sim_build=SIM_BUILD,
        plus_args=["--trace"],  # https://github.com/cocotb/cocotb/issues/3894
        waves=1,
    )
