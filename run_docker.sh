#!/bin/bash
docker run -it --rm --name rtldev -v $(pwd):/temp/ -w /temp/ aignacio/rtldev bash
