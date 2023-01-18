##!/usr/bin/ruby

# ================================================================
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# ================================================================
# Example technique for retrieving all descriptors with a given tag from
# ThreatExchange.
#
# Notes:
#
# * We use the tagged_objects endpoint to fetch IDs of all descriptors. This
#   endpoint doesn't return all desired metadata fields, so we use it as a
#   quick map from tag ID to list of descriptor IDs. This is relatively quick.
#
# * Then for each resulting descriptor ID we do a query for all fields
#   associated with that ID. This is relatively slow, but batching multiple
#   IDs per query helps a lot.
#
# Please see README.md for example usages.
# ================================================================

# ThreatExchange dependencies
require 'TENet.rb'

# ================================================================
# MAIN COMMAND-LINE ENTRY POINT
class MainHandler

  # ----------------------------------------------------------------
  # General rule about exit-codes and output streams:
  # * When help was asked for: print to stdout and exit 0.
  # * When unacceptable command-line syntax was provided: print to stderr and exit 1.
  def usage(exitCode)
    stream =  exitCode == 0 ? $stdout : $stderr
  output = <<-EOF
Usage: te-tag-query [options] {verb} {verb arguments}
Downloads descriptors in bulk from ThreatExchange, given
either a tag name or a list of IDs one per line on standard input.

Options:
  -h|--help      Show detailed help.
  --list-verbs   Show a list of supported verbs.
  -q|--quiet     Only print IDs/descriptors output with no narrative.
  -v|--verbose   Print IDs/descriptors output along with narrative.
  -s|--show-urls Print URLs used for queries, before executing them.
  -a|--app-token-env-name {...} Name of app-token environment variable.
                 Defaults to "TX_ACCESS_TOKEN".
  -b|--te-base-url {...} Defaults to "#{ThreatExchange::TENet::DEFAULT_TE_BASE_URL}"

EOF

    stream.puts output
    SubcommandHandlerFactory.listVerbs()
    exit(exitCode)
  end # MainHandler usage

  # ----------------------------------------------------------------
  # We don't use getopt, intentionally so. It doesn't know about our subcommand
  # structure.
  #
  # * ruby TETagQuery.rb -h
  #   We want the -h handled by main().
  # * ruby TETagQuery.rb submit -h
  #   We want the -h handled by submit().
  # * ruby TETagQuery.rb -s submit -i ... -t ...
  #   We want the -s handled by main(), and -i/-t/etc handled by submit().
  def handle(args)
    options = self.getDefaultOptions()
    subcommandHandlerFactory = SubcommandHandlerFactory.new

    # Rememmber that ARGV does not include the program name ($0) in Ruby.
    # This is like Java; unlike Python and C/C++/Go.
    loop do
      break if args.length == 0
      break unless args[0][0] == '-'
      option = args.shift

      if option == '-h'
        self.usage(0)
      elsif option == '--help'
        self.usage(0)
      elsif option == '-l' || option == '--list-verbs'
        SubcommandHandlerFactory.listVerbs()
        exit(0)

      elsif option == '-v' || option == '--verbose'
        options['verbose'] = true
      elsif option == '-q' || option == '--quiet'
        options['verbose'] = false
      elsif option == '-s' || option == '--show-urls'
        options['showURLs'] = true

      elsif option == '-a' || option == '--app-token-env-name'
        self.usage(1) unless args.length >= 1
        options['accessTokenEnvName'] = args.shift
      elsif option == '-b' || option == '--base-te-url'
        self.usage(1) unless args.length >= 1
        options['baseTEURL'] = args.shift

      else
        $stderr.puts "#{$0}: unrecognized  option #{option}"
        exit 1
      end
    end

    if args.length < 1
      self.usage(1)
    end
    verbName = args.shift
    verbArgs = args

    # Endpoint setup common to all verbs
    ThreatExchange::TENet::setAppTokenFromEnvName(options['accessTokenEnvName'])
    baseTEURL = options['baseTEURL']
    unless baseTEURL.nil?
      ThreatExchange::TENet::setTEBaseURL(baseTEURL)
    end
    ThreatExchange::TENet::setAppTokenFromEnvName(options['accessTokenEnvName'])

    subcommandHandler = subcommandHandlerFactory.create(verbName)

    if subcommandHandler.nil?
      $stderr.puts "#{$0}: unrecognized verb \"#{verbName}\""
      exit 1
    end

    subcommandHandler.handle(args, options)

  end # MainHandler.handle

  # ----------------------------------------------------------------
  def getDefaultOptions
    return {
      'verbose'                  => false,
      'showURLs'                 => false,
      'pageSize'                 => 10,

      'accessTokenEnvName'       => 'TX_ACCESS_TOKEN',
      # Use default from Constants.rb unless overridden
      'baseTEURL'                => nil,
    }
  end # MainHandler.getDefaultOptions
