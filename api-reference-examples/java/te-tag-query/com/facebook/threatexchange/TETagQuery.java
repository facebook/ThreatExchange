// Copyright (c) Meta Platforms, Inc. and affiliates.

package com.facebook.threatexchange;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.lang.NumberFormatException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

/**
 * Example technique for retrieving all descriptors with a given tag from
 * ThreatExchange.
 *
 * Notes:
 *
 * * We use the tagged_objects endpoint to fetch IDs of all descriptors. This
 *   endpoint doesn't return all desired metadata fields, so we use it as a
 *   quick map from tag ID to list of descriptor IDs. This is relatively quick.
 *
 * * Then for each resulting descriptor ID we do a query for all fields
 *   associated with that ID. This is relatively slow, but batching multiple
 *   IDs per query helps a lot.
 *
 * Please see README.md for example usages.
 */
public class TETagQuery {
  private static final String PROGNAME = "TETagQuery";
  private static final String DEFAULT_APP_TOKEN_ENV_NAME = "TX_ACCESS_TOKEN";

  // https://developers.facebook.com/docs/threat-exchange/best-practices#batching
  private static final int MAX_IDS_PER_QUERY = 50;

  // ================================================================
  // MAIN COMMAND-LINE ENTRY POINT
  // ================================================================

  /**
   * Usage function for main().
   */
  private static void usage(int exitCode) {
    PrintStream o = Utils.getPrintStream(exitCode);
    o.printf("Usage: %s [options] {verb} {verb arguments}\n", PROGNAME);
    o.printf("Downloads descriptors in bulk from ThreatExchange, given\n");
    o.printf("either a tag name or a list of IDs one per line on standard input.\n");
    o.printf("Options:\n");
    o.printf("  -h|--help      Show detailed help.\n");
    o.printf("  -l|--list-verbs   Show a list of supported verbs.\n", PROGNAME);
    o.printf("  -q|--quiet     Only print IDs/descriptors output with no narrative.\n");
    o.printf("  -v|--verbose   Print IDs/descriptors output along with narrative.\n");
    o.printf("  -s|--show-urls Print URLs used for queries, before executing them.\n");
    o.printf("  -a|--app-token-env-name {...} Name of app-token environment variable.\n");
    o.printf("                 Defaults to \"%s\".\n", DEFAULT_APP_TOKEN_ENV_NAME);
    o.printf("  -b|--te-base-url {...} Defaults to \"%s\"\n", Constants.DEFAULT_TE_BASE_URL);
    CommandHandlerFactory.list(o);
    System.exit(exitCode);
  }

  /**
   * There can be only one.
   */
  public static void main(String[] args) throws IOException {

    // Set defaults
    String appTokenEnvName = DEFAULT_APP_TOKEN_ENV_NAME;
    boolean verbose = false;
    boolean showURLs = false;
    int numIDsPerQuery = MAX_IDS_PER_QUERY;
    DescriptorFormatter descriptorFormatter = new JSONDescriptorFormatter();

    // Override defaults
    while (args.length > 0 && args[0].startsWith("-")) {
      String option = args[0];
      args = Arrays.copyOfRange(args, 1, args.length);

      if (option.equals("-h") || option.equals("--help")) {
        usage(0);

      } else if (option.equals("-v") || option.equals("--verbose")) {
        verbose = true;

      } else if (option.equals("-q") || option.equals("--quiet")) {
        verbose = false;

      } else if (option.equals("-s") || option.equals("--show-urls")) {
        showURLs = true;

      } else if (option.equals("-l") || option.equals("--list-verbs")) {
        CommandHandlerFactory.list(System.out);
        System.exit(0);

      } else if (option.equals("--ids-per-query")) {
        if (args.length < 1) {
          usage(1);
        }
        String svalue = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);
        try {
          numIDsPerQuery = Integer.valueOf(svalue);
        } catch (NumberFormatException e) {
          System.err.printf("%s: could not parse \"%s\" as integer.\n",
            PROGNAME, svalue);
          System.exit(1);
        }
        if (numIDsPerQuery < 1 || numIDsPerQuery > MAX_IDS_PER_QUERY) {
          System.err.printf("%s: num IDs per query must be in the range 1..%d; got %d.\n",
            PROGNAME, MAX_IDS_PER_QUERY, numIDsPerQuery);
          System.exit(1);
        }

      } else if (option.equals("-a") || option.equals("--app-token-env-name")) {
        if (args.length < 1) {
          usage(1);
        }
        appTokenEnvName = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

      } else if (option.equals("-b") || option.equals("--te-base-url")) {
        if (args.length < 1) {
          usage(1);
        }
        Net.setTEBaseURL(args[0]);
        args = Arrays.copyOfRange(args, 1, args.length);

      } else {
        System.err.printf("%s: unrecognized option \"%s\".\n", PROGNAME, option);
        usage(1);
      }
    }

    Net.setAppToken(appTokenEnvName);

    if (args.length < 1) {
      usage(1);
    }
    String verb = args[0];
    args = Arrays.copyOfRange(args, 1, args.length);

