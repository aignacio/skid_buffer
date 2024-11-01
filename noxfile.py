#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : noxfile.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 08.10.2023
# Last Modified Date: 01.11.2024

import nox


@nox.session(python=["3.6", "3.7", "3.8", "3.9", "3.10", "3.12"],reuse_venv=True)
def run(session):
    session.env["DUT"] = "tb"
    session.env['SIM'] = "verilator"
    # session.env["SIM"] = "icarus"
    session.env["TIMEPREC"] = "1ps"
    session.env["TIMEUNIT"] = "1ns"
    session.install(
        "pytest",
        "pytest-sugar",
        "pytest-xdist",
        "pytest-split",
        "cocotb >= 1.8.0",
        "cocotb-test",
        "cocotbext-waves >= 0.1.9",
    )
    session.run(
        "pytest",
        "-rP",
        "-n",
        "auto",
        *session.posargs
    )
