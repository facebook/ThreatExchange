#!/usr/bin/ruby
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# See README.md for context.

# ----------------------------------------------------------------
def dkvpline2map(line)
  map = {}
  line.split(',').each do |pair|
    (k, v) = pair.split('=', 2)
    map[k] = v
  end
  map
end

# ----------------------------------------------------------------
puts "<html>"
puts "<body>"

width = 10
idx = 0
ARGF.each do |line|
  idx += 1
  map = dkvpline2map(line.chomp)
  filename = map['filename']
  q = map['quality']

  puts "<br/>" if idx % width == 0
  puts "<img height=200 src=\"#{filename}\" title=\"#{filename} q=#{q}\" " +
    "alt=\"#{filename} q=#{q}\">"
end

puts "</body>"
puts "</html>"
