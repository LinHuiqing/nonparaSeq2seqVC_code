#!/bin/bash

find ./outdir -type f -printf '%T@ %p\n' | sort -k1,1nr | head -5