end # class MainHandler

# ================================================================
# This is just a subcommand looker-upper. We use n subcommands within one
# script, instead of shipping n scripts.
class SubcommandHandlerFactory
  VERB_NAMES = {
    'look-up-tag-id' => 'look-up-tag-id',
    'tag-to-ids'     => 'tag-to-ids',
    'ids-to-details' => 'ids-to-details',
    'tag-to-details' => 'tag-to-details',
    'paginate'       => 'paginate',
    'submit'         => 'submit',
    'update'         => 'update',
    'copy'           => 'copy',
  }

  # Static method
  def self.listVerbs()
    puts "Verbs:"
    VERB_NAMES.each do |key, _value|
      puts "  #{key}"
    end
  end

  def create(verbName)
    if verbName == VERB_NAMES['look-up-tag-id']
      return LookUpTagIDHandler.new(verbName)
    elsif verbName == VERB_NAMES['tag-to-ids']
      return TagToIDsHandler.new(verbName)
    elsif verbName == VERB_NAMES['ids-to-details']
      return IDsToDetailsHandler.new(verbName)
    elsif verbName == VERB_NAMES['tag-to-details']
      return TagToDetailsHandler.new(verbName)
    elsif verbName == VERB_NAMES['paginate']
      return PaginateHandler.new(verbName)
    elsif verbName == VERB_NAMES['submit']
      return SubmitHandler.new(verbName)
    elsif verbName == VERB_NAMES['update']
      return UpdateHandler.new(verbName)
    elsif verbName == VERB_NAMES['copy']
      return CopyHandler.new(verbName)
    else
      return nil
    end
  end
end

# ================================================================
# Code-reuse for all subcommand handlers.
class SubcommandHandler
  def initialize(verbName)
    @verbName = verbName
  end
end

# ================================================================
class LookUpTagIDHandler < SubcommandHandler
  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  # ----------------------------------------------------------------
  def usage(exitCode)
    stream =  exitCode == 0 ? $stdout : $stderr
  output = <<-EOF
Usage: #{$0} #{@verbName} {one or more tag names}
EOF
    stream.puts output
    exit(exitCode)
  end

  def handle(args, options)
    if args.length >= 1
      if args[0] == '-h' || args[0] == '--help'
        self.usage(0)
      end
    end

    if args.length != 1
      self.usage(1)
    end

    tagName = args[0]
    tag_id = ThreatExchange::TENet::getTagIDFromName(
      tagName,
      showURLs: options['showURLs'],
    )
    puts tag_id
  end
end

# ================================================================
class TagToIDsHandler < SubcommandHandler
  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  def usage(exitCode)
    stream =  exitCode == 0 ? $stdout : $stderr
    output = <<-EOF
Usage: #{$0} #{@verbName} [options] {tag name}
Options:
--tagged-since {x}
--tagged-until {x}
--page-size {x}
The \"tagged-since\" or \"tagged-until\" parameter is any supported by ThreatExchange,
e.g. seconds since the epoch, or "-1hour", or "-1day", etc.
EOF
    stream.puts output
    exit(exitCode)
  end

  def handle(args, options)

    options['includeIndicatorInOutput'] = true
    options['pageSize'] = 10

    loop do
      break if args.length == 0
      break unless args[0][0] == '-'
      option = args.shift

      if option == '-h'
        self.usage(0)
      elsif option == '--help'
        self.usage(0)

      elsif option == '--tagged-since'
        self.usage(1) unless args.length >= 1
        options['taggedSince'] = args.shift;
      elsif option == '--tagged-until'
        self.usage(1) unless args.length >= 1
        options['taggedUntil'] = args.shift;

      elsif option == '--page-size'
        self.usage(1) unless args.length >= 1
        options['pageSize'] = args.shift;

      else
        $stderr.puts "#{$0} #{@verbName}: unrecognized  option #{option}"
        exit 1
      end
    end

    if args.length != 1
      self.usage(1)
    end
    tagName = args[0]

    # Step 1: tag text to ID
    # Step 2: tag ID to descriptor IDs, paginated
    # Step 3: descriptor IDs to descriptor details, paginated

    tag_id = ThreatExchange::TENet::getTagIDFromName(
      tagName,
      showURLs: options['showURLs'],
    )

    idProcessor = lambda do |idBatch|
      idBatch.each do |id|
        puts id
      end
    end

    ThreatExchange::TENet::processDescriptorIDsByTagID(
      tag_id,
      verbose: options['verbose'],
      showURLs: options['showURLs'],
      taggedSince: options['taggedSince'],
      taggedUntil: options['taggedUntil'],
      pageSize: options['pageSize'],
      idProcessor: idProcessor)

  end
