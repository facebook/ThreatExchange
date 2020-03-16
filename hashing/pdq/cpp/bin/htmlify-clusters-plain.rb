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
clusters = {}

ARGF.each do |line|
  map = dkvpline2map(line.chomp)

  if map['clidx'] != nil
    clidx = map['clidx']
    filename = map['filename']
    d = map['d']
    q = map['quality']
    if clusters[clidx].nil?
      clusters[clidx] = []
    end
    clusters[clidx] << [filename, d, q]
  end
end

# ----------------------------------------------------------------
puts "<html>"
puts "<body>"

clusters.each do |clidx, pairs|
  puts "<br/>"

  pairs.each do |pair|
    (filename, d, q) = pair
    puts "<img height=200 src=\"#{filename}\" title=\"#{filename}\" " +
      "alt=\"#{filename} d=#{d} q=#{q}\">"
  end
end

puts "</body>"
puts "</html>"
