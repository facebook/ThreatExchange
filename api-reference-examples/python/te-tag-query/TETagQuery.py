#!/usr/bin/env python

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

import sys
import json

# ThreatExchange dependencies
import TE


def eprint(string):
    sys.stderr.write(string)
    sys.stderr.write("\n")


# ================================================================
# MAIN COMMAND-LINE ENTRY POINT
class MainHandler:
    def __init__(self, progName):
        self.progName = progName

    # ----------------------------------------------------------------
    # General rule about exit-codes and output streams:
    # * When help was asked for: print to stdout and exit 0.
    # * When unacceptable command-line syntax was provided: print to stderr and exit 1.
    def usage(self, exitCode):
        stream = sys.stdout if exitCode == 0 else sys.stderr
        output = """Usage: %s [options] {verb} {verb arguments}
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
  -b|--te-base-url {...} Defaults to "%s"

""" % (
            self.progName,
            TE.Net.DEFAULT_TE_BASE_URL,
        )

        stream.write(output + "\n")
        SubcommandHandlerFactory.listVerbs()
        sys.exit(exitCode)

    # ----------------------------------------------------------------
    # We don't use getopt, intentionally so. It doesn't know about our subcommand
    # structure.
    #
    # * python TETagQuery.py -h
    #   We want the -h handled by main().
    # * python TETagQuery.py submit -h
    #   We want the -h handled by submit().
    # * python TETagQuery.py -s submit -i ... -t ...
    #   We want the -s handled by main(), and -i/-t/etc handled by submit().

    def handle(self, args):
        options = self.getDefaultOptions()
        subcommandHandlerFactory = SubcommandHandlerFactory()

        while True:
            if len(args) == 0:
                break
            if args[0][0] != "-":
                break
            option = args[0]
            args = args[1:]

            if option == "-h":
                self.usage(0)
            elif option == "--help":
                self.usage(0)
            elif option == "-l" or option == "--list-verbs":
                SubcommandHandlerFactory.listVerbs()
                sys.exit(0)

            elif option == "-v" or option == "--verbose":
                options["verbose"] = True
            elif option == "-q" or option == "--quiet":
                options["verbose"] = False
            elif option == "-s" or option == "--show-urls":
                options["showURLs"] = True
            elif option == "-a" or option == "--app-token-env-name":
                if len(args) < 1:
                    self.usage(1)
                options["accessTokenEnvName"] = args[0]
                args = args[1:]
            elif option == "-b" or option == "--base-te-url":
                if len(args) < 1:
                    self.usage(1)
                options["baseTEURL"] = args[0]
                args = args[1:]
            else:
                eprint("%s: unrecognized  option %s" % (self.progName, option))
                sys.exit(1)

        if len(args) < 1:
            self.usage(1)

        verbName = args[0]
        args = args[1:]

        # Endpoint setup common to all verbs
        # ThreatExchange::TENet::setAppTokenFromEnvName(options['accessTokenEnvName'])
        baseTEURL = options["baseTEURL"]
        if baseTEURL != None:
            TE.Net.setTEBaseURL(baseTEURL)
        if options["accessTokenEnvName"] != None:
            TE.Net.setAppTokenFromEnvName(options["accessTokenEnvName"])

        subcommandHandler = subcommandHandlerFactory.create(self.progName, verbName)
        if subcommandHandler is None:
            eprint("%s: unrecognized verb %s" % (self.progName, verbName))
            sys.exit(1)
        subcommandHandler.handle(args, options)

    # ----------------------------------------------------------------
    def getDefaultOptions(self):
        return {
            "verbose": False,
            "showURLs": False,
            "pageSize": 10,
            "accessTokenEnvName": "TX_ACCESS_TOKEN",
            "baseTEURL": None,
        }