end

# ================================================================
class IDsToDetailsHandler < SubcommandHandler
  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  def usage(exitCode)
    stream =  exitCode == 0 ? $stdout : $stderr
    output = <<-EOF
Usage: #{$0} #{@verbName} [options] [IDs]
Options:
--no-print-indicator -- Don't print the indicator to the terminal
Please supply IDs either one line at a time on standard input, or on the command line
after the options.
EOF
    stream.puts output
    exit(exitCode)
  end

  def handle(args, options)
    options['includeIndicatorInOutput'] = true
    options['pageSize'] = 10

    loop do
      break if args.length == 0
      break unless args[0][0] == '-'
      option = args.shift

      if option == '-h'
        self.usage(0)
      elsif option == '--help'
        self.usage(0)

      elsif option == '--tagged-since'
        self.usage(1) unless args.length >= 1
        options['taggedSince'] = args.shift;
      elsif option == '--tagged-until'
        self.usage(1) unless args.length >= 1
        options['taggedUntil'] = args.shift;

      elsif option == '--page-size'
        self.usage(1) unless args.length >= 1
        options['pageSize'] = args.shift;
      elsif option == '--no-print-indicator'
        self.usage(1) unless args.length >= 1
        options['includeIndicatorInOutput'] = false

      else
        $stderr.puts "#{$0} #{@verbName}: unrecognized  option #{option}"
        exit 1
      end
    end

    ids = []
    if args.length > 0
      ids = args
    else
      $stdin.readlines.each do |line|
        id = line.chomp
        ids.push(id)
      end
    end

    ids.each do |id|
      idBatch = [id]
      descriptors = ThreatExchange::TENet.getInfoForIDs(
        idBatch,
        verbose: options['verbose'],
        showURLs: options['showURLs'],
        includeIndicatorInOutput: options['includeIndicatorInOutput'])
      descriptors.each do |descriptor|
        # Stub processing -- one would perhaps integrate with one's own system
        puts descriptor.to_json
      end
    end

  end
end

# ================================================================
class TagToDetailsHandler < SubcommandHandler
  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  def usage(exitCode)
    stream =  exitCode == 0 ? $stdout : $stderr
    output = <<-EOF
Usage: #{$0} #{@verbName} [options] {tag name}
Options:
--tagged-since {x}
--tagged-until {x}
--created-since {x}
--created-until {x}

  Timestamp options for all four are epoch seconds, various datetime formats
  including "2020-12-34T56:07:08+0900", and time-deltas like "-5minutes",
  "-3hours", "-1week".

  At most one of --tagged-since and --created-since can be specified; likewise
  --tagged-until and --created-until.

