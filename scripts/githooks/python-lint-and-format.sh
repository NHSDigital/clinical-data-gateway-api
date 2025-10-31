#!/bin/bash
set -e

ruff format --diff
ruff check
