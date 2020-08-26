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

ARGF.each do |line|
  map = dkvpline2map(line.chomp)
  filename = map['filename']
  q = map['quality']

  puts "<br/>"
  puts "<img height=200 src=\"#{filename}\" title=\"#{filename}\" " +
    "alt=\"#{filename}\"> #{filename} q=#{q}"
end

puts "</body>"
puts "</html>"