--page-size {x}
--no-print-indicator -- Don't print the indicator to the terminal
The \"tagged-since\" or \"tagged-until\" parameter is any supported by ThreatExchange,
e.g. seconds since the epoch, or "-1hour", or "-1day", etc.
EOF
    stream.puts output
    exit(exitCode)
  end

  def handle(args, options)
    options['includeIndicatorInOutput'] = true
    options['pageSize'] = 10

    loop do
      break if args.length == 0
      break unless args[0][0] == '-'
      option = args.shift

      if option == '-h'
        self.usage(0)
      elsif option == '--help'
        self.usage(0)

      elsif option == '--tagged-since'
        self.usage(1) unless args.length >= 1
        options['taggedSince'] = args.shift;
      elsif option == '--tagged-until'
        self.usage(1) unless args.length >= 1
        options['taggedUntil'] = args.shift;

      elsif option == '--created-since'
        self.usage(1) unless args.length >= 1
        options['createdSince'] = args.shift;
      elsif option == '--created-until'
        self.usage(1) unless args.length >= 1
        options['createdUntil'] = args.shift;

      elsif option == '--page-size'
        self.usage(1) unless args.length >= 1
        options['pageSize'] = args.shift;
      elsif option == '--no-print-indicator'
        self.usage(1) unless args.length >= 1
        options['includeIndicatorInOutput'] = false

      else
        $stderr.puts "#{$0} #{@verbName}: unrecognized  option #{option}"
        exit 1
      end
    end

    # Tagged-at filtering is done server-side -- the TE /tagged_objects
    # endpoint filters by tagged-at timestamps on the graph edges from tag to
    # descriptor ID. An implementation detail of /tagged_objects is that it
    # only yields abstract IDs; descriptor IDs to details are a separate pass
    # in this design.
    #
    # This means that if the user wants to filter on created-at:
    # * We have the invariants that created-at <= tagged-at, and tagged-at <= now.
    # * If they ask for created-since t, we query the server for tagged-since t
    #   (which overfetches) and then we filter client-side.
    # * If they as for created-until t, we query the server for tagged-until now
    #   (which overfetches) and then we filter client-side.
    options['createdSinceEpochSeconds'] = nil
    options['createdUntilEpochSeconds'] = nil
    if options['createdSince'] != nil
      if options['taggedSince'] != nil
        $stderr.puts "#{$0} #{@verbName}: Please specify at most one of --tagged-since and --created-since."
        exit 1
      end
      options['taggedSince'] = options['createdSince']
      options['createdSinceEpochSeconds'] = ThreatExchange::TENet::parseTimeStringToEpochSeconds(options['createdSince'])
    end
    if options['createdUntil'] != nil
      if options['taggedUntil'] != nil
        $stderr.puts "#{$0} #{@verbName}: Please specify at most one of --tagged-until and --created-until."
        exit 1
      end
      # keep options['taggedUntil'] = nil
      options['createdUntilEpochSeconds'] = ThreatExchange::TENet::parseTimeStringToEpochSeconds(options['createdUntil'])
    end

    if args.length != 1
      self.usage(1)
    end
    tagName = args[0]

    # Step 1: tag text to ID
    # Step 2: tag ID to descriptor IDs, paginated
    # Step 3: descriptor IDs to descriptor details, paginated

    puts("TAG_NAME=#{tagName}")
    tag_id = ThreatExchange::TENet::getTagIDFromName(
      tagName,
      showURLs: options['showURLs'],
    )

    idProcessor = lambda do |idBatch|
      descriptors = ThreatExchange::TENet.getInfoForIDs(
        idBatch,
        verbose: options['verbose'],
        showURLs: options['showURLs'],
        includeIndicatorInOutput: options['includeIndicatorInOutput'])

      createdSinceEpochSeconds = options['createdSinceEpochSeconds']
      createdUntilEpochSeconds = options['createdUntilEpochSeconds']

      descriptors.each do |descriptor|
        added_on = descriptor['added_on']
        if added_on.nil?
          puts("WTFA")
          puts(descriptor)
          puts("WTFB")
        end
        descriptorCreatedAtEpochSeconds = ThreatExchange::TENet::parseTimeStringToEpochSeconds(added_on)
        if createdSinceEpochSeconds != nil
          if descriptorCreatedAtEpochSeconds < createdSinceEpochSeconds
            next
          end
        end
        if createdUntilEpochSeconds != nil
          if descriptorCreatedAtEpochSeconds > createdUntilEpochSeconds
            next
          end
        end

        # Stub processing -- one would perhaps integrate with one's own system
        puts descriptor.to_json
      end
    end

    ThreatExchange::TENet::processDescriptorIDsByTagID(
      tag_id,
      verbose: options['verbose'],
      showURLs: options['showURLs'],
      taggedSince: options['taggedSince'],
      taggedUntil: options['taggedUntil'],
      pageSize: options['pageSize'],
      includeIndicatorInOutput: options['includeIndicatorInOutput'],
      idProcessor: idProcessor)
  end
end

# ================================================================
class PaginateHandler < SubcommandHandler
  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  def usage(exitCode)
    stream =  exitCode == 0 ? $stdout : $stderr
  output = <<-EOF