    CommandHandler commandHandler = CommandHandlerFactory.create(verb);
    if (commandHandler == null) {
      System.err.printf("%s: verb \"%s\" not found.\n", PROGNAME, verb);
      System.exit(1);
    }
    commandHandler.handle(args, numIDsPerQuery, verbose, showURLs,
      descriptorFormatter);
  }

  // ================================================================
  // Command-handlers invoked from main.
  // ================================================================

  /**
   * Maps verb from main to a handler for it.
   */
  public static class CommandHandlerFactory {
    private static final String LOOK_UP_TAG_ID = "look-up-tag-id";
    private static final String TAG_TO_IDS = "tag-to-ids";
    private static final String IDS_TO_DETAILS = "ids-to-details";
    private static final String TAG_TO_DETAILS = "tag-to-details";
    private static final String INCREMENTAL = "incremental";
    private static final String PAGINATE = "paginate";
    private static final String SUBMIT = "submit";
    private static final String UPDATE = "update";
    private static final String COPY = "copy";

    public static CommandHandler create(String verb) {
      switch(verb) {
      case LOOK_UP_TAG_ID:
        return new LookUpTagIDHandler(verb);
      case TAG_TO_IDS:
        return new TagToIDsHandler(verb);
      case IDS_TO_DETAILS:
        return new IDsToDetailsHandler(verb);
      case TAG_TO_DETAILS:
        return new TagToDetailsHandler(verb);
      case INCREMENTAL:
        return new IncrementalHandler(verb);
      case PAGINATE:
        return new PaginateHandler(verb);
      case SUBMIT:
        return new SubmitHandler(verb);
      case UPDATE:
        return new UpdateHandler(verb);
      case COPY:
        return new CopyHandler(verb);
      default:
        return null;
      }
    }

    public static void list(PrintStream o) {
      o.printf("Verbs:\n");
      o.printf("  %s\n", LOOK_UP_TAG_ID);
      o.printf("  %s\n", TAG_TO_IDS);
      o.printf("  %s\n", IDS_TO_DETAILS);
      o.printf("  %s\n", TAG_TO_DETAILS);
      o.printf("  %s\n", INCREMENTAL);
      o.printf("  %s\n", PAGINATE);
      o.printf("  %s\n", SUBMIT);
      o.printf("  %s\n", UPDATE);
      o.printf("  %s\n", COPY);
    }
  }

  /**
   * Code-reuse for various command-handlers.
   */
  public static abstract class CommandHandler {
    protected static String _verb;
    public CommandHandler(String verb) {
      _verb = verb;
    }
    abstract void usage(int exitCode);
    abstract void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    );
  }

  // ----------------------------------------------------------------
  public static class LookUpTagIDHandler extends CommandHandler {
    public LookUpTagIDHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s {one or more tag names}\n",
        PROGNAME, _verb);
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      if (args.length < 1) {
        usage(1);
      }

      for (String tagName : args) {
        String tagID = Net.getTagIDFromName(tagName, showURLs);
        if (tagID == null) {
          System.out.printf("tag_name=%s,tag_id=null\n", tagName);
        } else {
          System.out.printf("tag_name=%s,tag_id=%s\n", tagName, tagID);
        }
      }
    }
  }

  // ----------------------------------------------------------------
  public static class TagToIDsHandler extends CommandHandler {
    public TagToIDsHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options] {tag name}\n",
        PROGNAME, _verb);
      o.printf("Options:\n");
      o.printf("--tagged-since {x}\n");
      o.printf("--tagged-until {x}\n");
      o.printf("--page-size {x}\n");
      o.printf("--no-print-indicator -- Don't print the indicator to the terminal\n");
      o.printf("The \"tagged-since\" or \"tagged-until\" parameter is any supported by ThreatExchange,\n");
      o.printf("e.g. seconds since the epoch, or \"-1hour\", or \"-1day\", etc.\n");
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      int pageSize = 10;
      boolean includeIndicatorInOutput = true;
      String taggedSince = null;
      String taggedUntil = null;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--tagged-since")) {
          if (args.length < 1) {
            usage(1);
          }
          taggedSince = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--tagged-until")) {
          if (args.length < 1) {
            usage(1);
          }
          taggedUntil = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--page-size")) {
          if (args.length < 1) {
            usage(1);
          }
          pageSize = Integer.valueOf(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--no-print-indicator")) {
          includeIndicatorInOutput = false;

        } else {
          System.err.printf("%s %s: unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }

      if (args.length != 1) {
        usage(1);
      }
      String tagName = args[0];

      String tagID = Net.getTagIDFromName(tagName, showURLs);
      if (tagID == null) {
        System.err.printf("%s: could not find tag by name \"%s\".\n",
          PROGNAME, tagName);
        System.exit(1);
      }

      if (verbose) {
        SimpleJSONWriter w = new SimpleJSONWriter();
        w.add("tag_name", tagName);
        w.add("tag_id", tagID);
        System.out.println(w.format());
        System.out.flush();
      }

      // Returns IDs for all descriptors. The return from this bulk-query call
      // gives back only ID code, indicator text, and the uninformative label
      // "THREAT_DESCRIPTOR". From this we can dive in on each item, though,
      // and query for its details one ID at a time.
      Net.getDescriptorIDsByTagID(tagID, verbose, showURLs,
        taggedSince, taggedUntil, pageSize, includeIndicatorInOutput,
        new IDPrinterProcessor(verbose));
    }
  }

  /**
   * Callback for TagToIDsHandler: what we want done with every batch of
   * threat-descriptor IDs.
   */
  private static class IDPrinterProcessor implements IDProcessor {
    private final boolean _verbose;

    public IDPrinterProcessor(boolean verbose) {
      _verbose = verbose;
    }

    public void processIDs(List<String> ids) {
      if (_verbose) {
        SimpleJSONWriter w = new SimpleJSONWriter();
        w.add("descriptor_count", ids.size());
        System.out.println(w.format());
        System.out.flush();

        int i = 0;
        for (String id : ids) {
          w = new SimpleJSONWriter();
          w.add("i", i);
          w.add("descriptor_id", id);
          System.out.println(w.format());
          System.out.flush();
          i++;
        }
      } else {
        for (String id: ids) {
          System.out.println(id);
          System.out.flush();
        }
      }
    }
  }

  // ----------------------------------------------------------------
  public static class IDsToDetailsHandler extends CommandHandler {
    public IDsToDetailsHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options] [IDs]\n",
        PROGNAME, _verb);
      o.printf("Options:\n");
      o.printf("--no-print-indicator -- Don't print the indicator to the terminal\n");
      o.printf("--data-dir {d} -- Write descriptors as {ID}.{extension} files in directory named {d}\n");
      o.printf("Please supply IDs either one line at a time on standard input, or on the command line\n");
      o.printf("after the options.\n");
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      boolean includeIndicatorInOutput = true;
      String dataDir = null;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--data-dir")) {
          if (args.length < 1) {
            usage(1);
          }
          dataDir = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--no-print-indicator")) {
          includeIndicatorInOutput = false;

        } else {
          System.err.printf("%s %s: unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }

      if (dataDir != null) {
        File handle = new File(dataDir);
        boolean ok = handle.exists() || handle.mkdirs();
        if (!ok) {
          System.err.printf("%s: could not create output directory \"%s\"\n",
            PROGNAME, dataDir);
          System.exit(1);
        }
      }

      List<String> ids = new ArrayList<String>();

      if (args.length > 0) {
        for (String arg: args) {
          ids.add(arg);
        }
      } else {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        int lno = 1;
        try {
          while ((line = reader.readLine()) != null) {
            lno++;
            // In Java, line-terminators already stripped for us
            ids.add(line);
          }
        } catch (IOException e) {
          System.err.printf("Couldn't read line %d of standard input.\n", lno);
          System.exit(1);
        }
      }

      outputDetails(ids, numIDsPerQuery, verbose, showURLs,
        IndicatorTypeFilterer.createAllFilterer(), includeIndicatorInOutput,
        dataDir, descriptorFormatter);
    }
  }

  // ----------------------------------------------------------------
  public static class TagToDetailsHandler extends CommandHandler {
    public TagToDetailsHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options] {tag name}\n",
        PROGNAME, _verb);
      o.printf("Options:\n");
      o.printf("--tagged-since {x}\n");
      o.printf("--tagged-until {x}\n");
      o.printf("--page-size {x}\n");
      o.printf("--indicator-type {x}\n");
      o.printf("--no-print-indicator -- Don't print the indicator\n");
      o.printf("--data-dir {d} -- Write descriptors as {ID}.{extension} files in directory named {d}\n");
      o.printf("The \"tagged-since\" or \"tagged-until\" parameter is any supported by ThreatExchange,\n");
      o.printf("e.g. seconds since the epoch, or \"-1hour\", or \"-1day\", etc.\n");
      o.printf("--list   Print valid indicator-types and exit.\n");
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      IndicatorTypeFilterer indicatorTypeFilterer = IndicatorTypeFilterer.createAllFilterer();
      int pageSize = 1000;
      String taggedSince = null;
      String taggedUntil = null;
      boolean includeIndicatorInOutput = true;
      String dataDir = null;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--list")) {
          IndicatorTypeFilterer.list(System.out);
          System.exit(0);
        } else if (option.equals("--data-dir")) {
          if (args.length < 1) {
            usage(1);
          }
          dataDir = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--tagged-since")) {
          if (args.length < 1) {
            usage(1);
          }
          taggedSince = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--tagged-until")) {
          if (args.length < 1) {
            usage(1);
          }
          taggedUntil = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--page-size")) {
          if (args.length < 1) {
            usage(1);
          }
          pageSize = Integer.valueOf(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--indicator-type")) {
          if (args.length < 1) {
            usage(1);
          }

          indicatorTypeFilterer = IndicatorTypeFilterer.create(args[0]);
          if (indicatorTypeFilterer == null) {
            System.err.printf("%s %s: unrecognized indicator-type filter \"%s\".\n",
              PROGNAME, _verb, args[0]);
            usage(1);
          }

          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--no-print-indicator")) {
          includeIndicatorInOutput = false;

        } else {
          System.err.printf("%s %s: unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }

      if (args.length != 1) {
        usage(1);
      }
      String tagName = args[0];

      if (dataDir != null) {
        File handle = new File(dataDir);
        boolean ok = handle.exists() || handle.mkdirs();
        if (!ok) {
          System.err.printf("%s: could not create output directory \"%s\"\n",
            PROGNAME, dataDir);
          System.exit(1);
        }
      }

      String tagID = Net.getTagIDFromName(tagName, showURLs);
      if (tagID == null) {
        System.err.printf("%s: could not find tag by name \"%s\".\n",
          PROGNAME, tagName);
        System.exit(1);
      }
      if (verbose) {
        SimpleJSONWriter w = new SimpleJSONWriter();
        w.add("tag_name", tagName);
        w.add("tag_id", tagID);
        System.out.println(w.format());
        System.out.flush();
      }

      // Returns IDs for all descriptors. The return from this bulk-query call
      // gives back only ID code, indicator text, and the uninformative label
      // "THREAT_DESCRIPTOR". From this we can dive in on each item, though,
      // and query for its details one ID at a time.
      IDProcessor processor = new IDDetailsProcessor(numIDsPerQuery, verbose,
        showURLs, indicatorTypeFilterer, includeIndicatorInOutput,
        dataDir, descriptorFormatter);
      Net.getDescriptorIDsByTagID(tagID, verbose, showURLs,
        taggedSince, taggedUntil, pageSize, includeIndicatorInOutput,
        processor);
    }
  }

  /**
   * Callback for TagToDetailsHandler: what we want done with every batch of
   * threat-descriptor IDs.
   */

  private static class IDDetailsProcessor implements IDProcessor {
    private final int _numIDsPerQuery;
    private final boolean _verbose;
    private final boolean _showURLs;
    private final IndicatorTypeFilterer _indicatorTypeFilterer;
    private final boolean _includeIndicatorInOutput;
    private final String _dataDir;
    private final DescriptorFormatter _descriptorFormatter;

    public IDDetailsProcessor(
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      IndicatorTypeFilterer indicatorTypeFilterer,
      boolean includeIndicatorInOutput,
      String dataDir,
      DescriptorFormatter descriptorFormatter
    ) {
      _numIDsPerQuery = numIDsPerQuery;
      _verbose = verbose;
      _showURLs = showURLs;
      _indicatorTypeFilterer = indicatorTypeFilterer;
      _includeIndicatorInOutput = includeIndicatorInOutput;
      _dataDir = dataDir;
      _descriptorFormatter = descriptorFormatter;
    }

    public void processIDs(List<String> ids) {
      outputDetails(ids, _numIDsPerQuery, _verbose, _showURLs,
        _indicatorTypeFilterer, _includeIndicatorInOutput,
        _dataDir, _descriptorFormatter);
    }
  }

  /**
   * Print details for each descriptor ID. Shared code between the
   * tag-to-details and IDs-to-details handlers.
   */
  public static void outputDetails(
    List<String> ids,
    int numIDsPerQuery,
    boolean verbose,
    boolean showURLs,
    IndicatorTypeFilterer indicatorTypeFilterer,
    boolean includeIndicatorInOutput,
    String dataDir,
    DescriptorFormatter descriptorFormatter)
  {
    List<List<String>> chunks = Utils.chunkify(ids, numIDsPerQuery);

    // Now look up details for each ID.
    for (List<String> chunk: chunks) {
      List<ThreatDescriptor> threatDescriptors = Net.getInfoForIDs(chunk, verbose, showURLs,
        includeIndicatorInOutput);
      for (ThreatDescriptor threatDescriptor : threatDescriptors) {
        if (!indicatorTypeFilterer.accept(threatDescriptor.td_indicator_type)) {
          continue;
        }

        // TODO: pull out body to method here and re-use for getIncremental

        // TODO: create-time/update-time filters go here ...

        if (dataDir == null) {
          System.out.println(descriptorFormatter.format(threatDescriptor, includeIndicatorInOutput));
        } else {
          String path = dataDir
            + File.separator
            + threatDescriptor.id
            + Utils.td_indicator_typeToFileSuffix(threatDescriptor.td_indicator_type);

          SimpleJSONWriter w = new SimpleJSONWriter();
          w.add("path", path);
          System.out.println(w.format());
          System.out.flush();

          try {
            Utils.outputIndicatorToFile(threatDescriptor, path, verbose);
          } catch (FileNotFoundException e) {
            System.err.printf("FileNotFoundException: \"%s\".\n", path);
          } catch (IOException e) {
            System.err.printf("IOException: \"%s\".\n", path);
          }
        }
      }
    }
  }

  // ----------------------------------------------------------------
  // NOTE: THIS IS KNOWN TO NOT CORRECTLY HANDLE PAGINATION.
  // PLEASE USE TAGGED_OBJECTS WITH TAGGED_SINCE.
  public static class IncrementalHandler extends CommandHandler {
    public IncrementalHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options] {tag name}\n",
        PROGNAME, _verb);
      o.printf("Options:\n");
      o.printf("--since {x}\n");
      o.printf("--indicator-type {x}\n");
      o.printf("--page-size {x}\n");
      o.printf("The \"since\" parameter is any supported by ThreatExchange,\n");
      o.printf("e.g. seconds since the epoch, or \"-1hour\", or \"-1day\", etc.\n");
      o.printf("--list   Print valid indicator-types and exit.\n");
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      IndicatorTypeFilterer indicatorTypeFilterer = IndicatorTypeFilterer.createAllFilterer();
      int pageSize = 1000;
      String since = null;
      String until = null;
      boolean includeIndicatorInOutput = true;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--list")) {
          IndicatorTypeFilterer.list(System.out);
          System.exit(0);

        } else if (option.equals("--since")) {
          if (args.length < 1) {
            usage(1);
          }
          since = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--until")) {
          if (args.length < 1) {
            usage(1);
          }
          until = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--page-size")) {
          if (args.length < 1) {
            usage(1);
          }
          pageSize = Integer.valueOf(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--indicator-type")) {
          if (args.length < 1) {
            usage(1);
          }

          indicatorTypeFilterer = IndicatorTypeFilterer.create(args[0]);
          if (indicatorTypeFilterer == null) {
            System.err.printf("%s %s: unrecognized descriptor filter \"%s\".\n",
              PROGNAME, _verb, args[0]);
            usage(1);
          }

          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--no-print-indicator")) {
          includeIndicatorInOutput = false;

        } else {
          System.err.printf("%s %s: unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }

      if (since == null) {
        System.err.printf("%s %s: --since is required.\n",
          PROGNAME, _verb);
        usage(1);
      }
      if (args.length != 1) {
        usage(1);
      }
      String tagName = args[0];

      // The 'type' field coming back from TE API requests has 'HASH_MD5' not
      // 'md5', etc.
      String uppercaseName = indicatorTypeFilterer.getUppercaseName();

      Net.getIncremental(tagName, uppercaseName, since,
        pageSize, verbose, showURLs, descriptorFormatter, includeIndicatorInOutput);
    }
  }

  // ----------------------------------------------------------------
  public static class PaginateHandler extends CommandHandler {
    public PaginateHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s {URL}\n", PROGNAME, _verb);
      o.printf("Curls the URL, JSON-dumps the return value's data blob, then curls\n");
      o.printf("the next-page URL and repeats until there are no more pages.\n");
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      if (args.length != 1) {
        usage(1);
      }
      if (args[0].equals("-h") || args[0].equals("--help")) {
        usage(0);
      }
      String startURL = args[0];
      String nextURL = startURL;

      int pageIndex = 0;
      do {
        if (showURLs) {
          System.out.println("URL:");
          System.out.println(nextURL);
        }
        try (InputStream response = new URL(nextURL).openConnection().getInputStream()) {

          JSONObject object = (JSONObject) new JSONParser().parse(new InputStreamReader(response));
          JSONArray data = (JSONArray) object.get("data");
          JSONObject paging = (JSONObject) object.get("paging");
          if (paging == null) {
            nextURL = null;
          } else {
            nextURL = (String) paging.get("next");
          }

          System.out.println(data.toString());
          pageIndex++;
        } catch (Exception e) {
          e.printStackTrace(System.err);
          System.exit(1);
        }
      } while (nextURL != null);
    }
  }

  // ----------------------------------------------------------------
  // Some code-reuse for all subcommand handlers that do POSTs.
  public static abstract class AbstractPostSubcommandHandler extends CommandHandler {

    public AbstractPostSubcommandHandler(String verb) {
      super(verb);
    }

    // Not the same for submit/update/copy.
    protected abstract void usageDescription(PrintStream o);
    protected abstract void usageDashIDashN(PrintStream o);
    protected abstract void usageAddRemoveTags(PrintStream o);
    protected abstract void usageNotCopied(PrintStream o);
    protected abstract void usageOptional(PrintStream o);

    protected void commonPosterUsage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);

      o.printf("Usage: %s %s [options]\n", PROGNAME, this._verb);

      usageDescription(o);
      usageDashIDashN(o);

      o.println("-d|--description {...}");
      o.println("-l|--share-level {...}");
      o.println("-p|--privacy-type {...}");
      o.println("-y|--severity {...}");
      o.println("");
      o.println("Optional:");
      o.println("-h|--help");
      o.println("--dry-run");
      usageOptional(o);
      o.println("-m|--privacy-members {...} If privacy-type is HAS_WHITELIST these must be");
      o.println("                       comma-delimited app IDs. If privacy-type is");
      o.println("                       HAS_PRIVACY_GROUP these must be comma-delimited");
      o.println("                       privacy-group IDs.");
      usageNotCopied(o);

      o.println("--tags {...}           Comma-delimited. Overwrites on repost.");
      usageAddRemoveTags(o);

      o.println("--related-ids-for-upload {...} Comma-delimited. IDs of descriptors (which must");
      o.println("                       already exist) to relate the new descriptor to.");
      usageNotCopied(o);
      o.println("--related-triples-json-for-upload {...} Alternate to --related-ids-for-upload.");
      o.println("                       Here you can uniquely the relate-to descriptors by their");
      o.println("                       owner ID / indicator-type / indicator-text, rather than");
      o.println("                       by their IDs. See README.md for an example.");
      usageNotCopied(o);
      o.println("");
      o.println("--reactions-to-add {...}    Example for add/remove: INGESTED,IN_REVIEW");
      o.println("--reactions-to-remove {...}");
      o.println("");
      o.println("--confidence {...}");
      o.println("-s|--status {...}");
      o.println("-r|--review-status {...}");
      o.println("--first-active {...}");
      o.println("--last-active {...}");
      o.println("--expired-on {...}");
      o.println("");
      o.println("Please see the following for allowed values in all enumerated types except reactions:");
      o.println("https://developers.facebook.com/docs/threat-exchange/reference/submitting");
      o.println("");
      o.println("Please also see:");
      o.println("https://developers.facebook.com/docs/threat-exchange/reference/editing");
      o.println("");
      o.println("Please see the following for enumerated types in reactions:");
      o.println("See also https://developers.facebook.com/docs/threat-exchange/reference/reacting");

      System.exit(exitCode);
    }

    // ----------------------------------------------------------------
    // For CLI-parsing
    //
    // Input:
    // * option such as '-d'
    // * remaining args as string-list
    // * postParams dict
    //
    // Output:
    // * boolean whether the option was recognized
    // * args may be shifted if the option was recognized and successfully handled
    //
    // Modified by reference:
    // * postParams dict modified by reference if the option was recognized and
    //   successfully handled

    protected boolean commonPosterOptionCheck(
      String option,
      ArrayList<String> args, // modified by reference, must be list not array
      DescriptorPostParameters postParams
    ) {
      boolean handled = true;

      if (option.equals("-d") || option.equals("--description")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setDescription(args.get(0));
        args.remove(0);

      } else if (option.equals("-l") || option.equals("--share-level")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setShareLevel(args.get(0));
        args.remove(0);

      } else if (option.equals("-p") || option.equals("--privacy-type")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setPrivacyType(args.get(0));
        args.remove(0);

      } else if (option.equals("-m") || option.equals("--privacy-members")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setPrivacyMembers(args.get(0));
        args.remove(0);

      } else if (option.equals("-s") || option.equals("--status")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setStatus(args.get(0));
        args.remove(0);

      } else if (option.equals("-r") || option.equals("--review-status")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setReviewStatus(args.get(0));
        args.remove(0);

      } else if (option.equals("-y") || option.equals("--severity")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setSeverity(args.get(0));
        args.remove(0);

      } else if (option.equals("-c") || option.equals("--confidence")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setConfidence(args.get(0));
        args.remove(0);

      } else if (option.equals("--related-ids-for-upload")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setRelatedIDsForUpload(args.get(0));
        args.remove(0);
      } else if (option.equals("--related-triples-for-upload-as-json")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setRelatedTriplesForUploadAsJSON(args.get(0));
        args.remove(0);

      } else if (option.equals("--reactions-to-add")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setReactionsToAdd(args.get(0));
        args.remove(0);
      } else if (option.equals("--reactions-to-remove")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setReactionsToRemove(args.get(0));
        args.remove(0);

      } else if (option.equals("--first-active")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setFirstActive(args.get(0));
        args.remove(0);
      } else if (option.equals("--last-active")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setLastActive(args.get(0));
        args.remove(0);

      } else if (option.equals("--expired-on")) {
        if (args.size() < 1) {
          usage(1);
        }
        postParams.setExpiredOn(args.get(0));
        args.remove(0);

      } else {
        handled = false;
      }

      return handled;
    }
  }

  // ----------------------------------------------------------------
  public static class SubmitHandler extends AbstractPostSubcommandHandler {
    public SubmitHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      this.commonPosterUsage(exitCode);
    }

    @Override
    protected void usageDescription(PrintStream o) {
      o.println("Uploads a threat descriptor with the specified values.");
      o.println("On repost (with same indicator text/type and app ID), updates changed fields.");
      o.println("");
    }

    @Override
    protected void usageDashIDashN(PrintStream o) {
      o.println("Required:");
      o.println("-i|--indicator {...}   The indicator text: hash/URL/etc.");
      o.println("-I                     Take indicator text from standard input, one per line.");
      o.println("Exactly one of -i or -I is required.");
      o.println("-t|--type {...}");
      o.println("");
    }

    @Override
    protected void usageAddRemoveTags(PrintStream o) {
      // Nothing extra here
    }

    @Override
    protected void usageNotCopied(PrintStream o) {
      // Nothing extra here
    }

    @Override
    protected void usageOptional(PrintStream o) {
      // Nothing extra here
    }

    @Override
    public void handle(
      String[] argsAsArray,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      boolean dryRun = false;
      boolean indicatorTextFromStdin = false;
      DescriptorPostParameters postParams = new DescriptorPostParameters();
      ArrayList<String> args = new ArrayList<String>(Arrays.asList(argsAsArray));

      while (args.size() > 0 && args.get(0).startsWith("-")) {
        String option = args.get(0);
        args.remove(0);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--dry-run")) {
          dryRun = true;

        } else if (option.equals("-I")) {
          indicatorTextFromStdin = true;
        } else if (option.equals("-i") || option.equals("--indicator")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setIndicatorText(args.get(0));
          args.remove(0);
        } else if (option.equals("-t") || option.equals("--type")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setIndicatorType(args.get(0));
          args.remove(0);

        } else if (option.equals("--tags")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setTagsToSet(args.get(0));
          args.remove(0);

        } else {
          boolean handled = this.commonPosterOptionCheck(option, args, postParams);
          if (!handled) {
            System.err.printf("%s %s: Unrecognized option \"%s\".\n",
              PROGNAME, _verb, option);
            usage(1);
          }
        }
      }
      if (args.size() > 0) {
        System.err.printf("%s %s: Extraneous argument \"%s\"\n", PROGNAME, this._verb, args.get(0));
        usage(1);
      }

      if (indicatorTextFromStdin) {
        if (postParams.getIndicatorText() != null) {
          System.err.printf("%s %s: exactly one of -I and -i must be supplied.\n",
            PROGNAME, _verb);
          System.exit(1);
        }

        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        int lno = 1;
        try {
          while ((line = reader.readLine()) != null) {
            lno++;
            // In Java, line-terminators already stripped for us
            postParams.setIndicatorText(line);
            submitSingle(postParams, verbose, showURLs, dryRun);
          }
        } catch (IOException e) {
          System.err.printf("Couldn't read line %d of standard input.\n", lno);
          System.exit(1);
        }
      } else {
        if (postParams.getIndicatorText() == null) {
          System.err.printf("%s %s: exactly one of -I and -i must be supplied.\n",
            PROGNAME, _verb);
          System.exit(1);
        }
        submitSingle(postParams, verbose, showURLs, dryRun);
      }
    }

    private void submitSingle(
      DescriptorPostParameters postParams,
      boolean verbose,
      boolean showURLs,
      boolean dryRun
    ) {
      if (postParams.getIndicatorType().equals(Constants.INDICATOR_TYPE_TMK)) {
        String filename = postParams.getIndicatorText();
        String contents = null;
        try {
          contents = Utils.readTMKHashFromFile(filename, verbose);
        } catch (FileNotFoundException e) {
          System.err.printf("%s %s: cannot find \"%s\".\n",
            PROGNAME, _verb, filename);
        } catch (IOException e) {
          System.err.printf("%s %s: cannot load \"%s\".\n",
            PROGNAME, _verb, filename);
          e.printStackTrace(System.err);
        }
        postParams.setIndicatorText(contents);
      }

      Net.PostResult postResult = Net.submitThreatDescriptor(postParams, showURLs, dryRun);
      if (!postResult.ok) {
        System.err.println(postResult.errorMessage);
        System.exit(1);
      } else {
        System.out.println(postResult.responseMessage);
      }
    }

  } // class SubmitHandler

  // ----------------------------------------------------------------
  public static class UpdateHandler extends AbstractPostSubcommandHandler {
    public UpdateHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      this.commonPosterUsage(exitCode);
    }

    @Override
    protected void usageDescription(PrintStream o) {
      o.println("Updates specified attributes on an existing threat descriptor.");
      o.println("");
    }

    @Override
    protected void usageDashIDashN(PrintStream o) {
      o.println("Required:");
      o.println("-n {...}               ID of descriptor to be edited. Must already exist.");
      o.println("-N                     Take descriptor IDs from standard input, one per line.");
      o.println("Exactly one of -n or -N is required.");
    }

    @Override
    protected void usageAddRemoveTags(PrintStream o) {
      o.println("--add-tags {...}       Comma-delimited. Adds these on repost.");
      o.println("--remove-tags {...}    Comma-delimited. Removes these on repost.");
    }

    @Override
    protected void usageNotCopied(PrintStream o) {
      // Nothing extra here
    }

    @Override
    protected void usageOptional(PrintStream o) {
      // Nothing extra here
    }

    @Override
    public void handle(
      String[] argsAsArray,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      boolean dryRun = false;
      boolean descriptorIDsFromStdin = false;
      DescriptorPostParameters  postParams = new DescriptorPostParameters();
      ArrayList<String> args = new ArrayList<String>(Arrays.asList(argsAsArray));

      while (args.size() > 0 && args.get(0).startsWith("-")) {
        String option = args.get(0);
        args.remove(0);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--dry-run")) {
          dryRun = true;

        } else if (option.equals("-N")) {
          if (args.size() < 1) {
            usage(1);
          }
          descriptorIDsFromStdin = true;
        } else if (option.equals("-n")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setDescriptorID(args.get(0));
          args.remove(0);

        } else if (option.equals("--add-tags")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setTagsToAdd(args.get(0));
          args.remove(0);

        } else if (option.equals("--remove-tags")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setTagsToRemove(args.get(0));
          args.remove(0);

        } else if (option.equals("--tags")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setTagsToSet(args.get(0));
          args.remove(0);

        } else {
          boolean handled = this.commonPosterOptionCheck(option, args, postParams);
          if (!handled) {
            System.err.printf("%s %s: Unrecognized option \"%s\".\n",
              PROGNAME, _verb, option);
            usage(1);
          }
        }
      }

      if (args.size() > 0) {
        System.err.printf("%s %s: Extraneous argument \"%s\"\n", PROGNAME, this._verb, args.get(0));
        usage(1);
      }

      if (descriptorIDsFromStdin) {
        if (postParams.getDescriptorID() != null) {
          System.err.printf("%s %s: exactly one of -N and -n must be supplied.\n",
            PROGNAME, _verb);
          System.exit(1);
        }

        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        int lno = 1;
        try {
          while ((line = reader.readLine()) != null) {
            lno++;
            // In Java, line-terminators already stripped for us
            postParams.setDescriptorID(line);
            updateSingle(postParams, verbose, showURLs, dryRun);
          }
        } catch (IOException e) {
          System.err.printf("Couldn't read line %d of standard input.\n", lno);
          System.exit(1);
        }
      } else {
        if (postParams.getDescriptorID() == null) {
          System.err.printf("%s %s: exactly one of -N and -n must be supplied.\n",
            PROGNAME, _verb);
          System.exit(1);
        }
        updateSingle(postParams, verbose, showURLs, dryRun);
      }
    }

    private void updateSingle(
      DescriptorPostParameters postParams,
      boolean verbose,
      boolean showURLs,
      boolean dryRun
    ) {
      Net.PostResult postResult = Net.updateThreatDescriptor(postParams, showURLs, dryRun);
      if (!postResult.ok) {
        System.err.println(postResult.errorMessage);
        System.exit(1);
      } else {
        System.out.println(postResult.responseMessage);
      }
    }

  } // class UpdateHandler

  // ----------------------------------------------------------------
  public static class CopyHandler extends AbstractPostSubcommandHandler {
    public CopyHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      this.commonPosterUsage(exitCode);
    }

    @Override
    protected void usageDescription(PrintStream o) {
      o.println("Copies threat descriptors to others, with optional overrides.");
      o.println("");
    }

    @Override
    protected void usageDashIDashN(PrintStream o) {
      o.println("Required:");
      o.println("-n {...}               ID of descriptor to be edited. Must already exist.");
      o.println("-N                     Take descriptor IDs from standard input, one per line.");
      o.println("Exactly one of -n or -N is required.");
    }

    @Override
    protected void usageAddRemoveTags(PrintStream o) {
      o.println("--add-tags {...}       Comma-delimited. Adds these on repost.");
      o.println("--remove-tags {...}    Comma-delimited. Removes these on repost.");
    }

    @Override
    protected void usageNotCopied(PrintStream o) {
      o.println("                       Must be explicitly specified for copy; not available from the source descriptor.");
    }

    @Override
    protected void usageOptional(PrintStream o) {
      o.println("-i|--indicator {...}   Indicator value to overwrite for copy.");
    }

    @Override
    public void handle(
      String[] argsAsArray,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      DescriptorFormatter descriptorFormatter
    ) {
      boolean dryRun = false;
      boolean descriptorIDsFromStdin = false;
      DescriptorPostParameters  postParams = new DescriptorPostParameters();
      ArrayList<String> args = new ArrayList<String>(Arrays.asList(argsAsArray));

      while (args.size() > 0 && args.get(0).startsWith("-")) {
        String option = args.get(0);
        args.remove(0);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--dry-run")) {
          dryRun = true;

        } else if (option.equals("-N")) {
          descriptorIDsFromStdin = true;
        } else if (option.equals("-n")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setDescriptorID(args.get(0));
          args.remove(0);

        } else if (option.equals("-i") || option.equals("--indicator")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setIndicatorText(args.get(0));
          args.remove(0);
        } else if (option.equals("-t") || option.equals("--type")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setIndicatorType(args.get(0));
          args.remove(0);

        } else if (option.equals("--tags")) {
          if (args.size() < 1) {
            usage(1);
          }
          postParams.setTagsToSet(args.get(0));
          args.remove(0);

        } else {
          boolean handled = this.commonPosterOptionCheck(option, args, postParams);
          if (!handled) {
            System.err.printf("%s %s: Unrecognized option \"%s\".\n",
              PROGNAME, _verb, option);
            usage(1);
          }
        }
      }

      if (args.size() > 0) {
        System.err.printf("%s %s: Extraneous argument \"%s\"\n", PROGNAME, this._verb, args.get(0));
        usage(1);
      }

      if (descriptorIDsFromStdin) {
        if (postParams.getDescriptorID() != null) {
          System.err.printf("%s %s: exactly one of -N and -n must be supplied.\n",
            PROGNAME, _verb);
          System.exit(1);
        }

        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        int lno = 1;
        try {
          while ((line = reader.readLine()) != null) {
            lno++;
            // In Java, line-terminators already stripped for us
            postParams.setDescriptorID(line);
            copySingle(postParams, verbose, showURLs, dryRun);
          }
        } catch (IOException e) {
          System.err.printf("Couldn't read line %d of standard input.\n", lno);
          System.exit(1);
        }
      } else {
        if (postParams.getDescriptorID() == null) {
          System.err.printf("%s %s: exactly one of -N and -n must be supplied.\n",
            PROGNAME, _verb);
          System.exit(1);
        }
        copySingle(postParams, verbose, showURLs, dryRun);
      }
    }

    private void copySingle(
      DescriptorPostParameters postParams,
      boolean verbose,
      boolean showURLs,
      boolean dryRun
    ) {
      Net.PostResult postResult = Net.copyThreatDescriptor(postParams, verbose, showURLs, dryRun);
      if (!postResult.ok) {
        System.err.println(postResult.errorMessage);
        System.exit(1);
      } else {
        System.out.println(postResult.responseMessage);
      }
    }

  } // class CopyHandler

}

