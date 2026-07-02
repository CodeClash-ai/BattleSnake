#!/bin/sh
bundle install --quiet
exec bundle exec rackup -p "${PORT:-8000}" -o 0.0.0.0
