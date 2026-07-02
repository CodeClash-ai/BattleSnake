#!/bin/sh
# Build & launch the real esproso Go server on $PORT (upstream binds :5001).
b=/tmp/esproso_build; rm -rf "$b"; cp -r esproso_src "$b"
sed -i "s/:5001/:${PORT:-8000}/" "$b/main.go"
cd "$b" && go build -o bot . && exec ./bot