# ================================================================
# This is just a subcommand looker-upper. We use n subcommands within one
# script, instead of shipping n scripts.
class SubcommandHandlerFactory:
    VERB_NAMES = {
        "look-up-tag-id": "look-up-tag-id",
        "tag-to-ids": "tag-to-ids",
        "ids-to-details": "ids-to-details",
        "tag-to-details": "tag-to-details",
        "power-search": "power-search",
        "paginate": "paginate",
        "submit": "submit",
        "update": "update",
        "copy": "copy",
    }

    # Static method
    @classmethod
    def listVerbs(self):
        print("Verbs:")
        for keyValuePair in self.VERB_NAMES.items():
            key = keyValuePair[0]
            print(key)

    def create(self, progName, verbName):
        if verbName == self.VERB_NAMES["look-up-tag-id"]:
            return LookUpTagIDHandler(progName, verbName)
        elif verbName == self.VERB_NAMES["tag-to-ids"]:
            return TagToIDsHandler(progName, verbName)
        elif verbName == self.VERB_NAMES["ids-to-details"]:
            return IDsToDetailsHandler(progName, verbName)
        elif verbName == self.VERB_NAMES["tag-to-details"]:
            return TagToDetailsHandler(progName, verbName)
        elif verbName == self.VERB_NAMES["power-search"]:
            return PowerSearchHandler(progName, verbName)
        elif verbName == self.VERB_NAMES["paginate"]:
            return PaginateHandler(progName, verbName)
        elif verbName == self.VERB_NAMES["submit"]:
            return SubmitHandler(progName, verbName)
        elif verbName == self.VERB_NAMES["update"]:
            return UpdateHandler(progName, verbName)
        elif verbName == self.VERB_NAMES["copy"]:
            return CopyHandler(progName, verbName)
        else:
            return None


# ================================================================
# Code-reuse for all subcommand handlers.
class SubcommandHandler:
    def __init__(self, progName, verbName):
        self.progName = progName
        self.verbName = verbName