Usage: #{$0} #{@verbName} {URL}
Curls the URL, JSON-dumps the return value's data blob, then curls
the next-page URL and repeats until there are no more pages.
EOF

    stream.puts output
    exit(exitCode)
  end

  def handle(args, options)
    if args.length >= 1
      if args[0] == '-h' || args[0] == '--help'
        self.usage(0)
      end
    end

    if args.length != 1
      self.usage(1)
    end
    startURL = args[0]
    nextURL = startURL

    loop do
      if (options['showURLs'])
        puts "URL:"
        puts nextURL
      end

      responseString = Net::HTTP.get(URI(nextURL))
      responseObject = JSON.parse(responseString)
      dataObject = responseObject['data']
      pagingObject = responseObject['paging']
      if pagingObject.nil?
        nextURL = nil
      else
        nextURL = pagingObject['next']
      end

      puts dataObject.to_json

      break if nextURL.nil?
    end
  end
end

# ================================================================
# Some code-reuse for all subcommand handlers that do POSTs.
class AbstractPostSubcommandHandler < SubcommandHandler
  # These allow us to customize the mostly-overlapping usage() method
  POSTER_NAME_SUBMIT = 'submit'
  POSTER_NAME_UPDATE = 'update'
  POSTER_NAME_COPY   = 'copy'
  attr_accessor :POSTER_NAME_SUBMIT, :POSTER_NAME_UPDATE, :POSTER_NAME_COPY

  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  # ----------------------------------------------------------------
  protected
  def commonPosterUsage(exitCode, posterName)
    if posterName.nil?
      raise "#{$0}: internal coding error in commonPosterUsage"
    end

    stream =  exitCode == 0 ? $stdout : $stderr
    output1 = <<-EOF1
Usage: #{$0} #{@verbName} [options]
EOF1

    output2 = nil
    output3 = nil
    output4 = nil
    output5 = nil

    output2 = nil
    if posterName == POSTER_NAME_SUBMIT
      output2 = <<-EOF2s
Uploads a threat descriptor with the specified values.
On repost (with same indicator text/type and app ID), updates changed fields.

Required:
-i|--indicator {...}   The indicator text: hash/URL/etc.
-I                     Take indicator text from standard input, one per line.
Exactly one of -i or -I is required.
-t|--type {...}
EOF2s
    end
    if posterName == POSTER_NAME_UPDATE
      output2 = <<-EOF2u
Updates specified attributes on an existing threat descriptor.

Required:
-n {...}               ID of descriptor to be edited. Must already exist.
-N                     Take descriptor IDs from standard input, one per line.
Exactly one of -n or -N is required.
EOF2u
    end

    output3 = <<-EOF3
-d|--description {...}
-l|--share-level {...}
-p|--privacy-type {...}
-y|--severity {...}

Optional:
-h|--help
--dry-run
-m|--privacy-members {...} If privacy-type is HAS_WHITELIST these must be
                       comma-delimited app IDs. If privacy-type is
                       HAS_PRIVACY_GROUP these must be comma-delimited
                       privacy-group IDs.
--tags {...}           Comma-delimited. Overwrites on repost.
EOF3

    output4=nil
    if posterName == POSTER_NAME_UPDATE
      output3 = <<-EOF4u
--add-tags {...}       Comma-delimited. Adds these on repost.
--remove-tags {...}    Comma-delimited. Removes these on repost.
EOF4u
    end

    output5 = <<-EOF5
--related-ids-for-upload {...} Comma-delimited. IDs of descriptors (which must
                       already exist) to relate the new descriptor to.
--related-triples-json-for-upload {...} Alternate to --related-ids-for-upload.
                       Here you can uniquely the relate-to descriptors by their
                       owner ID / indicator-type / indicator-text, rather than
                       by their IDs. See README.md for an example.

--reactions-to-add {...}    Example for add/remove: INGESTED,IN_REVIEW
--reactions-to-remove {...}

--confidence {...}
-s|--status {...}
-r|--review-status {...}
--first-active {...}
--last-active {...}
--expired-on {...}

Please see the following for allowed values in all enumerated types except reactions:
https://developers.facebook.com/docs/threat-exchange/reference/submitting

Please also see:
https://developers.facebook.com/docs/threat-exchange/reference/editing

