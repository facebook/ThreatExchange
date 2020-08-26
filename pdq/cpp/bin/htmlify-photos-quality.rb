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

numper = 8
i = 0
ARGF.each do |line|
  map = dkvpline2map(line.chomp)
  filename = map['filename']
  q = map['quality']

  if (i % numper) == 0
    puts "<br/>"
  end
  puts "<img height=200 src=\"#{filename}\" title=\"#{filename}\" " +
    "alt=\"#{filename}\">&nbsp;q=#{q}"
  i += 1
end

puts "</body>"
puts "</html>"
