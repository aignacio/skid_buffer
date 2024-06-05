#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : const.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 06.06.2024
import os
import glob
import copy


class cfg:
    RST_CYCLES = 3
    CLK_100MHz = (10, "ns")
    TIMEOUT_TEST = (CLK_100MHz[0] * 200, "ns")
    TIMEOUT_TEST = (CLK_100MHz[0] * 200, "ns")

    TOPLEVEL = str(os.getenv("DUT"))
    SIMULATOR = str(os.getenv("SIM"))

    TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
    INC_DIR = [os.path.join(TESTS_DIR, "../../rtl/include")]
    RTL_DIR = os.path.join(TESTS_DIR, "../../rtl")

    VERILOG_SOURCES = []  # The sequence below is important...
    VERILOG_SOURCES = VERILOG_SOURCES + glob.glob(f"{RTL_DIR}/*.sv", recursive=True)
    VERILOG_SOURCES = VERILOG_SOURCES + glob.glob(f"{RTL_DIR}/*.v", recursive=True)

    EXTRA_ENV = {}
    EXTRA_ENV["COCOTB_HDL_TIMEPRECISION"] = os.getenv("TIMEPREC")
    EXTRA_ENV["COCOTB_HDL_TIMEUNIT"] = os.getenv("TIMEUNIT")
    TIMESCALE = os.getenv("TIMEUNIT") + "/" + os.getenv("TIMEPREC")

    if SIMULATOR == "verilator":
        EXTRA_ARGS = [
            "--trace-fst",
            "--coverage",
            "--coverage-line",
            "--coverage-toggle",
            "--trace-structs",
            "--Wno-UNOPTFLAT",
            "--Wno-REDEFMACRO",
        ]
    else:
        EXTRA_ARGS = []
        
    EXTRA_ARGS_SMALL = copy.deepcopy(EXTRA_ARGS)
    EXTRA_ARGS_BIG = copy.deepcopy(EXTRA_ARGS)
   
    OPTIONS = ["SMALL", "BIG"] 
    OPTIONS_TEST = {}
    
    SMALL = {}
    SMALL['DATA_WIDTH'] = 1
    SMALL['REG_OUTPUT'] = 0

    BIG = {}
    BIG['DATA_WIDTH'] = 32
    BIG['REG_OUTPUT'] = 1
 
    OPTIONS_TEST['SMALL'] = SMALL 
    OPTIONS_TEST['BIG'] = BIG 
   
    for param in SMALL.items():
        EXTRA_ARGS_SMALL.append("-G"+param[0].upper()+"="+str(param[1]))
    for param in BIG.items():
        EXTRA_ARGS_BIG.append("-G"+param[0].upper()+"="+str(param[1]))

    def _get_cfg_args(config):
        if config == "SMALL":
            return cfg.EXTRA_ARGS_SMALL
        elif config == "BIG":
            return cfg.EXTRA_ARGS_BIG