Please see the following for enumerated types in reactions:
See also https://developers.facebook.com/docs/threat-exchange/reference/reacting
EOF5

    stream.puts(output1)
    stream.puts(output2) unless output2.nil?
    stream.puts(output3)
    stream.puts(output4) unless output4.nil?
    stream.puts(output5)

    exit(exitCode)
  end


  # ----------------------------------------------------------------
  # For CLI-parsing
  #
  # Input:
  # * option such as '-d'
  # * remaining args as string-list
  # * postParams dict
  #
  # Output:
  # * boolean whether the option was recognized
  # * args may be shifted if the option was recognized and successfully handled
  #
  # Modified by reference:
  # * postParams dict modified by reference if the option was recognized and
  #   successfully handled
  def commonPosterOptionCheck(option, args, postParams)
    # Local keystroke-saver for this enum
    names = ThreatExchange::TENet::POST_PARAM_NAMES

    handled = true

    if option == '-d' || option == '--description'
      self.usage(1) unless args.length >= 1
      postParams[names[:description]] = args.shift;

    elsif option == '-l' || option == '--share-level'
      self.usage(1) unless args.length >= 1
      postParams[names[:share_level]] = args.shift;
    elsif option == '-p' || option == '--privacy-type'
      self.usage(1) unless args.length >= 1
      postParams[names[:privacy_type]] = args.shift;
    elsif option == '-m' || option == '--privacy-members'
      self.usage(1) unless args.length >= 1
      postParams[names[:privacy_members]] = args.shift;

    elsif option == '-s' || option == '--status'
      self.usage(1) unless args.length >= 1
      postParams[names[:status]] = args.shift;
    elsif option == '-r' || option == '--review-status'
      self.usage(1) unless args.length >= 1
      postParams[names[:review_status]] = args.shift;
    elsif option == '-y' || option == '--severity'
      self.usage(1) unless args.length >= 1
      postParams[names[:severity]] = args.shift;
    elsif option == '-c' || option == '--confidence'
      self.usage(1) unless args.length >= 1
      postParams[names[:confidence]] = args.shift;

    elsif option == '--related-ids-for-upload'
      self.usage(1) unless args.length >= 1
      postParams[names[:related_ids_for_upload]] = args.shift;
    elsif option == '--related-triples-for-upload-as-json'
      self.usage(1) unless args.length >= 1
      postParams[names[:related_triples_for_upload_as_json]] = args.shift;

    elsif option == '--reactions-to-add'
      self.usage(1) unless args.length >= 1
      postParams[names[:reactions]] = args.shift;
    elsif option == '--reactions-to-remove'
      self.usage(1) unless args.length >= 1
      postParams[names[:reactions_to_remove]] = args.shift;

    elsif option == '--first-active'
      self.usage(1) unless args.length >= 1
      postParams[names[:first_active]] = args.shift;
    elsif option == '--last-active'
      self.usage(1) unless args.length >= 1
      postParams[names[:last]] = args.shift;
    elsif option == '--expired-on'
      self.usage(1) unless args.length >= 1
      postParams[names[:expired_on]] = args.shift;

    else
      handled = false
    end

    return [handled, args]
  end
end

