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
def hamming_norm_on_nybble(h)
  nybble_norm_lookup_table = [
    0, # 00
    1, # 01
    1, # 02
    2, # 03
    1, # 04
    2, # 05
    2, # 06
    3, # 07
    1, # 08
    2, # 09
    2, # 0a
    3, # 0b
    2, # 0c
    3, # 0d
    3, # 0e
    4 # 0f
  ]
  nybble_norm_lookup_table[h]
end

# ----------------------------------------------------------------
def hamming_distance_on_hashes(a, b)
  ac = a.chars
  bc = b.chars
  m = ac.length
  n = bc.length
  i = 0
  d = 0
  while i < m && i < n do
    u = ac[i].to_i(16)
    v = bc[i].to_i(16)
    d += hamming_norm_on_nybble(u ^ v)
    i += 1
  end
  d
end

# ----------------------------------------------------------------
# For copydays/labelme/etc. naming conventions
def basename2(path)
  a = File.basename File.dirname path
  b = File.basename path
  a + '/' + b
end

# ----------------------------------------------------------------
filename1 = ARGV[0]
filename2 = ARGV[1]
lines1 = File.readlines(filename1).collect { |line| line.chomp }
lines2 = File.readlines(filename2).collect { |line| line.chomp }

m = lines1.length
n = lines2.length
i = 0

# ----------------------------------------------------------------
puts "<html>"
puts "<body>"

while i < m && i < n do
  map1 = dkvpline2map(lines1[i])
  map2 = dkvpline2map(lines2[i])

  filename1 = map1['filename']
  filename2 = map2['filename']

  hash1 = map1['hash']
  hash2 = map2['hash']

  d = hamming_distance_on_hashes(hash1, hash2)

  puts "<br/>"
  puts "<img height=200 src=\"#{filename1}\" title=\"#{filename1}\" " +
    "alt=\"#{filename1}\"> #{basename2 filename1}"
  puts "<img height=200 src=\"#{filename2}\" title=\"#{filename2}\" " +
    "alt=\"#{filename2}\"> #{basename2 filename2} d=#{d}"

  i += 1
end

puts "</body>"
puts "</html>"
