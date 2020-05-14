// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

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
      IndicatorTypeFilterer indicatorTypeFilterer = new AllIndicatorTypeFilterer();

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
      o.printf("--indicator-type {x}\n");
      o.printf("--no-print-indicator -- Don't print the indicator to the terminal\n");
      o.printf("The \"tagged-since\" or \"tagged-until\" parameter is any supported by ThreatExchange,\n");
      o.printf("e.g. seconds since the epoch, or \"-1hour\", or \"-1day\", etc.\n");
      o.printf("Descriptor types:\n");
      IndicatorTypeFiltererFactory.list(o);
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
      IndicatorTypeFilterer indicatorTypeFilterer = new AllIndicatorTypeFilterer();
      int pageSize = 1000;
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

        } else if (option.equals("--indicator-type")) {
          if (args.length < 1) {
            usage(1);
          }

          indicatorTypeFilterer = IndicatorTypeFiltererFactory.create(args[0]);
          if (indicatorTypeFilterer == null) {
            System.err.printf("%s %s: unrecognized descriptor filter \"%s\".\n",
              PROGNAME, _verb, args[1]);
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
        indicatorTypeFilterer, taggedSince, taggedUntil, pageSize, includeIndicatorInOutput,
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

      outputDetails(ids, numIDsPerQuery, verbose, showURLs, includeIndicatorInOutput,
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
      o.printf("Indicator types:\n");
      IndicatorTypeFiltererFactory.list(o);
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
      IndicatorTypeFilterer indicatorTypeFilterer = new AllIndicatorTypeFilterer();
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

          indicatorTypeFilterer = IndicatorTypeFiltererFactory.create(args[0]);
          if (indicatorTypeFilterer == null) {
            System.err.printf("%s %s: unrecognized descriptor filter \"%s\".\n",
              PROGNAME, _verb, args[1]);
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
        showURLs, includeIndicatorInOutput, dataDir, descriptorFormatter);
      Net.getDescriptorIDsByTagID(tagID, verbose, showURLs,
        indicatorTypeFilterer, taggedSince, taggedUntil, pageSize, includeIndicatorInOutput,
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
    private final boolean _includeIndicatorInOutput;
    private final String _dataDir;
    private final DescriptorFormatter _descriptorFormatter;

    public IDDetailsProcessor(
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      boolean includeIndicatorInOutput,
      String dataDir,
      DescriptorFormatter descriptorFormatter
    ) {
      _numIDsPerQuery = numIDsPerQuery;
      _verbose = verbose;
      _showURLs = showURLs;
      _includeIndicatorInOutput = includeIndicatorInOutput;
      _dataDir = dataDir;
      _descriptorFormatter = descriptorFormatter;
    }

    public void processIDs(List<String> ids) {
      outputDetails(ids, _numIDsPerQuery, _verbose, _showURLs, _includeIndicatorInOutput,
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
      o.printf("Indicator types:\n");
      IndicatorTypeFiltererFactory.list(o);
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
      IndicatorTypeFilterer indicatorTypeFilterer = new AllIndicatorTypeFilterer();
      int pageSize = 1000;
      String since = null;
      String until = null;
      boolean includeIndicatorInOutput = true;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

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

          indicatorTypeFilterer = IndicatorTypeFiltererFactory.create(args[0]);
          if (indicatorTypeFilterer == null) {
            System.err.printf("%s %s: unrecognized descriptor filter \"%s\".\n",
              PROGNAME, _verb, args[1]);
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

      String td_indicator_typeForTE = indicatorTypeFilterer.getTEName();

      Net.getIncremental(tagName, td_indicator_typeForTE, since,
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
  // NOTE: SubmitHandler and UpdateHandler have a lot of the same code but also
  // several differences. I found it simpler (albeit more verbose) to duplicate
  // rather than do an abstract-and-override refactor.

  public static class SubmitHandler extends CommandHandler {
    public SubmitHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options]\n", PROGNAME, _verb);
      o.printf("Uploads a threat descriptor with the specified values.\n");
      o.printf("On repost (with same indicator text/type and app ID), updates changed fields.\n");
      o.printf("\n");
      o.printf("Required:\n");
      o.printf("-i|--indicator {...}   If indicator type is HASH_TMK this must be the\n");
      o.printf("                       path to a .tmk file, else the indicator text.\n");
      o.printf("-I                     Take indicator text from standard input, one per line.\n");
      o.printf("Exactly one of -i or -I is required.\n");
      o.printf("-t|--type {...}\n");
      o.printf("-d|--description {...}\n");
      o.printf("-l|--share-level {...}\n");
      o.printf("-p|--privacy-type {...}\n");
      o.printf("-y|--severity {...}\n");
      o.printf("\n");
      o.printf("Optional:\n");
      o.printf("-h|--help\n");
      o.printf("--dry-run\n");
      o.printf("-m|--privacy-members {...} If privacy-type is HAS_WHITELIST these must be\n");
      o.printf("                       comma-delimited app IDs. If privacy-type is\n");
      o.printf("                       HAS_PRIVACY_GROUP these must be comma-delimited\n");
      o.printf("                       privacy-group IDs.\n");
      o.printf("--tags {...}           Comma-delimited. Overwrites on repost.\n");
      o.printf("--related-ids-for-upload {...} Comma-delimited. IDs of descriptors (which must\n");
      o.printf("                       already exist) to relate the new descriptor to.\n");
      o.printf("--related-triples-json-for-upload {...} Alternate to --related-ids-for-upload.\n");
      o.printf("                       Here you can uniquely the relate-to descriptors by their\n");
      o.printf("                       owner ID / indicator-type / indicator-text, rather than\n");
      o.printf("                       by their IDs. See README.md for an example.\n");
      o.printf("-c|--confidence {...}\n");
      o.printf("-s|--status {...}\n");
      o.printf("-r|--review-status {...}\n");
      o.printf("--first-active {...}\n");
      o.printf("--last-active {...}\n");
      o.printf("--expired-on {...}\n");
      o.printf("\n");
      o.printf("Please see the following for allowed values in all enumerated types:\n");
      o.printf("https://developers.facebook.com/docs/threat-exchange/reference/submitting\n");
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
      boolean dryRun = false;
      boolean indicatorTextFromStdin = false;
      DescriptorPostParameters  params = new DescriptorPostParameters();

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--dry-run")) {
          dryRun = true;

        } else if (option.equals("-I")) {
          if (args.length < 1) {
            usage(1);
          }
          indicatorTextFromStdin = true;
        } else if (option.equals("-i") || option.equals("--indicator")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setIndicatorText(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-t") || option.equals("--type")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setIndicatorType(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-d") || option.equals("--description")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setDescription(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-l") || option.equals("--share-level")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setShareLevel(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-p") || option.equals("--privacy-type")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setPrivacyType(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-m") || option.equals("--privacy-members")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setPrivacyMembers(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("-s") || option.equals("--status")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setStatus(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-r") || option.equals("--review-status")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setReviewStatus(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-y") || option.equals("--severity")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setSeverity(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--related-ids-for-upload")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setRelatedIDsForUpload(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("--related-triples-for-upload-as-json")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setRelatedTriplesForUploadAsJSON(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--tags")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setTagsToSet(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("-c") || option.equals("--confidence")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setConfidence(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--first-active")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setFirstActive(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("--last-active")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setLastActive(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("--expired-on")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setExpiredOn(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else {
          System.err.printf("%s %s: Unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }
      if (args.length > 0) {
        System.err.printf("Extraneous argument \"%s\"\n", args[0]);
        usage(1);
      }

      if (indicatorTextFromStdin) {
        if (params.getIndicatorText() != null) {
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
            params.setIndicatorText(line);
            submitSingle(params, verbose, showURLs, dryRun);
          }
        } catch (IOException e) {
          System.err.printf("Couldn't read line %d of standard input.\n", lno);
          System.exit(1);
        }
      } else {
        if (params.getIndicatorText() == null) {
          System.err.printf("%s %s: exactly one of -I and -i must be supplied.\n",
            PROGNAME, _verb);
          System.exit(1);
        }
        submitSingle(params, verbose, showURLs, dryRun);
      }
    }

    private void submitSingle(
      DescriptorPostParameters params,
      boolean verbose,
      boolean showURLs,
      boolean dryRun
    ) {
      if (params.getIndicatorType().equals(Constants.INDICATOR_TYPE_TMK)) {
        String filename = params.getIndicatorText();
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
        params.setIndicatorText(contents);
      }

      boolean ok = Net.submitThreatDescriptor(params, showURLs, dryRun);
      if (!ok) {
        // Error message already printed out
        System.exit(1);
      }
    }

  } // class SubmitHandler

  // ----------------------------------------------------------------
  // NOTE: SubmitHandler and UpdateHandler have a lot of the same code but also
  // several differences. I found it simpler (albeit more verbose) to duplicate
  // rather than do an abstract-and-override refactor.

  public static class UpdateHandler extends CommandHandler {
    public UpdateHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options]\n", PROGNAME, _verb);
      o.printf("Updates specified attributes on an existing threat descriptor.\n");
      o.printf("\n");
      o.printf("Required:\n");
      o.printf("-i {...}               ID of descriptor to be edited. Must already exist.\n");
      o.printf("-I                     Take descriptor IDs from standard input, one per line.\n");
      o.printf("Exactly one of -i or -I is required.\n");
      o.printf("-d|--description {...}\n");
      o.printf("-l|--share-level {...}\n");
      o.printf("-p|--privacy-type {...}\n");
      o.printf("-y|--severity {...}\n");
      o.printf("\n");
      o.printf("Optional:\n");
      o.printf("-h|--help\n");
      o.printf("--dry-run\n");
      o.printf("-m|--privacy-members {...} If privacy-type is HAS_WHITELIST these must be\n");
      o.printf("                       comma-delimited app IDs. If privacy-type is\n");
      o.printf("                       HAS_PRIVACY_GROUP these must be comma-delimited\n");
      o.printf("                       privacy-group IDs.\n");
      o.printf("--tags {...}           Comma-delimited. Overwrites on repost.\n");
      o.printf("--add-tags {...}       Comma-delimited. Adds these on repost.\n");
      o.printf("--remove-tags {...}    Comma-delimited. Removes these on repost.\n");
      o.printf("--related-ids-for-upload {...} Comma-delimited. IDs of descriptors (which must\n");
      o.printf("                       already exist) to relate the new descriptor to.\n");
      o.printf("--related-triples-json-for-upload {...} Alternate to --related-ids-for-upload.\n");
      o.printf("                       Here you can uniquely the relate-to descriptors by their\n");
      o.printf("                       owner ID / indicator-type / indicator-text, rather than\n");
      o.printf("                       by their IDs. See README.md for an example.\n");
      o.printf("-c|--confidence {...}\n");
      o.printf("-s|--status {...}\n");
      o.printf("-r|--review-status {...}\n");
      o.printf("--first-active {...}\n");
      o.printf("--last-active {...}\n");
      o.printf("--expired-on {...}\n");
      o.printf("\n");
      o.printf("Please see the following for allowed values in all enumerated types:\n");
      o.printf("https://developers.facebook.com/docs/threat-exchange/reference/editing\n");
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
      boolean dryRun = false;
      boolean descriptorIDsFromStdin = false;
      DescriptorPostParameters  params = new DescriptorPostParameters();

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--dry-run")) {
          dryRun = true;

        } else if (option.equals("-I")) {
          if (args.length < 1) {
            usage(1);
          }
          descriptorIDsFromStdin = true;
        } else if (option.equals("-i")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setDescriptorID(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-d") || option.equals("--description")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setDescription(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-l") || option.equals("--share-level")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setShareLevel(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-p") || option.equals("--privacy-type")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setPrivacyType(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-m") || option.equals("--privacy-members")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setPrivacyMembers(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("-s") || option.equals("--status")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setStatus(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-r") || option.equals("--review-status")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setReviewStatus(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("-y") || option.equals("--severity")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setSeverity(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--related-ids-for-upload")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setRelatedIDsForUpload(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("--related-triples-for-upload-as-json")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setRelatedTriplesForUploadAsJSON(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--tags")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setTagsToSet(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("--add-tags")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setTagsToAdd(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("--remove-tags")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setTagsToRemove(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("-c") || option.equals("--confidence")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setConfidence(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--first-active")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setFirstActive(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("--last-active")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setLastActive(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);
        } else if (option.equals("--expired-on")) {
          if (args.length < 1) {
            usage(1);
          }
          params.setExpiredOn(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else {
          System.err.printf("%s %s: Unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }
      if (args.length > 0) {
        System.err.printf("Extraneous argument \"%s\"\n", args[0]);
        usage(1);
      }

      if (descriptorIDsFromStdin) {
        if (params.getDescriptorID() != null) {
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
            params.setDescriptorID(line);
            updateSingle(params, verbose, showURLs, dryRun);
          }
        } catch (IOException e) {
          System.err.printf("Couldn't read line %d of standard input.\n", lno);
          System.exit(1);
        }
      } else {
        if (params.getDescriptorID() == null) {
          System.err.printf("%s %s: exactly one of -I and -i must be supplied.\n",
            PROGNAME, _verb);
          System.exit(1);
        }
        updateSingle(params, verbose, showURLs, dryRun);
      }
    }

    private void updateSingle(
      DescriptorPostParameters params,
      boolean verbose,
      boolean showURLs,
      boolean dryRun
    ) {
      boolean ok = Net.updateThreatDescriptor(params, showURLs, dryRun);
      if (!ok) {
        // Error message already printed out
        System.exit(1);
      }
    }

  } // class UpdateHandler

}