# ================================================================
class SubmitHandler < AbstractPostSubcommandHandler
  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  # ----------------------------------------------------------------
  def usage(exitCode)
    self.commonPosterUsage(exitCode, POSTER_NAME_SUBMIT)
  end

  # ----------------------------------------------------------------
  def handle(args, options)

    options['dryRun'] = false;
    options['indicatorTextFromStdin'] = false;

    postParams = {}

    # Local keystroke-saver for this enum
    names = ThreatExchange::TENet::POST_PARAM_NAMES

    loop do
      break if args.length == 0
      break unless args[0][0] == '-'
      option = args.shift

      if option == '-h'
        self.usage(0)
      elsif option == '--help'
        self.usage(0)

      elsif option == '--dry-run'
        options['dryRun'] = true

      elsif option == '-I'
        options['indicatorTextFromStdin'] = true;
      elsif option == '-i' || option == '--indicator'
        self.usage(1) unless args.length >= 1
        postParams[names[:indicator]] = args.shift;

      elsif option == '-t' || option == '--type'
        self.usage(1) unless args.length >= 1
        postParams[names[:type]] = args.shift;

      elsif option == '--tags'
        self.usage(1) unless args.length >= 1
        postParams[names[:tags]] = args.shift;

      else
        handled, args = self.commonPosterOptionCheck(option, args, postParams)
        if not handled
          $stderr.puts "#{$0} #{@verbName}: unrecognized  option #{option}"
          exit 1
        end
      end
    end

    if args.length > 0
      $stderr.puts "#{$0} #{@verbName}: extraneous argument(s) \"#{args.join(' ')}\"."
      exit 1
    end

    if options['indicatorTextFromStdin']
      unless postParams[names[:indicator]].nil?
        $stderr.puts "#{$0} #{@verbName}: only one of -I and -i must be supplied."
        exit 1
      end

      $stdin.readlines.each do |line|
        postParams[names[:indicator]] = line.chomp
        self.submitSingle(
          postParams,
          verbose: options['verbose'],
          showURLs: options['showURLs'],
          dryRun: options['dryRun'],
        )
      end
    else
      if postParams[names[:indicator]].nil?
        $stderr.puts "#{$0} #{@verbName}: exactly one of -I and -i must be supplied."
        exit 1
      end
      self.submitSingle(
        postParams,
        verbose: options['verbose'],
        showURLs: options['showURLs'],
        dryRun: options['dryRun'],
      )
    end

  end # SubmitHandler.handle

  # ----------------------------------------------------------------
  def submitSingle(
    postParams,
    verbose: false,
    showURLs: false,
    dryRun: false)

    validationErrorMessage, response_body, response_code = ThreatExchange::TENet::submitThreatDescriptor(
      postParams,
      showURLs: showURLs,
      dryRun: dryRun)

    unless validationErrorMessage.nil?
      $stderr.puts validationErrorMessage
      exit 1
    end

    puts response_body

    if response_code != 200
      exit 1
    end
  end # SubmitHandler.submitSingle
end # class SubmitHandler

# ================================================================
# NOTE: SubmitHandler and UpdateHandler have a lot of the same code but also
# several differences. I found it simpler (albeit more verbose) to duplicate
# rather than do an abstract-and-override refactor.

class UpdateHandler < AbstractPostSubcommandHandler
  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  # ----------------------------------------------------------------
  def usage(exitCode)
    self.commonPosterUsage(exitCode, POSTER_NAME_UPDATE)
  end

  # ----------------------------------------------------------------
  def handle(args, options)

    options['dryRun'] = false;
    options['descriptorIDsFromStdin'] = false;

    postParams = {}

    # Local keystroke-saver for this enum
    names = ThreatExchange::TENet::POST_PARAM_NAMES

    loop do
      break if args.length == 0
      break unless args[0][0] == '-'
      option = args.shift

      if option == '-h'
        self.usage(0)
      elsif option == '--help'
        self.usage(0)

      elsif option == '--dry-run'
        options['dryRun'] = true

      elsif option == '-N'
        options['descriptorIDsFromStdin'] = true;
      elsif option == '-n'
        self.usage(1) unless args.length >= 1
        postParams[names[:descriptor_id]] = args.shift;

      elsif option == '--tags'
        self.usage(1) unless args.length >= 1
        postParams[names[:tags]] = args.shift;
      elsif option == '--add-tags'
        self.usage(1) unless args.length >= 1
        postParams[names[:add_tags]] = args.shift;
      elsif option == '--remove-tags'
        self.usage(1) unless args.length >= 1
        postParams[names[:remove_tags]] = args.shift;

      else
        handled, args = self.commonPosterOptionCheck(option, args, postParams)
        if not handled
          $stderr.puts "#{$0} #{@verbName}: unrecognized  option #{option}"
          exit 1
        end
      end
    end

    if args.length > 0
      $stderr.puts "#{$0} #{@verbName}: extraneous argument(s) \"#{args.join(' ')}\"."
      exit 1
    end

    if options['descriptorIDsFromStdin']
      unless postParams[names[:descriptor_id]].nil?
        $stderr.puts "#{$0} #{@verbName}: only one of -N and -n must be supplied."
        exit 1
      end

      $stdin.readlines.each do |line|
        postParams[names[:descriptor_id]] = line.chomp
        self.updateSingle(
          postParams,
          verbose: options['verbose'],
          showURLs: options['showURLs'],
          dryRun: options['dryRun'],
        )
      end
    else
      if postParams[names[:descriptor_id]].nil?
        $stderr.puts "#{$0} #{@verbName}: exactly one of -N and -n must be supplied."
        exit 1
      end
      self.updateSingle(
        postParams,
        verbose: options['verbose'],
        showURLs: options['showURLs'],
        dryRun: options['dryRun'],
      )
    end
  end # UpdateHandler.handle

  # ----------------------------------------------------------------
  def updateSingle(
    postParams,
    verbose: false,
    showURLs: false,
    dryRun: false)

    validationErrorMessage, response_body, response_code = ThreatExchange::TENet::updateThreatDescriptor(
      postParams,
      showURLs: showURLs,
      dryRun: dryRun)

    unless validationErrorMessage.nil?
      $stderr.puts validationErrorMessage
      exit 1
    end

    puts response_body

    if response_code != "200"
      exit 1
    end
  end # UpdateHandler.updateSingle
