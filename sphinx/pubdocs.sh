#!/bin/bash
make html
cp build/html/* ../docs
cp -r build/html/_static ../docs
cp -r build/html/_sources ../docs
