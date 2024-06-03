#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_basic.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 03.06.2024
import random
import cocotb
import os
import logging
import pytest

from random import randrange
from const.const import cfg
from cocotb_test.simulator import run
from cocotb.triggers import ClockCycles
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory
from cocotb.result import TestFailure

def rnd_val(bit: int = 0, zero: bool = True):
    if zero is True:
        return random.randint(0, (2**bit) - 1)
    else:
        return random.randint(1, (2**bit) - 1)

async def setup_dut(dut, cycles):
    cocotb.start_soon(Clock(dut.clk, *cfg.CLK_100MHz).start())
    dut.rst.value = 1
    await ClockCycles(dut.clk, cycles)
    dut.rst.value = 0

@cocotb.test()
async def run_test(dut):
    await setup_dut(dut, cfg.RST_CYCLES)
    # Master side
    dut.in_valid_i.value = 0
    dut.in_data_i.value = 0 #rnd_val(8, True) 
    
    # Slave side
    dut.out_ready_i.value = 0
    await ClockCycles(dut.clk, 10) 

    ## Inicia aqui o test

    # Master side
    dut.in_valid_i.value = 1
    
    # Slave side
    dut.out_ready_i.value = 1
    
    for i in range(100):
        dut.in_data_i.value = rnd_val(8, True) 
        await ClockCycles(dut.clk, 1) 

    dut.in_valid_i.value = 0
    dut.in_data_i.value = 0
    dut.out_ready_i.value = 0
    await ClockCycles(dut.clk, 10) 

    dut.in_valid_i.value = 1
    for i in range(100):
        dut.out_ready_i.value = rnd_val(1, True) 
        if dut.in_ready_o.value != 0:
            dut.in_data_i.value = rnd_val(8, True) 
        await ClockCycles(dut.clk, 1) 

    while dut.in_ready_o.value == 0:
        await ClockCycles(dut.clk, 1) 
        dut.out_ready_i.value = rnd_val(1, True) 

    dut.in_valid_i.value = 0
    dut.in_data_i.value = 0
    dut.out_ready_i.value = 1
    await ClockCycles(dut.clk, 10)

def test_basic():
    """
    Basic test to check the DUT

    Test ID: 1
    """
    module = os.path.splitext(os.path.basename(__file__))[0]
    SIM_BUILD = os.path.join(
        cfg.TESTS_DIR, f"../../run_dir/sim_build_{cfg.SIMULATOR}_{module}"
    )
    extra_args_sim = cfg.EXTRA_ARGS

    run(
        python_search=[cfg.TESTS_DIR],
        includes=cfg.INC_DIR,
        verilog_sources=cfg.VERILOG_SOURCES,
        toplevel=cfg.TOPLEVEL,
        timescale=cfg.TIMESCALE,
        module=module,
        sim_build=SIM_BUILD,
        extra_args=extra_args_sim,
        waves=1,
    )