end # class UpdateHandler

# ----------------------------------------------------------------
class CopyHandler < AbstractPostSubcommandHandler
  # ----------------------------------------------------------------
  def initialize(verbName)
    super(verbName)
  end

  # ----------------------------------------------------------------
  def usage(exitCode)
    self.commonPosterUsage(exitCode, POSTER_NAME_COPY)
  end

  # ----------------------------------------------------------------
  def handle(args, options)

    options['dryRun'] = false;
    options['descriptorIDsFromStdin'] = false;

    postParams = {}

    # Local keystroke-saver for this enum
    names = ThreatExchange::TENet::POST_PARAM_NAMES

    loop do
      break if args.length == 0
      break unless args[0][0] == '-'
      option = args.shift

      if option == '-h'
        self.usage(0)
      elsif option == '--help'
        self.usage(0)

      elsif option == '--dry-run'
        options['dryRun'] = true

      elsif option == '-N'
        options['descriptorIDsFromStdin'] = true;
      elsif option == '-n'
        self.usage(1) unless args.length >= 1
        postParams[names[:descriptor_id]] = args.shift;

      elsif option == '-i' || option == '--indicator'
        self.usage(1) unless args.length >= 1
        postParams[names[:indicator]] = args.shift;

      elsif option == '-t' || option == '--type'
        self.usage(1) unless args.length >= 1
        postParams[names[:type]] = args.shift;

      elsif option == '--tags'
        self.usage(1) unless args.length >= 1
        postParams[names[:tags]] = args.shift;

      else
        handled, args = self.commonPosterOptionCheck(option, args, postParams)
        if not handled
          $stderr.puts "#{$0} #{@verbName}: unrecognized  option #{option}"
          exit 1
        end
      end
    end

    if args.length > 0
      $stderr.puts "#{$0} #{@verbName}: extraneous argument(s) \"#{args.join(' ')}\"."
      exit 1
    end

    if options['descriptorIDsFromStdin']
      unless postParams[names[:descriptor_id]].nil?
        $stderr.puts "#{$0} #{@verbName}: only one of -N and -n must be supplied."
        exit 1
      end

      $stdin.readlines.each do |line|
        postParams[names[:descriptor_id]] = line.chomp
        self.copySingle(
          postParams,
          verbose: options['verbose'],
          showURLs: options['showURLs'],
          dryRun: options['dryRun'],
        )
      end
    else
      if postParams[names[:descriptor_id]].nil?
        $stderr.puts "#{$0} #{@verbName}: exactly one of -N and -n must be supplied."
        exit 1
      end
      self.copySingle(
        postParams,
        verbose: options['verbose'],
        showURLs: options['showURLs'],
        dryRun: options['dryRun'],
      )
    end
  end # CopyHandler.handle

  # ----------------------------------------------------------------
  def copySingle(
    postParams,
    verbose: false,
    showURLs: false,
    dryRun: false)

    validationErrorMessage, response_body, response_code = ThreatExchange::TENet::copyThreatDescriptor(
      postParams,
      showURLs: showURLs,
      dryRun: dryRun)

    unless validationErrorMessage.nil?
      $stderr.puts validationErrorMessage
      exit 1
    end

    puts response_body

    if response_code != "200"
      exit 1
    end
  end # CopyHandler.copySingle
end # class CopyHandler

# ----------------------------------------------------------------
# Top-down programming style, please :)

if __FILE__ == $0
  begin
    MainHandler.new.handle(ARGV)
    exit 0
  rescue Interrupt => e # Control-C handling
    exit 1
  end
end