## ================================================================
class LookUpTagIDHandler(SubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        stream = sys.stdout if exitCode == 0 else sys.stderr
        output = "Usage: %s %s {one or more tag names}" % (self.progName, self.verbName)
        stream.write(output + "\n")
        sys.exit(exitCode)

    def handle(self, args, options):
        pass
        if len(args) >= 1:
            if args[0] == "-h" or args[0] == "--help":
                self.usage(0)

        if len(args) != 1:
            self.usage(1)

        tagName = args[0]
        tag_id = TE.Net.getTagIDFromName(tagName, options["showURLs"])
        if tag_id is None:
            eprint('Tag "%s" not found.' % tagName)
            sys.exit(1)
        else:
            print(tag_id)


# ================================================================
class TagToIDsHandler(SubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        stream = sys.stdout if exitCode == 0 else sys.stderr
        output = """Usage: %s %s [options] {tag name}
Options:
--tagged-since {x}
--tagged-until {x}
  Timestamp options for both are epoch seconds, various datetime formats
  including "2020-12-34T56:07:08+0900", and time-deltas like "-5minutes",
  "-3hours", "-1week".
--page-size {x}
""" % (
            self.progName,
            self.verbName,
        )
        stream.write(output + "\n")
        sys.exit(exitCode)

    def handle(self, args, options):

        options["includeIndicatorInOutput"] = True
        options["pageSize"] = 10

        while True:
            if len(args) == 0:
                break
            if args[0][0] != "-":
                break
            option = args[0]
            args = args[1:]

            if option == "-h":
                self.usage(0)
            elif option == "--help":
                self.usage(0)

            elif option == "--tagged-since":
                if len(args) < 1:
                    self.usage(1)
                options["taggedSince"] = args[0]
                args = args[1:]
            elif option == "--tagged-until":
                if len(args) < 1:
                    self.usage(1)
                options["taggedUntil"] = args[0]
                args = args[1:]

            elif option == "--page-size":
                if len(args) < 1:
                    self.usage(1)
                options["pageSize"] = args[0]
                args = args[1:]

            else:
                eprint(
                    "%s %s: unrecognized  option %s"
                    % (self.progName, self.verbName, option)
                )
                sys.exit(1)

        if len(args) != 1:
            self.usage(1)
        tagName = args[0]

        tag_id = TE.Net.getTagIDFromName(tagName, options["showURLs"])
        if tag_id is None:
            eprint('Tag "%s" not found.' % tagName)
            sys.exit(1)

        # Step 1: tag text to ID
        # Step 2: tag ID to descriptor IDs, paginated
        # Step 3: descriptor IDs to descriptor details, paginated
        idProcessor = lambda idBatch: self.IDProcessor(idBatch)

        TE.Net.processDescriptorIDsByTagID(
            tag_id,
            idProcessor,
            verbose=options["verbose"],
            showURLs=options["showURLs"],
            taggedSince=options.get("taggedSince", None),
            taggedUnti=options.get("taggedUntil", None),
            pageSize=options["pageSize"],
        )

    @classmethod
    def IDProcessor(self, idBatch):
        for id in idBatch:
            print(id)


# ================================================================
class IDsToDetailsHandler(SubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        stream = sys.stdout if exitCode == 0 else sys.stderr
        output = """Usage: %s %s [options] [IDs]
Options:
--no-print-indicator -- Don't print the indicator to the terminal
Please supply IDs either one line at a time on standard input, or on the command line
after the options.
""" % (
            self.progName,
            self.verbName,
        )
        stream.write(output + "\n")
        sys.exit(exitCode)

    def handle(self, args, options):
        options["includeIndicatorInOutput"] = True
        options["pageSize"] = 10

        while True:
            if len(args) == 0:
                break
            if args[0][0] != "-":
                break
            option = args[0]
            args = args[1:]

            if option == "-h":
                self.usage(0)
            elif option == "--help":
                self.usage(0)

            elif option == "--tagged-since":
                if len(args) < 1:
                    self.usage(1)
                options["taggedSince"] = args[0]
                args = args[1:]
            elif option == "--tagged-until":
                if len(args) < 1:
                    self.usage(1)
                options["taggedUntil"] = args[0]
                args = args[1:]

            elif option == "--page-size":
                if len(args) < 1:
                    self.usage(1)
                options["pageSize"] = args[0]
                args = args[1:]
            elif option == "--no-print-indicator":
                if len(args) < 1:
                    self.usage(1)
                options["includeIndicatorInOutput"] = False

            else:
                eprint(
                    "%s %s: unrecognized  option %s"
                    % (self.progName, self.verbName, option)
                )
                sys.exit(1)

        ids = []
        if len(args) > 0:
            ids = args
        else:
            while True:
                # Python line-reader returns the trailing newlines so
                # we need to right-strip the lines
                line = sys.stdin.readline()
                if line == "":
                    break
                ids.append(line.rstrip())

        for id in ids:
            idBatch = [id]

            descriptors = TE.Net.getInfoForIDs(
                idBatch,
                verbose=options["verbose"],
                showURLs=options["showURLs"],
                includeIndicatorInOutput=options["includeIndicatorInOutput"],
            )
            for descriptor in descriptors:
                print(json.dumps(descriptor))


# ================================================================
class TagToDetailsHandler(SubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        stream = sys.stdout if exitCode == 0 else sys.stderr
        output = """Usage: %s %s [options] {tag name}
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
""" % (
            self.progName,
            self.verbName,
        )
        stream.write(output + "\n")
        sys.exit(exitCode)

    def handle(self, args, options):
        options["includeIndicatorInOutput"] = True
        options["pageSize"] = 10

        while True:
            if len(args) == 0:
                break
            if args[0][0] != "-":
                break
            option = args[0]
            args = args[1:]

            if option == "-h":
                self.usage(0)
            elif option == "--help":
                self.usage(0)

            elif option == "--tagged-since":
                if len(args) < 1:
                    self.usage(1)
                options["taggedSince"] = args[0]
                args = args[1:]
            elif option == "--tagged-until":
                if len(args) < 1:
                    self.usage(1)
                options["taggedUntil"] = args[0]
                args = args[1:]

            elif option == "--created-since":
                if len(args) < 1:
                    self.usage(1)
                options["createdSince"] = args[0]
                args = args[1:]
            elif option == "--created-until":
                if len(args) < 1:
                    self.usage(1)
                options["createdUntil"] = args[0]
                args = args[1:]

            elif option == "--page-size":
                if len(args) < 1:
                    self.usage(1)
                options["pageSize"] = args[0]
                args = args[1:]
            elif option == "--no-print-indicator":
                if len(args) < 1:
                    self.usage(1)
                options["includeIndicatorInOutput"] = False

            else:
                eprint(
                    "%s %s: unrecognized  option %s"
                    % (self.progName, self.verbName, option)
                )
                sys.exit(1)

        if len(args) != 1:
            self.usage(1)
        tagName = args[0]

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

        options["createdSinceEpochSeconds"] = None
        options["createdUntilEpochSeconds"] = None
        if options.get("createdSince") != None:
            if options.get("taggedSince") != None:
                eprint(
                    "%s %s: Please specify at most one of --tagged-since and --created-since."
                    % (self.progName, self.verbName)
                )
                sys.exit(1)
            options["taggedSince"] = options["createdSince"]
            options["createdSinceEpochSeconds"] = TE.Net.parseTimeStringToEpochSeconds(
                options["createdSince"]
            )
        if options.get("createdUntil") != None:
            if options.get("taggedUntil") != None:
                eprint(
                    "%s %s: Please specify at most one of --tagged-until and --created-until."
                    % (self.progName, self.verbName)
                )
                sys.exit(1)
            # keep options['taggedUntil'] = None
            options["createdUntilEpochSeconds"] = TE.Net.parseTimeStringToEpochSeconds(
                options["createdUntil"]
            )

        # Step 1: tag text to ID
        # Step 2: tag ID to descriptor IDs, paginated
        # Step 3: descriptor IDs to descriptor details, paginated

        tag_id = TE.Net.getTagIDFromName(tagName, options["showURLs"])
        if tag_id is None:
            eprint('Tag "%s" not found.' % tagName)
            sys.exit(1)

        idProcessor = lambda idBatch: self.IDProcessor(idBatch, options)

        TE.Net.processDescriptorIDsByTagID(
            tag_id,
            idProcessor,
            verbose=options["verbose"],
            showURLs=options["showURLs"],
            taggedSince=options.get("taggedSince", None),
            taggedUnti=options.get("taggedUntil", None),
            pageSize=options["pageSize"],
        )

    @classmethod
    def IDProcessor(self, idBatch, options):
        descriptors = TE.Net.getInfoForIDs(
            idBatch,
            verbose=options["verbose"],
            showURLs=options["showURLs"],
            includeIndicatorInOutput=options["includeIndicatorInOutput"],
        )

        # See comments above regarding tagged-at filtering being done server-side
        # and created-at filtering being done client-side (i.e. right here).
        createdSinceEpochSeconds = options.get("createdSinceEpochSeconds")
        createdUntilEpochSeconds = options.get("createdUntilEpochSeconds")

        for descriptor in descriptors:
            descriptorCreatedAtEpochSeconds = TE.Net.parseTimeStringToEpochSeconds(
                descriptor["added_on"]
            )
            if createdSinceEpochSeconds != None:
                if descriptorCreatedAtEpochSeconds < createdSinceEpochSeconds:
                    continue
            if createdUntilEpochSeconds != None:
                if descriptorCreatedAtEpochSeconds > createdUntilEpochSeconds:
                    continue

            # Stub processing -- one would perhaps integrate with one's own system
            print(json.dumps(descriptor))


# ================================================================
class PowerSearchHandler(SubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        stream = sys.stdout if exitCode == 0 else sys.stderr
        output = """Usage: %s %s [options]
Options:
--limit {n} or --page-size {n}  Defines the maximum size of a page of results. The maximum is 1,000.
--max-confidence {n}            Defines the maximum allowed confidence value for the data returned.
--min-confidence {n}            Defines the minimum allowed confidence value for the data returned.
--owner {x}                     Comma-separated list of AppIDs of the person who submitted the data.
--review-status {x}             A given ReviewStatusType
--severity {x}                  A given SeverityWType
--share-level {x}               A given ShareLevelType
--since {x}                     Returns descriptors collected after a timestamp
--status {x}                    A given StatusType
--strict-text                   When provided, the API will not do approximate
                                matching on the value in the text field
--tags {a,b,c}                  Comma-separated list of tags to filter results,
                                ORed together unless --tags-are-anded is used
--tags-are-anded                If provided, tags are ANDed together
--text {x}                      Freeform text field with a value to search for.
                                This can be an indicator text or a string found in other fields of the objects.
--type or --indicator-type {x}  The type of descriptor to search for (see IndicatorTypes)
--until {x}                     Returns descriptors collected before a timestamp

Timestamp options for --since and --until are epoch seconds, various datetime
formats including "2020-12-34T56:07:08+0900", and time-deltas like "-5minutes",
"-3hours", "-1week".

NOTE: THIS IS KNOWN TO NOT CORRECTLY HANDLE PAGINATION.  Please use
tagged_objects with tagged_since in the TE API, which is wrapped by
tag-to-details in this tool.

See also
https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptors
""" % (
            self.progName,
            self.verbName,
        )
        stream.write(output + "\n")
        sys.exit(exitCode)

    def handle(self, args, options):
        urlParams = {}

        while True:
            if len(args) == 0:
                break
            if args[0][0] != "-":
                break
            option = args[0]
            args = args[1:]

            if option == "-h":
                self.usage(0)
            elif option == "--help":
                self.usage(0)

            elif option == "--limit" or option == "page-size":
                if len(args) < 1:
                    self.usage(1)
                urlParams["limit"] = args[0]
                args = args[1:]

            elif option == "--max-confidence":
                if len(args) < 1:
                    self.usage(1)
                urlParams["max_confidence"] = args[0]
                args = args[1:]

            elif option == "--min-confidence":
                if len(args) < 1:
                    self.usage(1)
                urlParams["min_confidence"] = args[0]
                args = args[1:]

            elif option == "--owner":
                if len(args) < 1:
                    self.usage(1)
                urlParams["owner"] = args[0]
                args = args[1:]

            elif option == "--review-status":
                if len(args) < 1:
                    self.usage(1)
                urlParams["review_status"] = args[0]
                args = args[1:]

            elif option == "--severity":
                if len(args) < 1:
                    self.usage(1)
                urlParams["severity"] = args[0]
                args = args[1:]

            elif option == "--share-level":
                if len(args) < 1:
                    self.usage(1)
                urlParams["share_level"] = args[0]
                args = args[1:]

            elif option == "--since":
                if len(args) < 1:
                    self.usage(1)
                urlParams["since"] = args[0]
                args = args[1:]

            elif option == "--status":
                if len(args) < 1:
                    self.usage(1)
                urlParams["status"] = args[0]
                args = args[1:]

            elif option == "--strict-text":
                urlParams["strict_text"] = "true"

            elif option == "--tag" or option == "--tags":
                if len(args) < 1:
                    self.usage(1)
                urlParams["tags"] = args[0]
                args = args[1:]

            elif option == "--tags-are-anded":
                urlParams["tags_are_anded"] = "true"

            elif option == "--text":
                if len(args) < 1:
                    self.usage(1)
                urlParams["text"] = args[0]
                args = args[1:]

            elif option == "--type" or option == "--indicator-type":
                if len(args) < 1:
                    self.usage(1)
                urlParams["type"] = args[0]
                args = args[1:]

            elif option == "--until":
                if len(args) < 1:
                    self.usage(1)
                urlParams["until"] = args[0]
                args = args[1:]

            else:
                eprint(
                    "%s %s: unrecognized  option %s"
                    % (self.progName, self.verbName, option)
                )
                sys.exit(1)

        if urlParams.get("since") is None:
            eprint("%s %s: --since is required" % (self.progName, self.verbName))
            self.usage(1)
        if len(args) > 0:
            eprint(
                "%s %s: extraneous argument(s) %s"
                % (self.progName, self.verbName, ", ".join(args))
            )
            self.usage(1)

        descriptorBatchProcessor = (
            lambda descriptorBatch: self.DescriptorBatchProcessor(
                descriptorBatch, options
            )
        )

        TE.Net.doPowerSearch(descriptorBatchProcessor, urlParams, options)

    def DescriptorBatchProcessor(self, descriptorBatch, options):
        for descriptor in descriptorBatch:
            # Stub processing -- one would perhaps integrate with one's own system
            print(json.dumps(descriptor))


# ================================================================
class PaginateHandler(SubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        stream = sys.stdout if exitCode == 0 else sys.stderr
        output = """Usage: %s %s {URL}
Curls the URL, JSON-dumps the return value's data blob, then curls
the next-page URL and repeats until there are no more pages.
""" % (
            self.progName,
            self.verbName,
        )
        stream.write(output + "\n")
        sys.exit(exitCode)

    def handle(self, args, options):
        if len(args) >= 1:
            if args[0] == "-h" or args[0] == "--help":
                self.usage(0)
        if len(args) != 1:
            self.usage(1)

        startURL = args[0]
        nextURL = startURL

        while nextURL != None:
            if options["showURLs"]:
                print("URL:")
                print(nextURL)
            response = TE.Net.getJSONFromURL(nextURL)
            data = response.get("data", None)
            paging = response.get("paging", None)
            if data is None:
                eprint("No data field found in response JSON.")
                break
            if paging is None:
                nextURL = None
            else:
                nextURL = paging.get("next", None)

            print(json.dumps(data))


# ================================================================
# Some code-reuse for all subcommand handlers that do POSTs.
class AbstractPostSubcommandHandler(SubcommandHandler):
    # These allow us to customize the mostly-overlapping usage() method
    POSTER_NAME_SUBMIT = "submit"
    POSTER_NAME_UPDATE = "update"
    POSTER_NAME_COPY = "copy"

    def __init__(self, progName, verbName):
        self.progName = progName
        self.verbName = verbName

    # ----------------------------------------------------------------
    def commonPosterUsage(self, exitCode, posterName):
        stream = sys.stdout if exitCode == 0 else sys.stderr

        output1 = """Usage: %s %s [options]
""" % (
            self.progName,
            self.verbName,
        )

        output2 = None
        if posterName == self.POSTER_NAME_SUBMIT:
            output2 = """
Uploads a threat descriptor with the specified values.
On repost (with same indicator text/type and app ID), updates changed fields.

Required:
-i|--indicator {...}   The indicator text: hash/URL/etc.
-I                     Take indicator text from standard input, one per line.
Exactly one of -i or -I is required.
-t|--type {...}
"""
        if posterName == self.POSTER_NAME_UPDATE:
            output2 = """
Updates specified attributes on an existing threat descriptor.

Required:
-n {...}               ID of descriptor to be edited. Must already exist.
-N                     Take descriptor IDs from standard input, one per line.
Exactly one of -n or -N is required.
"""

        output3 = """
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
"""

        output4 = None
        if posterName == self.POSTER_NAME_UPDATE:
            output4 = """
--add-tags {...}       Comma-delimited. Adds these on repost.
--remove-tags {...}    Comma-delimited. Removes these on repost.
"""

        output5 = """
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
"""

        stream.write(output1 + "\n")
        if output2 != None:
            stream.write(output2 + "\n")
        stream.write(output3 + "\n")
        if output4 != None:
            stream.write(output4 + "\n")
        stream.write(output5 + "\n")

        sys.exit(exitCode)

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
    def commonPosterOptionCheck(self, option, args, postParams):
        # Local keystroke-saver for this enum
        names = TE.Net.POST_PARAM_NAMES

        handled = True

        if option == "-d" or option == "--description":
            if len(args) < 1:
                self.usage(1)
            postParams[names["description"]] = args[0]
            args = args[1:]

        elif option == "-l" or option == "--share-level":
            if len(args) < 1:
                self.usage(1)
            postParams[names["share_level"]] = args[0]
            args = args[1:]
        elif option == "-p" or option == "--privacy-type":
            if len(args) < 1:
                self.usage(1)
            postParams[names["privacy_type"]] = args[0]
            args = args[1:]
        elif option == "-m" or option == "--privacy-members":
            if len(args) < 1:
                self.usage(1)
            postParams[names["privacy_members"]] = args[0]
            args = args[1:]

        elif option == "-s" or option == "--status":
            if len(args) < 1:
                self.usage(1)
            postParams[names["status"]] = args[0]
            args = args[1:]
        elif option == "-r" or option == "--review-status":
            if len(args) < 1:
                self.usage(1)
            postParams[names["review_status"]] = args[0]
            args = args[1:]
        elif option == "-y" or option == "--severity":
            if len(args) < 1:
                self.usage(1)
            postParams[names["severity"]] = args[0]
            args = args[1:]
        elif option == "-c" or option == "--confidence":
            if len(args) < 1:
                self.usage(1)
            postParams[names["confidence"]] = args[0]
            args = args[1:]

        elif option == "--related-ids-for-upload":
            if len(args) < 1:
                self.usage(1)
            postParams[names["related_ids_for_upload"]] = args[0]
            args = args[1:]
        elif option == "--related-triples-for-upload-as-json":
            if len(args) < 1:
                self.usage(1)
            postParams[names["related_triples_for_upload_as_json"]] = args[0]
            args = args[1:]

        elif option == "--reactions-to-add":
            if len(args) < 1:
                self.usage(1)
            postParams[names["reactions"]] = args[0]
            args = args[1:]
        elif option == "--reactions-to-remove":
            if len(args) < 1:
                self.usage(1)
            postParams[names["reactions_to_remove"]] = args[0]
            args = args[1:]

        elif option == "--first-active":
            if len(args) < 1:
                self.usage(1)
            postParams[names["first_active"]] = args[0]
            args = args[1:]
        elif option == "--last-active":
            if len(args) < 1:
                self.usage(1)
            postParams[names["last"]] = args[0]
            args = args[1:]
        elif option == "--expired-on":
            if len(args) < 1:
                self.usage(1)
            postParams[names["expired_on"]] = args[0]
            args = args[1:]

        else:
            handled = False

        return [handled, args]


# ================================================================
class SubmitHandler(AbstractPostSubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        self.commonPosterUsage(exitCode, self.POSTER_NAME_SUBMIT)

    def handle(self, args, options):
        options["dryRun"] = False
        options["indicatorTextFromStdin"] = False

        postParams = {}
        # Local keystroke-saver for this enum
        names = TE.Net.POST_PARAM_NAMES

        while True:
            if len(args) == 0:
                break
            if args[0][0] != "-":
                break
            option = args[0]
            args = args[1:]

            if option == "-h":
                self.usage(0)
            elif option == "--help":
                self.usage(0)

            elif option == "--dry-run":
                options["dryRun"] = True

            elif option == "-I":
                options["indicatorTextFromStdin"] = True
            elif option == "-i" or option == "--indicator":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["indicator"]] = args[0]
                args = args[1:]

            elif option == "-t" or option == "--type":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["type"]] = args[0]
                args = args[1:]

            elif option == "--tags":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["tags"]] = args[0]
                args = args[1:]

            else:
                handled, args = self.commonPosterOptionCheck(option, args, postParams)
                if not handled:
                    eprint(
                        "%s %s: unrecognized  option %s"
                        % (self.progName, self.verbName, option)
                    )
                    sys.exit(1)

        if len(args) > 0:
            eprint(
                '%s %s: extraneous argument(s) "%s"'
                % (self.progName, self.verbName, " ".join(args))
            )
            sys.exit(1)

        if options["indicatorTextFromStdin"]:
            if postParams.get(names["indicator"], None) != None:
                eprint(
                    "%s %s: only one of -I and -i must be supplied."
                    % (self.progName, self.verbName)
                )
                sys.exit(1)
            while True:
                # Python line-reader returns the trailing newlines so
                # we need to right-strip the lines
                line = sys.stdin.readline()
                if line == "":
                    break
                postParams[names["indicator"]] = line.rstrip()
                self.submitSingle(
                    postParams,
                    options["verbose"],
                    options["showURLs"],
                    options["dryRun"],
                )
        else:
            if postParams.get(names["indicator"], None) == None:
                eprint(
                    "%s %s: only one of -I and -i must be supplied."
                    % (self.progName, self.verbName)
                )
                sys.exit(1)
            self.submitSingle(
                postParams, options["verbose"], options["showURLs"], options["dryRun"]
            )

    # ----------------------------------------------------------------
    def submitSingle(self, postParams, verbose, showURLs, dryRun):
        (
            validationErrorMessage,
            serverSideError,
            responseBody,
        ) = TE.Net.submitThreatDescriptor(postParams, showURLs, dryRun)

        if validationErrorMessage != None:
            eprint(validationErrorMessage)
            sys.exit(1)

        if serverSideError != None:
            eprint(str(serverSideError))
            eprint(json.dumps(responseBody))
            sys.exit(1)

        print(json.dumps(responseBody))


# ================================================================
class UpdateHandler(AbstractPostSubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        self.commonPosterUsage(exitCode, self.POSTER_NAME_UPDATE)

    # ----------------------------------------------------------------
    def handle(self, args, options):

        options["dryRun"] = False
        options["descriptorIDsFromStdin"] = False

        postParams = {}

        # Local keystroke-saver for this enum
        names = TE.Net.POST_PARAM_NAMES

        while True:
            if len(args) == 0:
                break
            if args[0][0] != "-":
                break
            option = args[0]
            args = args[1:]

            if option == "-h":
                self.usage(0)
            elif option == "--help":
                self.usage(0)

            elif option == "--dry-run":
                options["dryRun"] = True

            elif option == "-N":
                options["descriptorIDsFromStdin"] = True
            elif option == "-n":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["descriptor_id"]] = args[0]
                args = args[1:]

            elif option == "--tags":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["tags"]] = args[0]
                args = args[1:]
            elif option == "--add-tags":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["add_tags"]] = args[0]
                args = args[1:]
            elif option == "--remove-tags":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["remove_tags"]] = args[0]
                args = args[1:]

            else:
                handled, args = self.commonPosterOptionCheck(option, args, postParams)
                if not handled:
                    eprint(
                        "%s %s: unrecognized  option %s"
                        % (self.progName, self.verbName, option)
                    )
                    sys.exit(1)

        if len(args) > 0:
            eprint(
                '%s %s: extraneous argument(s) "%s"'
                % (self.progName, self.verbName, " ".join(args))
            )
            sys.exit(1)

        if options["descriptorIDsFromStdin"]:
            if postParams.get(names["descriptor_id"], None) != None:
                eprint(
                    "%s %s: only one of -N and -n must be supplied."
                    % (self.progName, self.verbName)
                )
                sys.exit(1)
            while True:
                # Python line-reader returns the trailing newlines so
                # we need to right-strip the lines
                line = sys.stdin.readline()
                if line == "":
                    break
                postParams[names["descriptor_id"]] = line.rstrip()
                self.updateSingle(
                    postParams,
                    options["verbose"],
                    options["showURLs"],
                    options["dryRun"],
                )
        else:
            if postParams.get(names["descriptor_id"], None) == None:
                eprint(
                    "%s %s: only one of -N and -n must be supplied."
                    % (self.progName, self.verbName)
                )
                sys.exit(1)
            self.updateSingle(
                postParams, options["verbose"], options["showURLs"], options["dryRun"]
            )

    # ----------------------------------------------------------------
    def updateSingle(self, postParams, verbose, showURLs, dryRun):
        (
            validationErrorMessage,
            serverSideError,
            responseBody,
        ) = TE.Net.updateThreatDescriptor(postParams, showURLs, dryRun)

        if validationErrorMessage != None:
            eprint(validationErrorMessage)
            sys.exit(1)

        if serverSideError != None:
            eprint(str(serverSideError))
            eprint(json.dumps(responseBody))
            sys.exit(1)

        print(json.dumps(responseBody))


# ================================================================
class CopyHandler(AbstractPostSubcommandHandler):
    def __init__(self, progName, verbName):
        super(__class__, self).__init__(progName, verbName)

    def usage(self, exitCode):
        self.commonPosterUsage(exitCode, self.POSTER_NAME_COPY)

    # ----------------------------------------------------------------
    def handle(self, args, options):

        options["dryRun"] = False
        options["descriptorIDsFromStdin"] = False

        postParams = {}

        # Local keystroke-saver for this enum
        names = TE.Net.POST_PARAM_NAMES

        while True:
            if len(args) == 0:
                break
            if args[0][0] != "-":
                break
            option = args[0]
            args = args[1:]

            if option == "-h":
                self.usage(0)
            elif option == "--help":
                self.usage(0)

            elif option == "--dry-run":
                options["dryRun"] = True

            elif option == "-N":
                options["descriptorIDsFromStdin"] = True
            elif option == "-n":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["descriptor_id"]] = args[0]
                args = args[1:]

            elif option == "-i" or option == "--indicator":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["indicator"]] = args[0]
                args = args[1:]

            elif option == "-t" or option == "--type":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["type"]] = args[0]
                args = args[1:]

            elif option == "--tags":
                if len(args) < 1:
                    self.usage(1)
                postParams[names["tags"]] = args[0]
                args = args[1:]

            else:
                handled, args = self.commonPosterOptionCheck(option, args, postParams)
                if not handled:
                    eprint(
                        "%s %s: unrecognized  option %s"
                        % (self.progName, self.verbName, option)
                    )
                    sys.exit(1)

        if len(args) > 0:
            eprint(
                '%s %s: extraneous argument(s) "%s"'
                % (self.progName, self.verbName, " ".join(args))
            )
            sys.exit(1)

        if options["descriptorIDsFromStdin"]:
            if postParams.get(names["descriptor_id"], None) != None:
                eprint(
                    "%s %s: only one of -N and -n must be supplied."
                    % (self.progName, self.verbName)
                )
                sys.exit(1)
            while True:
                # Python line-reader returns the trailing newlines so
                # we need to right-strip the lines
                line = sys.stdin.readline()
                if line == "":
                    break
                postParams[names["descriptor_id"]] = line.rstrip()
                self.copySingle(
                    postParams,
                    options["verbose"],
                    options["showURLs"],
                    options["dryRun"],
                )
        else:
            if postParams.get(names["descriptor_id"], None) == None:
                eprint(
                    "%s %s: only one of -N and -n must be supplied."
                    % (self.progName, self.verbName)
                )
                sys.exit(1)
            self.copySingle(
                postParams, options["verbose"], options["showURLs"], options["dryRun"]
            )

    # ----------------------------------------------------------------
    def copySingle(self, postParams, verbose, showURLs, dryRun):
        (
            validationErrorMessage,
            serverSideError,
            responseBody,
        ) = TE.Net.copyThreatDescriptor(postParams, showURLs, dryRun)

        if validationErrorMessage != None:
            eprint(validationErrorMessage)
            sys.exit(1)

        if serverSideError != None:
            eprint(str(serverSideError))
            eprint(json.dumps(responseBody))
            sys.exit(1)

        print(json.dumps(responseBody))


# ----------------------------------------------------------------
# Top-down programming style, please :)

# Rememmber that sys.argv includes the program name in Python,
# like C/C++/Go and unlike Java or Ruby.
if __name__ == "__main__":
    MainHandler(sys.argv[0]).handle(sys.argv[1:])
