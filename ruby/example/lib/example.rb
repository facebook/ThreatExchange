def parse(dataset)
  printf "\nResults: \n"
  if dataset.kind_of?(String)
    puts dataset
  else
    unless dataset.empty?
      dataset.each { |data| p data }
    else
      puts 'No data found.'
    end
  end
end

def banner(header)
  puts '-'*80
  puts header
  puts '-'*80
end

def spinner(fps=30)
  chars = %w[| / - \\]
  delay = 1.0/fps
  iter = 0
  spinner = Thread.new do
    while iter do
      print chars[(iter+=1) % chars.length]
      sleep delay
      print "\b"
    end
  end
  yield.tap{       
    iter = false 
    spinner.join   
  }                
end